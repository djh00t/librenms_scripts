#!/usr/bin/python3
"""
This script adds `state` lookup data to librenms mysql database locations table using lat
and lon values provided by device SNMP location string.

Installation:
- This script requires the following packages to be installed: geopandas, shapely, sqlalchemy, dotenv, pymysql, requests, subprocess.
- The script also requires a .env file with the following variables: DB_NAME, DB_SERVER, DB_TABLE, DB_USER, DB_PASS.

Configuration:
- The script downloads a shapefile from the Australian Bureau of Statistics website to the 'geo_data' directory.
- The script reads location data from the specified database table and updates the table with the state information.

Usage:
- Run the script using the command 'python location_lookup.py'.
- Use the '-d' or '--debug' flag to enable debugging.
"""
from dotenv import load_dotenv
from shapely.geometry import Point
from sqlalchemy import create_engine
from subprocess import call, check_output
import argparse
import geopandas as gpd
import os
import pandas as pd
import pymysql
import requests
import subprocess
import sys
import zipfile

# Create a parser
parser = argparse.ArgumentParser(description="Location lookup script")

# Add --debug argument
parser.add_argument('-d', '--debug', action='store_true', help="Enable debugging")

# Parse arguments
args = parser.parse_args()

# Use args.debug to control debugging
if args.debug:
    print("Debugging is enabled")
else:
    print("Debugging is not enabled")

# Load environment variables
load_dotenv()

# Database credentials and details from .env file
DB_NAME = os.getenv('DB_NAME')
DB_SERVER = os.getenv('DB_SERVER')
DB_TABLE = os.getenv('DB_TABLE')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

if args.debug:
    # Print the database credentials and details
    print(f'Database name: {DB_NAME}')
    print(f'Database server: {DB_SERVER}')
    print(f'Database table: {DB_TABLE}')

# Define the geo_data directory
geo_data_dir = 'geo_data'

# Ensure the geo_data directory exists
if not os.path.exists(geo_data_dir):
    os.makedirs(geo_data_dir)

# Function to download and extract the shapefile
def setup_geodata():
    # If debug is enabled, print a message
    if args.debug:
        print("Setting up geodata")

    # Define the shapefile path
    shapefile_zip_url = 'https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/STE_2021_AUST_SHP_GDA2020.zip'
    zip_file_path = os.path.join(geo_data_dir, 'STE_2021_AUST_SHP_GDA2020.zip')

    # Download and unzip the shapefile if it's not already present
    if not os.listdir(geo_data_dir):
        if args.debug:
            print("Downloading shapefile...")
    response = requests.get(shapefile_zip_url, stream=True)
    with open(zip_file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=128):
            file.write(chunk)
    if args.debug:
        print("Shapefile downloaded. Extracting...")
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(geo_data_dir)
    if args.debug:
        print("Shapefile extracted. Removing zip file...")
    os.remove(zip_file_path)
    if args.debug:
        print("Zip file removed.")

# Run geodata setup if needed
if not os.path.exists('geo_data') or not os.listdir('geo_data'):
    setup_geodata()

# Iterate through requirements.txt, checking if each is installed. If a package
# is not installed, install it.
if args.debug:
    print("Checking if required packages are installed...")
with open('requirements.txt') as file:
    for line in file:
        package = line.strip()
        if args.debug:
            print(f"Checking if {package} is installed...")
        try:
            __import__(package)
        except ImportError:
            if args.debug:
                print(f"{package} is not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            if args.debug:
                print(f"{package} installed.")

# Database connection string
db_connection_str = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_SERVER}/{DB_NAME}'

# Create database engine
engine = create_engine(db_connection_str)

# State abbreviation mappings
state_mappings = {
    'New South Wales': 'NSW',
    'Queensland': 'QLD',
    'Victoria': 'VIC',
    'South Australia': 'SA',
    'Australian Capital Territory': 'ACT',
    'Northern Territory': 'NT',
    'Tasmania': 'TAS',
    'Western Australia': 'WA'
}

# Function to determine the state based on the latitude and longitude
def determine_state(lat, lng, gdf):
    # Check if latitude and longitude are valid
    if lat is None or lng is None or not (isinstance(lat, (int, float)) and isinstance(lng, (int, float))):
        if args.debug:
            print(f"Invalid lat/lng values: {lat}, {lng}")
        return 'Invalid Location'
    
    point = Point(lng, lat)

    for _, row in gdf.iterrows():
        # Check if the geometry is valid
        if row['geometry'] is None or row['geometry'].is_empty:
            continue
        
        # Check if the point is within the geometry
        if point.within(row['geometry']):
            full_state_name = row['STE_NAME21']
            if args.debug:
                print(f"Point {point} is within {row['STE_NAME21']} ({state_mappings.get(full_state_name, 'Not Found')})")
            # Map the full state name to its abbreviation
            return state_mappings.get(full_state_name, 'Not Found')
    if args.debug:
        print(f"Point {point} not found within any state")
    return 'Not Found'

# Path to the shapefile (assumed to be in the same directory as the script)
shapefile_path = './geo_data/STE_2021_AUST_GDA2020.shp'

# Load the shapefile into a GeoDataFrame
if args.debug:
    print("Loading shapefile into GeoDataFrame...")
gdf_states = gpd.read_file(shapefile_path)

# Read locations data from the database
sql = f'SELECT id, lat, lng FROM {DB_TABLE}'
if args.debug:
    print("Reading locations data from the database...")
df_locations = pd.read_sql(sql, engine)

# Determine the state for each location
if args.debug:
    print("Determining the state for each location...")
df_locations['state'] = df_locations.apply(
    lambda row: determine_state(row['lat'], row['lng'], gdf_states), axis=1
)

# Update the database with the state information
with engine.connect() as conn:
    if args.debug:
        print("Updating the database with the state information...")
    for index, row in df_locations.iterrows():
        # Ensure that values are valid varchar(3) values if they are not, skip
        # the row and log the error
        if row['state'] is None or not isinstance(row['state'], str) or len(row['state']) > 3:
            if args.debug:
                print(f"Invalid state value: {row['state']}")
            continue
        # Generate the SQL update statement
        update_sql = f'''
            UPDATE {DB_TABLE}
            SET state = %s
            WHERE id = %s
        '''
        conn.execute(update_sql, (row['state'], row['id']))
