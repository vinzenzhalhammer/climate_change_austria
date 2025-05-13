from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import duckdb

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

con = duckdb.connect("data.duckdb")

TOP_5 = [
    {"name": "Vienna", "delta": 2.1},
    {"name": "Graz", "delta": 1.9},
    {"name": "Linz", "delta": 1.8},
    {"name": "Salzburg", "delta": 1.7},
    {"name": "Innsbruck", "delta": 1.6},
]

BOTTOM_5 = [
    {"name": "Bregenz", "delta": 0.8},
    {"name": "Eisenstadt", "delta": 0.9},
    {"name": "Klagenfurt", "delta": 1.0},
    {"name": "Sankt Pölten", "delta": 1.1},
    {"name": "Villach", "delta": 1.2},
]

TOWN_ID_MAPPING = {
    'Vienna': '105',
    'Graz': '56',
    'Innsbruck': '39',
    'Salzburg': '6306',
    'Lienz': '55',
    'St. Paul im Lavanttal': '20501',
}

TOWNS = [
    {"name": "Vienna", "lat": 48.2082, "lon": 16.3738},
    {"name": "Graz", "lat": 47.0707, "lon": 15.4395},
    {"name": "Salzburg", "lat": 47.8095, "lon": 13.0550},
    {"name": "Lienz", "lat": 46.8298, "lon": 12.7682},
    {"name": "Innsbruck", "lat": 47.2682, "lon": 11.3923},
    {"name": "St. Paul im Lavanttal", "lat": 46.7333, "lon": 14.8667},
]

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

    df = con.execute(f"SELECT * FROM climate_data WHERE station_id = {selection}").fetchdf()
    df = df[df["date"].dt.year < 2025]

    pre_industrial = round(df[df["date"] < "1950-01-01"]["tl_mittel"].mean(), 2)
    modern_avg = round(df[df["date"] >= "2000-01-01"]["tl_mittel"].mean(), 2)

    smoothed = df["tl_mittel"].rolling(window=10).mean()
    df["smoothed"] = round(smoothed, 2)
    df_filtered = df[df["smoothed"].notna()].copy()

    delta = round(modern_avg - pre_industrial, 2)

    return JSONResponse({
        "town": town,
        "pre_industrial": pre_industrial,
        "modern_avg": modern_avg,
        "delta": delta,
        "labels": df_filtered["date"].dt.strftime("%Y").tolist(),
        "smoothed_data": df_filtered["smoothed"].tolist(),
    })
