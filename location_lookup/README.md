# Location State Lookup Script

This Python script is designed to enhance the locations table in a LibreNMS
MySQL database by adding Australian State information derived from device SNMP
location strings. It utilizes latitude and longitude values to determine and
update the state for each location.

## Features

- **Geographical Data Integration**: Uses shapefiles from the Australian Bureau of Statistics to map latitude and longitude to Australian states.
- **Database Interaction**: Reads and updates a specified database table with state information.
- **Automated Dependency Management**: Checks for required packages and installs them if missing.
- **Debugging Support**: Includes an optional debug mode for detailed operational logging.

## Installation

This script requires Python 3 and the following packages: `geopandas`, `shapely`, `sqlalchemy`, `dotenv`, `pymysql`, `requests`, and `subprocess`. You can install these packages using pip:

```bash
pip install geopandas shapely sqlalchemy python-dotenv pymysql requests subprocess
```

Additionally, ensure you have a `.env` file in your script directory with the following environment variables:

- `DB_NAME`: Name of your database.
- `DB_SERVER`: Database server address.
- `DB_TABLE`: Database table to be updated.
- `DB_USER`: Database user.
- `DB_PASS`: Database password.

## Configuration

1. **Shapefile Download**: The script automatically downloads the required shapefile from the Australian Bureau of Statistics website into the 'geo_data' directory.
2. **Database Connection**: Modify the `.env` file to configure the database connection details.

## Usage

To run the script, use the following command:

```bash
python location_lookup.py
```

For debugging output, add the `-d` or `--debug` flag:

```bash
python location_lookup.py --debug
```

## Operational Flow

1. **Setup Geodata**: Downloads and extracts the shapefile required for mapping coordinates to states.
2. **Dependency Check**: Ensures all required Python packages are installed.
3. **Database Interaction**:
    - Connects to the specified database.
    - Reads location data (latitude and longitude).
    - Determines the corresponding state for each location.
    - Updates the database with the state information.

## Important Notes

- Ensure you have the required permissions to access and modify the database.
- This script is specifically tailored for Australian geographic data and may need modifications for use in other regions.

## License

This script is open-source and can be used and modified as per your requirements.
