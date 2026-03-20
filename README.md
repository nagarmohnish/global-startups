# Global Startups Intelligence Platform

An end-to-end data platform that maps the global startup ecosystem across 20 cities, 13 countries, and 6 regions. Combines web-scraped data from multiple sources, normalizes it into analysis-ready formats, and powers a Neo4j knowledge graph with a React-based explorer UI.

## What This Does

Takes raw, messy startup data from three independent sources (Failory, Seedtable, F6S), merges and deduplicates it, enriches missing fields via automated web research, normalizes everything into a consistent schema, and loads it into a graph database that reveals connections invisible in flat tables — like which investors bridge two industries, which cities have structurally similar ecosystems, or which startups compete in the same market.

## Dataset

**3,022 unique startups** after deduplication, across:

| Region | Cities | Startups | Median Funding |
|--------|--------|----------|----------------|
| Europe | London, Berlin, Paris, Zurich, Stockholm, Madrid | 1,188 | $25M |
| East Asia | Beijing, Shanghai, Shenzhen, Hangzhou, Guangzhou, Tokyo, Seoul | 701 | $50M |
| North America | Silicon Valley, NYC, Boston, Los Angeles | 596 | $75.3M |
| Southeast Asia | Singapore | 225 | $30M |
| Latin America | Sao Paulo | 214 | $21.9M |
| Middle East | Tel Aviv | 98 | $40M |

**Top industries:** AI/ML (570), Fintech (543), SaaS/Software (424), Healthcare/Biotech (275), Media/Entertainment (225), Robotics/Hardware (216)

**Data completeness:** Website 98.5%, Industry 100%, Description 99.7%, Founded Year 94.3%, Funding 93.9%, Funding Stage 90.2%

## Architecture

```
                    ┌─────────────┐
                    │  3 Sources  │   Failory, Seedtable, F6S
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Scrapers   │   52 JSON files across 20 cities
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Enrichment │   Automated web search (DuckDuckGo)
                    │  & QA       │   Website validation, description cleanup
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Normalize   │   10-stage pipeline: dedup, currency
                    │ Pipeline    │   conversion, industry taxonomy, etc.
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌──▼───┐ ┌──────▼──────┐
       │  7 CSVs +   │ │ Excel│ │   Neo4j     │
       │  Parquet    │ │ 20   │ │  Knowledge  │
       │             │ │ tabs │ │   Graph     │
       └─────────────┘ └──────┘ └──────┬──────┘
                                       │
                                ┌──────▼──────┐
                                │  FastAPI    │   16 REST endpoints
                                └──────┬──────┘
                                       │
                                ┌──────▼──────┐
                                │   React     │   Explorer UI
                                │  Frontend   │
                                └─────────────┘
```

## Repository Structure

```
├── data/                           # 52 raw JSON files from 3 sources
│   ├── failory_*.json              # Failory scrapes (20 cities)
│   ├── seedtable_*.json            # Seedtable scrapes (20 cities)
│   └── f6s_*.json                  # F6S scrapes (12 cities)
│
├── scrapers/                       # Data collection & enrichment scripts
│   ├── berlin.py, london.py ...    # City-specific scrapers
│   ├── generic.py                  # Generic F6S scraper
│   ├── research_missing.py         # v1 web search enrichment
│   ├── research_v2.py              # v2 targeted enrichment (5 fields)
│   ├── fix_data_quality.py         # Bad data detection & cleanup
│   ├── fix_websites.py             # Website URL validation
│   └── fix_remaining.py            # Final quality pass
│
├── scripts/
│   ├── add_cities.py               # Merge sources → Excel workbook
│   └── normalize_pipeline.py       # 10-stage normalization pipeline
│
├── structured_data/                # Analysis-ready outputs
│   ├── startups_master.csv         # 3,022 startups, 23 columns
│   ├── startups_master.parquet     # Same, columnar format
│   ├── founders.csv                # 1,525 unique founders
│   ├── investors.csv               # 784 unique investors
│   ├── co_investments.csv          # 1,504 co-investor edges
│   ├── startup_cities.csv          # Multi-city mappings (63 startups)
│   ├── industry_taxonomy.csv       # 678 raw tags → 20 categories
│   ├── data_quality_report.csv     # Per-city completeness stats
│   └── cleaning_log.txt            # Full audit trail
│
├── global-startups-graph/          # Neo4j knowledge graph application
│   ├── docker-compose.yml          # Neo4j + FastAPI + React
│   ├── Makefile                    # setup, dev, ingest, clean
│   ├── data/                       # CSVs for graph ingestion
│   ├── backend/
│   │   ├── ingest.py               # Graph ingestion (4 phases)
│   │   ├── queries.py              # 17 query methods
│   │   ├── api.py                  # FastAPI REST API
│   │   └── config.py               # Connection settings
│   └── frontend/
│       └── src/
│           ├── components/
│           │   ├── Dashboard.tsx        # Heatmap, rankings, region cards
│           │   ├── IndustryDeepDive.tsx  # Industry analysis
│           │   ├── InvestorNetwork.tsx   # Portfolio & co-investor explorer
│           │   ├── CityEcosystem.tsx     # City comparison
│           │   ├── StartupDetail.tsx     # Startup profile + similarity
│           │   └── PathFinder.tsx        # Search + shortest path
│           └── api/client.ts            # API client
│
└── global_startups_final.xlsx      # Excel workbook (20 city tabs)
```

## Knowledge Graph

The Neo4j graph goes beyond basic relational mappings. It computes analytical edges during ingestion that reveal non-obvious patterns.

### Graph Schema

**11 node types:** Startup, Industry, IndustryCategory, City, Country, Region, Investor, Founder, FundingStage, FundingBracket, FoundedCohort

**19 relationship types** — 8 direct from data, 11 computed:

| Relationship | What It Reveals |
|---|---|
| `COMPETES_WITH` | Startups in same industry + same city, with similarity score |
| `SIMILAR_TO` | Structural analogs across cities (shared investors/industries) |
| `FOCUSES_ON` | What industries each investor actually bets on |
| `ACTIVE_IN` | Which cities each investor operates in |
| `INVESTS_AT_STAGE` | Seed vs Growth vs Late-stage investor profile |
| `SPECIALIZES_IN` | City industry strengths with **Location Quotient** (not just raw counts) |
| `ECOSYSTEM_PEER` | Which cities have structurally similar startup ecosystems |
| `SERIAL_FOUNDER_LINK` | Startups connected through repeat founders |
| `PART_OF_CATEGORY` | Industry taxonomy hierarchy (678 tags → 20 categories) |

**Total: 5,441 nodes, 55,162 relationships**

### Example Queries

```cypher
-- What does Berlin truly specialize in? (LQ > 1 = genuine specialization)
MATCH (c:City {name: "Berlin"})-[r:SPECIALIZES_IN]->(ic:IndustryCategory)
WHERE r.location_quotient > 1.0
RETURN ic.name, r.location_quotient ORDER BY r.location_quotient DESC

-- Investor thesis: where does General Catalyst focus?
MATCH (inv:Investor {name: "General Catalyst"})-[f:FOCUSES_ON]->(ic:IndustryCategory)
RETURN ic.name, f.startup_count ORDER BY f.startup_count DESC

-- Which cities have the most similar ecosystems?
MATCH (c1:City)-[r:ECOSYSTEM_PEER]->(c2:City)
RETURN c1.name, c2.name, r.shared_investors ORDER BY r.shared_investors DESC

-- Competition landscape for a startup
MATCH (s:Startup {name: "Revolut"})-[r:COMPETES_WITH]-(rival:Startup)
RETURN rival.name, r.score, r.industry ORDER BY r.score DESC LIMIT 10
```

## Normalization Pipeline

The `normalize_pipeline.py` script runs 10 stages:

1. **Combine** — Merge 20 Excel sheets, add City/Country/Region metadata
2. **Deduplicate** — Fuzzy name matching + domain cross-check (119 dupes removed)
3. **Normalize Funding/Revenue** — Parse 11 currency formats (USD, EUR, GBP, CNY, BRL, SEK, CHF, SGD, AUD, MYR, KRW), convert to USD
4. **Founded Year** — Clean to integer, flag pre-1990 anomalies
5. **Team Size** — Parse ranges, categories, and raw numbers into min/max/category
6. **Industry Taxonomy** — Map 678 raw tags to 20 canonical categories using fuzzy keyword matching
7. **Funding Round** — Normalize 27 raw values into 19 standard stages
8. **Founders & Investors** — Parse into relational tables with deduplication
9. **Output** — 7 CSVs + Parquet + quality report + cleaning log
10. **Validation** — Summary statistics and completeness checks

## Quick Start

### View the data
Open `global_startups_final.xlsx` — 20 tabs, one per city.

### Run the knowledge graph
```bash
cd global-startups-graph

# Start Neo4j, ingest data, launch all services
make setup

# Access:
# Neo4j Browser → http://localhost:7474 (neo4j / startupgraph)
# API docs      → http://localhost:8000/docs
# Frontend      → http://localhost:5173
```

### Re-run the normalization pipeline
```bash
python scripts/normalize_pipeline.py
```

## Data Sources

| Source | Coverage | Method |
|--------|----------|--------|
| [Failory](https://failory.com) | 20 cities, ~1,200 startups | Web scraping |
| [Seedtable](https://seedtable.com) | 20 cities, ~1,300 startups | Web scraping |
| [F6S](https://f6s.com) | 12 cities, ~1,100 startups | Web scraping |
| DuckDuckGo Search | Enrichment | Automated search for missing fields |

## Tech Stack

- **Data**: Python, pandas, openpyxl, thefuzz
- **Graph**: Neo4j 5 Community, Cypher
- **Backend**: FastAPI, neo4j Python driver
- **Frontend**: React, TypeScript, Tailwind CSS, Recharts, TanStack Query
- **Infrastructure**: Docker Compose
