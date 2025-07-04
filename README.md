# 🌍 Climate Change in Austria

A FastAPI-powered web application that visualizes the effects of climate change across Austrian towns using historical temperature data from a DuckDB database.

## Features

- 🌡️ Interactive display of climate data for Austrian towns
- 📊 Visualization of temperature deltas and 10-year rolling averages
- 🔍 Selectable town-specific statistics with comparison to the national average
- ⚡ Fast API and DuckDB powered backend

I also wrote a short blog post about it on my
[website](https://vinzenzhalhammer.com/blog/building_webapp_to_visualize_change_in_temperature).

## Live Demo

👉 **View the live dashboard here** [climateaustria.vinzenzhalhammer.com](https://climateaustria.vinzenzhalhammer.com)

![Screenshot of Climate Change in Austria App](assets/climate_change_dashboard.png)

## Architecture
Stack Overview:
- **Data source** Geosphere Austria API (klima-v2-1y dataset)
- **Database** DuckDB (stored locally & loaded in-memory at runtime)
- **Backend** FastAPI (serves a JSON API from precomputed DuckDB views)
- **Frontend** Leaflet + ApexCharts + TailwindCSS (interactive map + charts)
- **Deployment** Google Cloud Run (with custom domain via Cloudflare)
- **Infra tools** uv for Python env & Dockerfile builds
- **Data Flow**
data_load_pipeline.py fetches and cleans station metadata + yearly measurements
Computes rolling 10-year averages + pre/post temperature deltas
Creates a view used directly by the frontend
DuckDB makes it fast and simple to manage without needing a DB server

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/vinzenzhalhammer/climate_change_austria.git
cd climate_change_austria
```

2. **Install dependencies with [uv](https://github.com/astral-sh/uv)**

Make sure you have Python 3.12+ and `uv` installed. Alternatively, you can use `pip`, `poetry`, ... or what you prefer, the dependencies are defined in `pyproject.toml`:

```bash
uv sync
```

3. **Run the app**

```bash
uv run uvicorn main:app --reload
```

Visit [http://localhost:8000](http://localhost:8000) to view the application.

## Docker

To build and run the app in Docker:

```bash
docker-compose up --build
```
Visit [http://localhost:8080](http://localhost:8080) to view the application.

## Data Source
The application uses historical temperature data from the [Geosphere Austria](https://www.geosphere.at/en) and stores it in a DuckDB database. The data is processed to calculate temperature deltas and rolling averages.

