import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

def main():

    # # --- Configuration ---
    # end_date = datetime.now().date()
    # start_date = end_date - timedelta(days=365*250)
    # station_id = "55"  # Wien Hohe Warte
    # resource_id = "klima-v2-1y"#"klima-v2-1d"
    # parameters = ['TLMAX', 'TLMIN', 'TL_MITTEL']

    # # --- API Call ---
    # url = f"https://dataset.api.hub.geosphere.at/v1/station/historical/{resource_id}"
    # params = {
    #     "parameters": ','.join(parameters),
    #     "start": start_date.isoformat(),
    #     "end": end_date.isoformat(),
    #     "station_ids": station_id,
    # }

    # response = requests.get(url, params=params)
    # data = response.json()

    # # --- Parse Station & Coordinates ---
    # feature = data['features'][0]
    # lat, lon = feature['geometry']['coordinates']
    # station_id = feature['properties']['station']
    # timestamps = pd.to_datetime(data['timestamps'])

    # # --- Extract Parameter Data Dynamically ---
    # param_data = feature['properties']['parameters']
    # df = pd.DataFrame({'date': timestamps})

    # for code, value in param_data.items():
    #     df[code.lower()] = value['data']

    # # --- Add Metadata ---
    # df['station_id'] = station_id
    # df['latitude'] = lat
    # df['longitude'] = lon

    # df.dropna(subset="tl_mittel", inplace=True)

    # Optional: Rearrange columns
    #cols = ['date', 'station_id', 'latitude', 'longitude'] + [col for col in df.columns if col not in ['date', 'station_id', 'latitude', 'longitude']]
    #df = df[cols]

    # print(df.head())

    import duckdb

    # # Connect to DuckDB (creates file if it doesn't exist)
    con = duckdb.connect("app/data.duckdb")

    # con.execute("""
    #     CREATE TABLE IF NOT EXISTS climate_data (
    #         date DATE,
    #         tlmax DOUBLE,
    #         tlmin DOUBLE,
    #         tl_mittel DOUBLE,
    #         station_id VARCHAR,
    #         latitude DOUBLE,
    #         longitude DOUBLE
    #     )
    # """)

    # con.execute("INSERT INTO climate_data SELECT * FROM df")
    print(con.execute("SHOW TABLES").fetchall())
    df = con.execute("SELECT * FROM climate_data WHERE station_id = '6306'").fetchdf()
    print(df.head())

    # # Rename columns to more readable names (optional)
    # df_plot = df.rename(columns={
    #     'tlmin': 'Min Temp (°C)',
    #     'tlmax': 'Max Temp (°C)',
    #     'tl_mittel': 'Avg Temp (°C)'
    # })

    # df_plot['Avg Temp MA (10y)'] = df_plot['Avg Temp (°C)'].rolling(window=10).mean()

    # # Create figure
    # fig = go.Figure()

    # # # Add scatter points for daily values
    # # fig.add_trace(go.Scatter(
    # #     x=df_plot['date'], y=df_plot['Min Temp (°C)'],
    # #     mode='markers',
    # #     name='Min Temp (°C)',
    # #     marker=dict(size=4)
    # # ))

    # # fig.add_trace(go.Scatter(
    # #     x=df_plot['date'], y=df_plot['Max Temp (°C)'],
    # #     mode='markers',
    # #     name='Max Temp (°C)',
    # #     marker=dict(size=4)
    # # ))

    # fig.add_trace(go.Scatter(
    #     x=df_plot['date'], y=df_plot['Avg Temp (°C)'],
    #     mode='markers',
    #     name='Avg Temp (°C)',
    #     marker=dict(size=4)
    # ))

    # # Add line for moving average
    # fig.add_trace(go.Scatter(
    #     x=df_plot['date'], y=df_plot['Avg Temp MA (10y)'],
    #     mode='lines',
    #     name='Avg Temp MA (10y)',
    #     line=dict(color='black', width=2)
    # ))

    # # Customize layout
    # fig.update_layout(
    #     title='Daily Temperatures and Moving Average',
    #     xaxis_title='Date',
    #     yaxis_title='Temperature (°C)',
    #     hovermode='x unified',
    #     template='plotly_white',
    #     title_x=0.5
    # )

    # fig.write_html('temperature_plot.html')

if __name__ == "__main__":
    main()
