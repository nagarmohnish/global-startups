"""FastAPI REST API for Global Startups Knowledge Graph."""
from contextlib import asynccontextmanager
from typing import List, Optional
from urllib.parse import unquote

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
    version="2.0.0",
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
    return graph.industry_performance(unquote(name))


@app.get("/industries/{name}/startups")
def industry_startups(name: str, sort_by: str = "funding_usd", limit: int = 50):
    return graph.startups_in_industry(unquote(name), sort_by=sort_by, limit=limit)


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
    return graph.investors_by_industry(unquote(industry))


@app.get("/investors/{name}")
def investor_portfolio(name: str):
    return graph.investor_portfolio(unquote(name))


@app.get("/investors/{name}/network")
def investor_network(name: str, depth: int = 2):
    return graph.co_investor_network(unquote(name), depth=depth)


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
    return graph.ecosystem_summary(unquote(city))


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


# ==================================================================
# NEW ENDPOINTS
# ==================================================================

# ------------------------------------------------------------------
# Startup profile & related
# ------------------------------------------------------------------

@app.get("/startup/{startup_id}")
def startup_profile(startup_id: str):
    """Full startup profile with all relationships."""
    result = graph.startup_profile(startup_id)
    if result is None:
        return {"error": "Startup not found"}
    return result


@app.get("/startup/{startup_id}/competitors")
def startup_competitors(startup_id: str):
    """Competition landscape for a startup."""
    result = graph.startup_competitors(startup_id)
    if result is None:
        return {"error": "Startup not found"}
    return result


@app.get("/startup/{startup_id}/investor-match")
def investor_match(startup_id: str):
    """Find investors who fund similar startups but haven't invested here."""
    result = graph.investor_match(startup_id)
    if result is None:
        return {"error": "Startup not found"}
    return result


# ------------------------------------------------------------------
# Investor thesis
# ------------------------------------------------------------------

@app.get("/investor/{name}/thesis")
def investor_thesis(name: str):
    """Investor thesis analysis: portfolio, focus areas, stages."""
    return graph.investor_thesis(unquote(name))


# ------------------------------------------------------------------
# City profile
# ------------------------------------------------------------------

@app.get("/city/{name}/profile")
def city_profile(name: str):
    """Full city profile with LQ scores, ecosystem peers, stages."""
    return graph.city_profile(unquote(name))


# ------------------------------------------------------------------
# Industry overview
# ------------------------------------------------------------------

@app.get("/industry/{name}/overview")
def industry_overview(name: str):
    """Industry overview: counts, funding, geography, investors."""
    return graph.industry_overview(unquote(name))


# ------------------------------------------------------------------
# Autocomplete
# ------------------------------------------------------------------

@app.get("/autocomplete")
def autocomplete(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    """Fast prefix search across all entity types."""
    return graph.autocomplete(q, limit=limit)


# ------------------------------------------------------------------
# Graph neighborhood (Sigma.js)
# ------------------------------------------------------------------

@app.get("/graph/neighborhood")
def graph_neighborhood(
    name: str = Query(...),
    depth: int = Query(1, ge=1, le=3),
):
    """Return nodes and edges within N hops for Sigma.js visualization."""
    return graph.graph_neighborhood(name, depth=depth)


# ------------------------------------------------------------------
# Global stats
# ------------------------------------------------------------------

@app.get("/stats")
def global_stats():
    """Total startups, funding, investors, founders, cities, industries, cohorts."""
    return graph.global_stats()


# ------------------------------------------------------------------
# City comparison analytics
# ------------------------------------------------------------------

@app.get("/analytics/city-comparison")
def city_comparison(cities: str = Query(..., description="Comma-separated city names (2-4)")):
    """Compare 2-4 cities side by side."""
    city_list = [c.strip() for c in cities.split(",") if c.strip()]
    if len(city_list) < 2:
        return {"error": "Provide at least 2 cities (comma-separated)"}
    return graph.city_comparison(city_list)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
