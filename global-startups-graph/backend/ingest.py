"""Ingest CSV data into Neo4j knowledge graph."""
import os
import sys
import math
import time

import pandas as pd
from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, DATA_DIR

BATCH_SIZE = 500


def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    return pd.read_csv(path, encoding="utf-8-sig")


def clean_val(val):
    """Return None for NaN/empty/N/A, otherwise the value."""
    if pd.isna(val):
        return None
    if isinstance(val, str) and val.strip() in ("", "N/A", "nan", "NaN"):
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def clean_float(val):
    if pd.isna(val):
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def clean_int(val):
    if pd.isna(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class GraphIngester:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.driver.verify_connectivity()
        print(f"Connected to Neo4j at {NEO4J_URI}")

    def close(self):
        self.driver.close()

    def run(self, query, **params):
        with self.driver.session() as s:
            s.run(query, **params)

    def run_batch(self, query, rows, label=""):
        total = len(rows)
        count = 0
        for batch in batched(rows, BATCH_SIZE):
            with self.driver.session() as s:
                s.run(query, rows=batch)
            count += len(batch)
            print(f"  {label}: {count}/{total}")

    # ------------------------------------------------------------------
    # Schema setup
    # ------------------------------------------------------------------
    def create_constraints(self):
        print("\n=== Creating constraints & indexes ===")
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Startup) REQUIRE s.startup_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Region) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (co:Country) REQUIRE co.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (inv:Investor) REQUIRE inv.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Founder) REQUIRE f.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fs:FundingStage) REQUIRE fs.name IS UNIQUE",
        ]
        for c in constraints:
            self.run(c)
            print(f"  {c.split('FOR')[1].split('REQUIRE')[0].strip()}")

        # Additional indexes for query performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (s:Startup) ON (s.name)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Startup) ON (s.funding_usd)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Startup) ON (s.founded_year)",
        ]
        for idx in indexes:
            self.run(idx)

        # Full-text search indexes
        try:
            self.run(
                "CREATE FULLTEXT INDEX startupSearch IF NOT EXISTS "
                "FOR (s:Startup) ON EACH [s.name, s.description]"
            )
            self.run(
                "CREATE FULLTEXT INDEX investorSearch IF NOT EXISTS "
                "FOR (i:Investor) ON EACH [i.name]"
            )
            self.run(
                "CREATE FULLTEXT INDEX founderSearch IF NOT EXISTS "
                "FOR (f:Founder) ON EACH [f.name]"
            )
            print("  Full-text indexes created")
        except Exception as e:
            print(f"  Full-text index note: {e}")

    # ------------------------------------------------------------------
    # Node ingestion
    # ------------------------------------------------------------------
    def ingest_regions(self, startups_df):
        print("\n=== Ingesting Regions ===")
        regions = startups_df["region"].dropna().unique().tolist()
        rows = [{"name": r} for r in regions]
        self.run_batch(
            "UNWIND $rows AS row MERGE (r:Region {name: row.name})",
            rows, "Regions",
        )

    def ingest_countries(self, startups_df):
        print("\n=== Ingesting Countries ===")
        pairs = startups_df[["country", "region"]].drop_duplicates().dropna()
        rows = [{"name": r["country"], "region": r["region"]} for _, r in pairs.iterrows()]
        self.run_batch(
            """UNWIND $rows AS row
            MERGE (co:Country {name: row.name})
            WITH co, row
            MATCH (r:Region {name: row.region})
            MERGE (co)-[:IN_REGION]->(r)""",
            rows, "Countries",
        )

    def ingest_cities(self, startups_df):
        print("\n=== Ingesting Cities ===")
        triples = startups_df[["city", "country", "region"]].drop_duplicates().dropna()
        rows = [
            {"name": r["city"], "country": r["country"], "region": r["region"]}
            for _, r in triples.iterrows()
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MERGE (c:City {name: row.name})
            SET c.country = row.country, c.region = row.region
            WITH c, row
            MATCH (co:Country {name: row.country})
            MERGE (c)-[:IN_COUNTRY]->(co)""",
            rows, "Cities",
        )

    def ingest_industries(self, startups_df):
        print("\n=== Ingesting Industries ===")
        industries = set()
        for tags in startups_df["industry_tags"].dropna():
            for t in str(tags).split("|"):
                t = t.strip()
                if t and t != "nan":
                    industries.add(t)
        # Also add primary industries
        for ind in startups_df["primary_industry"].dropna().unique():
            industries.add(ind)

        rows = [{"name": i} for i in sorted(industries)]
        self.run_batch(
            "UNWIND $rows AS row MERGE (i:Industry {name: row.name})",
            rows, "Industries",
        )

    def ingest_funding_stages(self, startups_df):
        print("\n=== Ingesting Funding Stages ===")
        stages = [s for s in startups_df["funding_stage"].dropna().unique() if s.strip()]
        rows = [{"name": s} for s in stages]
        self.run_batch(
            "UNWIND $rows AS row MERGE (fs:FundingStage {name: row.name})",
            rows, "FundingStages",
        )

    def ingest_startups(self, startups_df):
        print("\n=== Ingesting Startups ===")
        rows = []
        for _, r in startups_df.iterrows():
            row = {
                "startup_id": r["startup_id"],
                "name": clean_val(r["name"]),
                "website": clean_val(r.get("website")),
                "description": clean_val(r.get("description")),
                "founded_year": clean_int(r.get("founded_year")),
                "funding_usd": clean_float(r.get("funding_usd")),
                "revenue_usd": clean_float(r.get("revenue_usd")),
                "funding_raw": clean_val(r.get("funding_raw")),
                "revenue_raw": clean_val(r.get("revenue_raw")),
                "funding_stage": clean_val(r.get("funding_stage")),
                "team_size_min": clean_int(r.get("team_size_min")),
                "team_size_max": clean_int(r.get("team_size_max")),
                "team_size_category": clean_val(r.get("team_size_category")),
                "city": clean_val(r.get("city")),
                "primary_industry": clean_val(r.get("primary_industry")),
                "industry_tags": clean_val(r.get("industry_tags")),
            }
            rows.append(row)

        self.run_batch(
            """UNWIND $rows AS row
            MERGE (s:Startup {startup_id: row.startup_id})
            SET s.name = row.name,
                s.website = row.website,
                s.description = row.description,
                s.founded_year = row.founded_year,
                s.funding_usd = row.funding_usd,
                s.revenue_usd = row.revenue_usd,
                s.funding_raw = row.funding_raw,
                s.revenue_raw = row.revenue_raw,
                s.team_size_min = row.team_size_min,
                s.team_size_max = row.team_size_max,
                s.team_size_category = row.team_size_category
            """,
            rows, "Startups",
        )

    # ------------------------------------------------------------------
    # Relationship ingestion
    # ------------------------------------------------------------------
    def ingest_startup_city_rels(self, startups_df, cities_df):
        print("\n=== Ingesting Startup → City relationships ===")
        # Primary city
        rows = [
            {"startup_id": r["startup_id"], "city": r["city"]}
            for _, r in startups_df.iterrows()
            if clean_val(r.get("city"))
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (s:Startup {startup_id: row.startup_id})
            MATCH (c:City {name: row.city})
            MERGE (s)-[rel:LOCATED_IN]->(c)
            SET rel.is_primary = true""",
            rows, "Primary City",
        )
        # Multi-city
        if not cities_df.empty:
            rows = [
                {"startup_id": r["startup_id"], "city": r["city"]}
                for _, r in cities_df.iterrows()
            ]
            self.run_batch(
                """UNWIND $rows AS row
                MATCH (s:Startup {startup_id: row.startup_id})
                MATCH (c:City {name: row.city})
                MERGE (s)-[rel:LOCATED_IN]->(c)
                ON CREATE SET rel.is_primary = false""",
                rows, "Multi-City",
            )

    def ingest_startup_industry_rels(self, startups_df):
        print("\n=== Ingesting Startup → Industry relationships ===")
        rows = []
        for _, r in startups_df.iterrows():
            primary = clean_val(r.get("primary_industry"))
            tags_str = clean_val(r.get("industry_tags"))
            if not tags_str:
                if primary:
                    rows.append({"startup_id": r["startup_id"], "industry": primary, "is_primary": True})
                continue
            tags = [t.strip() for t in str(tags_str).split("|") if t.strip() and t.strip() != "nan"]
            for tag in tags:
                rows.append({
                    "startup_id": r["startup_id"],
                    "industry": tag,
                    "is_primary": tag == primary,
                })

        self.run_batch(
            """UNWIND $rows AS row
            MATCH (s:Startup {startup_id: row.startup_id})
            MATCH (i:Industry {name: row.industry})
            MERGE (s)-[rel:IN_INDUSTRY]->(i)
            SET rel.is_primary = row.is_primary""",
            rows, "Industry",
        )

    def ingest_startup_stage_rels(self, startups_df):
        print("\n=== Ingesting Startup → FundingStage relationships ===")
        rows = [
            {"startup_id": r["startup_id"], "stage": r["funding_stage"]}
            for _, r in startups_df.iterrows()
            if clean_val(r.get("funding_stage"))
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (s:Startup {startup_id: row.startup_id})
            MATCH (fs:FundingStage {name: row.stage})
            MERGE (s)-[:AT_STAGE]->(fs)""",
            rows, "FundingStage",
        )

    def ingest_founders(self, founders_df):
        print("\n=== Ingesting Founders ===")
        # Create founder nodes
        unique_founders = founders_df.drop_duplicates(subset=["founder_id"])
        rows = [
            {"name": r["founder_name"], "founder_id": r["founder_id"]}
            for _, r in unique_founders.iterrows()
            if clean_val(r.get("founder_name"))
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MERGE (f:Founder {name: row.name})
            SET f.founder_id = row.founder_id""",
            rows, "Founder nodes",
        )
        # Create relationships
        rows = [
            {"startup_id": r["startup_id"], "founder_name": r["founder_name"]}
            for _, r in founders_df.iterrows()
            if clean_val(r.get("founder_name"))
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (s:Startup {startup_id: row.startup_id})
            MATCH (f:Founder {name: row.founder_name})
            MERGE (s)-[:FOUNDED_BY]->(f)""",
            rows, "FOUNDED_BY",
        )

    def ingest_investors(self, investors_df):
        print("\n=== Ingesting Investors ===")
        # Create investor nodes
        unique_investors = investors_df.drop_duplicates(subset=["investor_id"])
        rows = [
            {"name": r["investor_name"], "investor_id": r["investor_id"]}
            for _, r in unique_investors.iterrows()
            if clean_val(r.get("investor_name"))
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MERGE (inv:Investor {name: row.name})
            SET inv.investor_id = row.investor_id""",
            rows, "Investor nodes",
        )
        # Create INVESTED_IN relationships
        rows = [
            {
                "startup_id": r["startup_id"],
                "investor_name": r["investor_name"],
                "funding_stage": clean_val(r.get("funding_stage")) or "",
            }
            for _, r in investors_df.iterrows()
            if clean_val(r.get("investor_name"))
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (inv:Investor {name: row.investor_name})
            MATCH (s:Startup {startup_id: row.startup_id})
            MERGE (inv)-[rel:INVESTED_IN]->(s)
            SET rel.funding_stage = row.funding_stage""",
            rows, "INVESTED_IN",
        )

    def ingest_co_investments(self, co_invest_df):
        print("\n=== Ingesting Co-Investment edges ===")
        if co_invest_df.empty:
            print("  No co-investment data")
            return

        # Aggregate: count per (investor_a, investor_b) pair
        agg = co_invest_df.groupby(["investor_a", "investor_b"]).agg(
            count=("startup_id", "size"),
            startups=("startup_id", lambda x: list(x)),
            cities=("city", lambda x: list(set(x))),
        ).reset_index()

        rows = [
            {
                "investor_a": r["investor_a"],
                "investor_b": r["investor_b"],
                "count": int(r["count"]),
            }
            for _, r in agg.iterrows()
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (a:Investor {name: row.investor_a})
            MATCH (b:Investor {name: row.investor_b})
            MERGE (a)-[rel:CO_INVESTED_WITH]->(b)
            SET rel.count = row.count""",
            rows, "CO_INVESTED_WITH",
        )

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------
    def ingest_all(self):
        t0 = time.time()

        print("Loading CSVs...")
        startups_df = read_csv("startups_master.csv")
        founders_df = read_csv("founders.csv")
        investors_df = read_csv("investors.csv")
        co_invest_df = read_csv("co_investments.csv")
        cities_df = read_csv("startup_cities.csv")

        print(f"  startups: {len(startups_df)}")
        print(f"  founders: {len(founders_df)}")
        print(f"  investors: {len(investors_df)}")
        print(f"  co_investments: {len(co_invest_df)}")
        print(f"  multi-city mappings: {len(cities_df)}")

        self.create_constraints()

        # Nodes
        self.ingest_regions(startups_df)
        self.ingest_countries(startups_df)
        self.ingest_cities(startups_df)
        self.ingest_industries(startups_df)
        self.ingest_funding_stages(startups_df)
        self.ingest_startups(startups_df)
        self.ingest_founders(founders_df)
        self.ingest_investors(investors_df)

        # Relationships
        self.ingest_startup_city_rels(startups_df, cities_df)
        self.ingest_startup_industry_rels(startups_df)
        self.ingest_startup_stage_rels(startups_df)
        self.ingest_co_investments(co_invest_df)

        elapsed = time.time() - t0
        print(f"\n{'='*60}")
        print(f"INGESTION COMPLETE in {elapsed:.1f}s")
        print(f"{'='*60}")

        # Summary
        with self.driver.session() as s:
            result = s.run(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC"
            )
            print("\nNode counts:")
            for rec in result:
                print(f"  {rec['label']}: {rec['cnt']}")

            result = s.run(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS cnt ORDER BY cnt DESC"
            )
            print("\nRelationship counts:")
            for rec in result:
                print(f"  {rec['type']}: {rec['cnt']}")


if __name__ == "__main__":
    ingester = GraphIngester()
    try:
        ingester.ingest_all()
    finally:
        ingester.close()
