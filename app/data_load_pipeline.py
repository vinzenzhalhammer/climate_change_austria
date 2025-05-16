import requests
import duckdb
import pandas as pd
from duckdb import DuckDBPyConnection
from datetime import datetime, timedelta
import argparse
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%m-%d-%Y %H:%M:%S',
    level=logging.INFO
)

def connect_to_db(path: str = "data.duckdb") -> DuckDBPyConnection:
    con = duckdb.connect(path)
    logging.info(f"Connected to database {path}")
    return con

def create_stations_table(con: DuckDBPyConnection):
    con.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            state VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            altitude DOUBLE,
            valid_from DATE,
            valid_to DATE
        )
    """)

def create_measurement_table(con: DuckDBPyConnection):
    con.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            date DATE,
            tlmax DOUBLE,
            tlmin DOUBLE,
            tl_mittel DOUBLE,
            id INTEGER,
        )
    """)

def fetch_station_data(resource_id: str = "klima-v2-1y") -> pd.DataFrame:
    url = f"https://dataset.api.hub.geosphere.at/v1/station/historical/{resource_id}/metadata"
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    df = pd.DataFrame(data["stations"])

    df['valid_from'] = pd.to_datetime(df['valid_from'])
    df['valid_to'] = pd.to_datetime(df['valid_to'])
    df["id"] = df["id"].astype(int)

    df = df[(df['valid_from'].dt.year < 1950) & (df['valid_to'].dt.year > 2040)]
    df = df[["id", "name", "state", "lat", "lon", "altitude", "valid_from", "valid_to"]]

    df = df.rename(columns={"lat": "latitude", "lon": "longitude"})

    logging.info("Stations data fetched succesfully")

    return df

def fetch_measurement_data(parameter: dict, resource_id: str = "klima-v2-1y") -> pd.DataFrame:

    url = f"https://dataset.api.hub.geosphere.at/v1/station/historical/{resource_id}"

    response = requests.get(url, params=parameter)
    response.raise_for_status()
    data = response.json()

    # --- Parse Station & Coordinates ---
    feature = data['features'][0]
    station_id = feature['properties']['station']
    timestamps = pd.to_datetime(data['timestamps'])

    # --- Extract Parameter Data Dynamically ---
    param_data = feature['properties']['parameters']
    df = pd.DataFrame({'date': timestamps})

    for code, value in param_data.items():
        df[code.lower()] = value['data']

    # --- Add Metadata ---
    df['id'] = int(station_id)

    df.dropna(subset="tl_mittel", inplace=True)

    logging.info(f"Measurements data for station id {station_id} fetched succesfully")

    return df

def insert_stations(con: DuckDBPyConnection, df: pd.DataFrame):
    con.register("df", df)
    con.execute("""
        INSERT INTO stations (id, name, state, latitude, longitude, altitude, valid_from, valid_to)
        SELECT * FROM df
    """)
    logging.info("Stations data inserted to database")

def insert_measurement(con: DuckDBPyConnection, df: pd.DataFrame):
    con.register("df", df)
    con.execute("""
        INSERT INTO measurements (date, tlmax, tlmin, tl_mittel, id)
        SELECT * FROM df
    """)
    logging.info("Measurements data inserted to database")

def create_station_yearly_summary(con: DuckDBPyConnection):
    con.execute("""
        CREATE OR REPLACE TABLE station_yearly_stats AS
        SELECT
            id,
            EXTRACT(year FROM date) AS year,
            AVG(tl_mittel) AS tl_mittel,
            ROUND(AVG(AVG(tl_mittel)) OVER (
                PARTITION BY id ORDER BY EXTRACT(year FROM date)
                ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
            ), 2) AS rolling_avg_temp_10y
        FROM measurements
        GROUP BY id, year
        ORDER BY id, year;
    """)
    logging.info("Created table station_yearly_stats with rolling station temp averages")

def create_station_historic_temps(con: DuckDBPyConnection):
    con.execute("""
        CREATE OR REPLACE TABLE station_summary AS
        SELECT
            id,
            ROUND(AVG(CASE WHEN date < DATE '1970-01-01' AND DATE > '1950-01-01' THEN tl_mittel END), 2) AS pre1970_temp,
            ROUND(AVG(CASE WHEN date >= DATE '2000-01-01' THEN tl_mittel END), 2) AS post2000_temp,
            ROUND(post2000_temp - pre1970_temp, 2) AS delta_temp
        FROM measurements
        GROUP BY id
        ORDER BY id;
    """)
    logging.info("Created table station_summary with historic period temp averages")

def create_view_for_frontend(con: DuckDBPyConnection):
    con.execute("""
        CREATE OR REPLACE VIEW station_frontend_data AS
        SELECT
            s.id AS id,
            s.name,
            s.latitude,
            s.longitude,
            ss.pre1970_temp,
            ss.post2000_temp,
            ss.delta_temp,
            sys.year,
            sys.tl_mittel,
            sys.rolling_avg_temp_10y
        FROM stations s
        JOIN station_summary ss ON s.id = ss.id
        JOIN station_yearly_stats sys ON s.id = sys.id;
    """)
    logging.info("Created view station_frontend_data with all the data needed for the frontend")

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Force refetching data from API")
    args = parser.parse_args()

    con = connect_to_db()
    create_stations_table(con)
    create_measurement_table(con)

    # --- Configuration ---
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365*250)
    resource_id = "klima-v2-1y"  #"klima-v2-1d"
    parameters = ['TLMAX', 'TLMIN', 'TL_MITTEL']

    if args.refresh or con.execute("SELECT COUNT(*) FROM stations").fetchone()[0] == 0:
        df_stations = fetch_station_data(resource_id)
        insert_stations(con, df_stations)
    else:
        logging.info("Stations already in database. Skipping fetch.")

    station_list = con.execute("SELECT id FROM stations").fetch_df()["id"].tolist()
    existing_ids = con.execute("SELECT DISTINCT id FROM measurements").fetch_df()["id"].tolist()

    for station_id in station_list:
        if args.refresh or station_id in existing_ids:
            logging.info(f"Measurements for station {station_id} already exist. Skipping.")
            continue

        # Fetch and insert if missing
        params = {
            "parameters": ','.join(parameters),
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "station_ids": station_id,
        }
        try:
            df_measurement = fetch_measurement_data(params, resource_id)
            insert_measurement(con, df_measurement)
        except Exception as e:
            logging.error(f"Failed for station {station_id}: {e}")

    create_station_yearly_summary(con)
    create_station_historic_temps(con)
    create_view_for_frontend(con)


if __name__ == "__main__":
    main()