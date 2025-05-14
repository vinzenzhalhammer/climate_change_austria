import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

def main():

    # --- Configuration ---
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365*250)
    station_id = "55"  # Wien Hohe Warte
    resource_id = "klima-v2-1y"#"klima-v2-1d"
    parameters = ['TLMAX', 'TLMIN', 'TL_MITTEL']

    # --- API Call ---
    url = f"https://dataset.api.hub.geosphere.at/v1/station/historical/{resource_id}"
    params = {
        "parameters": ','.join(parameters),
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "station_ids": station_id,
    }

    response = requests.get(url, params=params)
    data = response.json()

    # --- Parse Station & Coordinates ---
    feature = data['features'][0]
    lat, lon = feature['geometry']['coordinates']
    station_id = feature['properties']['station']
    timestamps = pd.to_datetime(data['timestamps'])

    # --- Extract Parameter Data Dynamically ---
    param_data = feature['properties']['parameters']
    df = pd.DataFrame({'date': timestamps})

    for code, value in param_data.items():
        df[code.lower()] = value['data']

    # --- Add Metadata ---
    df['station_id'] = station_id
    df['latitude'] = lat
    df['longitude'] = lon

    df.dropna(subset="tl_mittel", inplace=True)

    Optional: Rearrange columns
    cols = ['date', 'station_id', 'latitude', 'longitude'] + [col for col in df.columns if col not in ['date', 'station_id', 'latitude', 'longitude']]
    df = df[cols]

    print(df.head())

    import duckdb

    # # Connect to DuckDB (creates file if it doesn't exist)
    con = duckdb.connect("app/data.duckdb")

    con.execute("""
        CREATE TABLE IF NOT EXISTS climate_data (
            date DATE,
            tlmax DOUBLE,
            tlmin DOUBLE,
            tl_mittel DOUBLE,
            station_id VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE
        )
    """)

    # con.execute("INSERT INTO climate_data SELECT * FROM df")
    print(con.execute("SHOW TABLES").fetchall())
    df = con.execute("SELECT * FROM climate_data WHERE station_id = '6306'").fetchdf()
    print(df.head())

if __name__ == "__main__":
    main()
