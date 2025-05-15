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

def get_top_bottom_cities():

    df = con.execute("SELECT DISTINCT name, delta_temp FROM station_frontend_data").fetchdf()

    top5_cities = df.nlargest(5, 'delta_temp')
    bottom5_cities = df.nsmallest(5, 'delta_temp')

    top_5 = top5_cities.to_dict(orient='records')
    bottom_5 = bottom5_cities.to_dict(orient='records')

    return (top_5, bottom_5)

TOP_5, BOTTOM_5 = get_top_bottom_cities()

# Fetch the relevant columns from the view
df = con.execute("""
    SELECT DISTINCT ON (id)
        id, name, latitude, longitude
    FROM station_frontend_data
""").fetch_df()

# Generate TOWN_ID_MAPPING
TOWN_ID_MAPPING = {row["name"]: str(row["id"]) for _, row in df.iterrows()}

# Generate TOWNS list
TOWNS = [{"name": row["name"], "lat": row["latitude"], "lon": row["longitude"]} for _, row in df.iterrows()]

@lru_cache
def get_station_summary() -> pd.DataFrame:
    return con.execute("SELECT * FROM station_frontend_data").fetchdf()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "towns": TOWNS,
        "top_5": TOP_5,
        "bottom_5": BOTTOM_5,
    })

@app.get("/data")
async def get_city_data(town: str = "Vienna"):
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
