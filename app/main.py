from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from functools import lru_cache
from typing import Tuple, Dict, List, Any
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

def get_city_list() -> Tuple[List[Dict[str, Any]], float]:
    """Fetches a sorted list of cities with their temperature delta and computes the Austria average.

    Returns:
        Tuple[List[Dict[str, Any]], float]: 
            - List of dictionaries with city names and delta_temp, sorted descending by delta_temp.
            - The average delta_temp across Austria, rounded to 2 decimals.
    """
    df = con.execute("SELECT DISTINCT name, delta_temp FROM station_frontend_data").fetchdf()
    df = df.sort_values(by="delta_temp", ascending=False)
    scroll_list = df.to_dict(orient='records')
    austria_average = round(df["delta_temp"].mean(), 2)
    return scroll_list, austria_average

scroll_list, austria_average = get_city_list()

# Fetch the relevant columns from the view
df: pd.DataFrame = con.execute("""
    SELECT DISTINCT id, name, latitude, longitude
    FROM station_frontend_data
""").fetch_df()

# Generate TOWN_ID_MAPPING
TOWN_ID_MAPPING: Dict[str, int] = df[["name", "id"]].set_index("name").to_dict()["id"]

# Generate TOWNS list
df = df[["name", "latitude", "longitude"]].sort_values(by="name")
df.rename(columns={"latitude": "lat", "longitude": "lon"}, inplace=True)
TOWNS: List[Dict[str, Any]] = df.to_dict(orient='records')

@lru_cache
def get_station_summary() -> pd.DataFrame:
    """Fetches the full station summary data from the DuckDB database.

    Returns:
        pd.DataFrame: DataFrame containing all rows from station_frontend_data.
    """
    return con.execute("SELECT * FROM station_frontend_data").fetch_df()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, town: str = "Aigen im Ennstal") -> HTMLResponse:
    """Renders the home page with climate data for the selected town.

    Args:
        request (Request): The incoming HTTP request.
        town (str, optional): The selected town. Defaults to "Aigen im Ennstal".

    Returns:
        HTMLResponse: Rendered HTML page.
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "town": town,
        "towns": TOWNS,
        "scroll_list": scroll_list,
        "austria_average": austria_average,
    })

@app.get("/data")
async def get_city_data(town: str = "Aigen im Ennstal") -> JSONResponse:
    """Returns climate data for a given town as JSON.

    Args:
        town (str, optional): The selected town. Defaults to "Aigen im Ennstal".

    Returns:
        JSONResponse: JSON containing climate data for the selected town.
    """
    selection = TOWN_ID_MAPPING.get(town, 105)

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
