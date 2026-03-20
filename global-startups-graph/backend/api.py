"""FastAPI REST API for Global Startups Knowledge Graph."""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from queries import StartupGraph

graph: Optional[StartupGraph] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    graph = StartupGraph()
    yield
    graph.close()


app = FastAPI(
    title="Global Startups Knowledge Graph API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Industry endpoints
# ------------------------------------------------------------------

@app.get("/industries/by-region")
def industries_by_region():
    return graph.industry_by_region()


@app.get("/industries/ranking")
def industries_ranking(limit: int = 10):
    return graph.top_industries_by_funding(limit=limit)


@app.get("/industries/{name}")
def industry_performance(name: str):
    return graph.industry_performance(name)


@app.get("/industries/{name}/startups")
def industry_startups(name: str, sort_by: str = "funding_usd", limit: int = 50):
    return graph.startups_in_industry(name, sort_by=sort_by, limit=limit)


# ------------------------------------------------------------------
# Geographic endpoints
# ------------------------------------------------------------------

@app.get("/cities/specializations")
def city_specializations():
    return graph.city_specializations()


@app.get("/regions/compare")
def regions_compare():
    return graph.region_comparison()


# ------------------------------------------------------------------
# Investor endpoints
# ------------------------------------------------------------------

@app.get("/investors/top-pairs")
def investor_top_pairs(limit: int = 20):
    return graph.top_investor_pairs(limit=limit)


@app.get("/investors/by-industry/{industry}")
def investors_by_industry(industry: str):
    return graph.investors_by_industry(industry)


@app.get("/investors/{name}")
def investor_portfolio(name: str):
    return graph.investor_portfolio(name)


@app.get("/investors/{name}/network")
def investor_network(name: str, depth: int = 2):
    return graph.co_investor_network(name, depth=depth)


# ------------------------------------------------------------------
# Founder endpoints
# ------------------------------------------------------------------

@app.get("/founders/serial")
def serial_founders():
    return graph.serial_founders()


# ------------------------------------------------------------------
# Graph / path endpoints
# ------------------------------------------------------------------

@app.get("/graph/shortest-path")
def shortest_path(
    from_entity: str = Query(..., alias="from"),
    to_entity: str = Query(..., alias="to"),
):
    result = graph.shortest_path(from_entity, to_entity)
    if result is None:
        return {"error": "No path found"}
    return result


@app.get("/startups/{startup_id}/similar")
def similar_startups(startup_id: str, limit: int = 10):
    return graph.similar_startups(startup_id, limit=limit)


@app.get("/startups/compare")
def compare_startups(a: str = Query(...), b: str = Query(...)):
    return graph.common_investors(a, b)


# ------------------------------------------------------------------
# Ecosystem endpoint
# ------------------------------------------------------------------

@app.get("/ecosystems/{city}")
def ecosystem_summary(city: str):
    return graph.ecosystem_summary(city)


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------

@app.get("/search")
def search(q: str = Query(...), limit: int = 20):
    return graph.search(q, limit=limit)


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
