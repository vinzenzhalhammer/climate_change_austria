from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from functools import lru_cache
from typing import Tuple, Dict
import duckdb
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%m-%d-%Y %H:%M:%S',
    level=logging.INFO
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

con = duckdb.connect("data.duckdb")

def get_city_list():

    df = con.execute("SELECT DISTINCT name, delta_temp FROM station_frontend_data").fetchdf()
    df = df.sort_values(by="delta_temp", ascending=False)
    scroll_list = df.to_dict(orient='records')

    return scroll_list

scroll_list = get_city_list()

# Fetch the relevant columns from the view
df = con.execute("""
    SELECT DISTINCT ON (id)
        id, name, latitude, longitude
    FROM station_frontend_data
""").fetch_df()

# Generate TOWN_ID_MAPPING
TOWN_ID_MAPPING = df[["name", "id"]].set_index("name").to_dict()["id"]

# Generate TOWNS list
df = df[["name", "latitude", "longitude"]].sort_values(by="name")
df.rename(columns={"latitude": "lat", "longitude": "lon"}, inplace=True)
TOWNS = df.to_dict(orient='records')

@lru_cache
def get_station_summary() -> pd.DataFrame:
    return con.execute("SELECT * FROM station_frontend_data").fetchdf()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "towns": TOWNS,
        "scroll_list": scroll_list
    })

@app.get("/data")
async def get_city_data(town: str = "Aigen im Ennstal"):
    selection = TOWN_ID_MAPPING.get(town, '105')

    df = get_station_summary()
    df = df[df["id"] == int(selection)]
    pre_industrial = df["post2000_temp"].iloc[0]
    modern_avg = df["pre1970_temp"].iloc[0]
    delta = df["delta_temp"].iloc[0]
    labels = df["year"].tolist()
    smoothed_data =  df["rolling_avg_temp_10y"].tolist()

    return JSONResponse({
        "town": town,
        "pre_industrial": pre_industrial,
        "modern_avg": modern_avg,
        "delta": delta,
        "labels": labels,
        "smoothed_data": smoothed_data
    })
