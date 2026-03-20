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
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ic:IndustryCategory) REQUIRE ic.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fb:FundingBracket) REQUIRE fb.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fc:FoundedCohort) REQUIRE fc.name IS UNIQUE",
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
        print("\n=== Ingesting Startup -> City relationships ===")
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
        print("\n=== Ingesting Startup -> Industry relationships ===")
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
        print("\n=== Ingesting Startup -> FundingStage relationships ===")
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
    # Phase 2: Hierarchical structures
    # ------------------------------------------------------------------
    def ingest_industry_categories(self, taxonomy_df):
        """Create IndustryCategory parent nodes and link Industries to them."""
        print("\n=== Ingesting Industry Categories (hierarchy) ===")
        cats = taxonomy_df["canonical_category"].dropna().unique().tolist()
        rows = [{"name": c} for c in cats if c and c != "nan"]
        self.run_batch(
            "UNWIND $rows AS row MERGE (ic:IndustryCategory {name: row.name})",
            rows, "IndustryCategory nodes",
        )
        # Link raw Industry nodes to their parent category
        mappings = []
        for _, r in taxonomy_df.iterrows():
            raw = clean_val(r.get("raw_tag"))
            cat = clean_val(r.get("canonical_category"))
            if raw and cat:
                mappings.append({"raw": raw, "cat": cat})
        # Also ensure primary industries map to themselves as categories
        for c in cats:
            mappings.append({"raw": c, "cat": c})
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (i:Industry {name: row.raw})
            MATCH (ic:IndustryCategory {name: row.cat})
            MERGE (i)-[:PART_OF_CATEGORY]->(ic)""",
            mappings, "PART_OF_CATEGORY",
        )

    def ingest_funding_brackets(self, startups_df):
        """Create FundingBracket nodes and link startups."""
        print("\n=== Ingesting Funding Brackets ===")
        brackets = [
            {"name": "Bootstrapped (<$1M)", "min": 0, "max": 1_000_000},
            {"name": "Early ($1M-$10M)", "min": 1_000_000, "max": 10_000_000},
            {"name": "Growth ($10M-$50M)", "min": 10_000_000, "max": 50_000_000},
            {"name": "Scale ($50M-$200M)", "min": 50_000_000, "max": 200_000_000},
            {"name": "Late ($200M-$1B)", "min": 200_000_000, "max": 1_000_000_000},
            {"name": "Mega ($1B+)", "min": 1_000_000_000, "max": 999_000_000_000},
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MERGE (fb:FundingBracket {name: row.name})
            SET fb.min_usd = row.min, fb.max_usd = row.max""",
            brackets, "FundingBracket nodes",
        )
        # Link startups
        rows = []
        for _, r in startups_df.iterrows():
            f = clean_float(r.get("funding_usd"))
            if f is None:
                continue
            for b in brackets:
                if b["min"] <= f < b["max"]:
                    rows.append({"startup_id": r["startup_id"], "bracket": b["name"]})
                    break
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (s:Startup {startup_id: row.startup_id})
            MATCH (fb:FundingBracket {name: row.bracket})
            MERGE (s)-[:IN_FUNDING_BRACKET]->(fb)""",
            rows, "IN_FUNDING_BRACKET",
        )

    def ingest_founded_cohorts(self, startups_df):
        """Create FoundedCohort nodes and link startups."""
        print("\n=== Ingesting Founded Cohorts ===")
        cohort_defs = [
            {"name": "Pre-2010", "min": 0, "max": 2010},
            {"name": "2010-2015", "min": 2010, "max": 2016},
            {"name": "2016-2018", "min": 2016, "max": 2019},
            {"name": "2019-2021", "min": 2019, "max": 2022},
            {"name": "2022-2024", "min": 2022, "max": 2025},
            {"name": "2025+", "min": 2025, "max": 9999},
        ]
        self.run_batch(
            """UNWIND $rows AS row
            MERGE (fc:FoundedCohort {name: row.name})
            SET fc.min_year = row.min, fc.max_year = row.max""",
            cohort_defs, "FoundedCohort nodes",
        )
        rows = []
        for _, r in startups_df.iterrows():
            y = clean_int(r.get("founded_year"))
            if y is None:
                continue
            for c in cohort_defs:
                if c["min"] <= y < c["max"]:
                    rows.append({"startup_id": r["startup_id"], "cohort": c["name"]})
                    break
        self.run_batch(
            """UNWIND $rows AS row
            MATCH (s:Startup {startup_id: row.startup_id})
            MATCH (fc:FoundedCohort {name: row.cohort})
            MERGE (s)-[:FOUNDED_IN_COHORT]->(fc)""",
            rows, "FOUNDED_IN_COHORT",
        )

    # ------------------------------------------------------------------
    # Phase 3: Computed analytical edges
    # ------------------------------------------------------------------
    def compute_investor_focus(self):
        """Investor -> FOCUSES_ON -> IndustryCategory (aggregated from portfolio)."""
        print("\n=== Computing Investor -> FOCUSES_ON -> IndustryCategory ===")
        with self.driver.session() as s:
            s.run("""
                MATCH (inv:Investor)-[:INVESTED_IN]->(s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
                WITH inv, i.name AS industry, count(DISTINCT s) AS cnt, sum(s.funding_usd) AS total
                MATCH (ic:IndustryCategory {name: industry})
                MERGE (inv)-[r:FOCUSES_ON]->(ic)
                SET r.startup_count = cnt, r.total_funding = total
            """)
            cnt = s.run("MATCH ()-[r:FOCUSES_ON]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} FOCUSES_ON edges")

    def compute_investor_active_in(self):
        """Investor -> ACTIVE_IN -> City (aggregated from portfolio geography)."""
        print("\n=== Computing Investor -> ACTIVE_IN -> City ===")
        with self.driver.session() as s:
            s.run("""
                MATCH (inv:Investor)-[:INVESTED_IN]->(s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City)
                WITH inv, c, count(DISTINCT s) AS cnt, sum(s.funding_usd) AS total
                MERGE (inv)-[r:ACTIVE_IN]->(c)
                SET r.startup_count = cnt, r.total_funding = total
            """)
            cnt = s.run("MATCH ()-[r:ACTIVE_IN]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} ACTIVE_IN edges")

    def compute_investor_stage_profile(self):
        """Investor -> INVESTS_AT_STAGE -> FundingStage."""
        print("\n=== Computing Investor -> INVESTS_AT_STAGE -> FundingStage ===")
        with self.driver.session() as s:
            s.run("""
                MATCH (inv:Investor)-[:INVESTED_IN]->(s:Startup)-[:AT_STAGE]->(fs:FundingStage)
                WITH inv, fs, count(DISTINCT s) AS cnt
                MERGE (inv)-[r:INVESTS_AT_STAGE]->(fs)
                SET r.count = cnt
            """)
            cnt = s.run("MATCH ()-[r:INVESTS_AT_STAGE]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} INVESTS_AT_STAGE edges")

    def compute_city_specializations(self):
        """City -> SPECIALIZES_IN -> IndustryCategory with Location Quotient."""
        print("\n=== Computing City -> SPECIALIZES_IN -> IndustryCategory (with LQ) ===")
        with self.driver.session() as s:
            # Get global industry distribution
            s.run("""
                // Get per-city, per-category counts
                MATCH (s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City)
                MATCH (s)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
                OPTIONAL MATCH (i)-[:PART_OF_CATEGORY]->(cat:IndustryCategory)
                WITH c, COALESCE(cat.name, i.name) AS category, count(s) AS city_cat_count
                // Get city totals
                WITH c, category, city_cat_count
                MATCH (s2:Startup)-[:LOCATED_IN {is_primary: true}]->(c)
                WITH c, category, city_cat_count, count(s2) AS city_total
                // Get global category count and global total
                MATCH (s3:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i3:Industry)
                OPTIONAL MATCH (i3)-[:PART_OF_CATEGORY]->(cat3:IndustryCategory)
                WITH c, category, city_cat_count, city_total,
                     COALESCE(cat3.name, i3.name) AS g_cat, count(s3) AS pair_count
                WITH c, category, city_cat_count, city_total,
                     sum(CASE WHEN g_cat = category THEN pair_count ELSE 0 END) AS global_cat_count,
                     sum(pair_count) AS global_total
                WITH c, category, city_cat_count, city_total, global_cat_count, global_total,
                     CASE WHEN global_cat_count = 0 OR city_total = 0 THEN 0
                     ELSE (toFloat(city_cat_count)/city_total) / (toFloat(global_cat_count)/global_total)
                     END AS lq
                MATCH (city:City {name: c.name})
                MATCH (ic:IndustryCategory {name: category})
                MERGE (city)-[r:SPECIALIZES_IN]->(ic)
                SET r.startup_count = city_cat_count,
                    r.location_quotient = round(lq * 100) / 100,
                    r.city_share = round(toFloat(city_cat_count) / city_total * 10000) / 100
            """)
            cnt = s.run("MATCH ()-[r:SPECIALIZES_IN]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} SPECIALIZES_IN edges")

    def compute_competes_with(self):
        """Startup -> COMPETES_WITH -> Startup (same category + same city)."""
        print("\n=== Computing COMPETES_WITH edges ===")
        with self.driver.session() as s:
            s.run("""
                MATCH (a:Startup)-[:IN_INDUSTRY {is_primary: true}]->(ia:Industry)
                MATCH (b:Startup)-[:IN_INDUSTRY {is_primary: true}]->(ib:Industry)
                WHERE a.startup_id < b.startup_id
                  AND ia = ib
                MATCH (a)-[:LOCATED_IN {is_primary: true}]->(c:City)<-[:LOCATED_IN {is_primary: true}]-(b)
                // Also check for shared non-primary industries
                OPTIONAL MATCH (a)-[:IN_INDUSTRY]->(shared:Industry)<-[:IN_INDUSTRY]-(b)
                WITH a, b, c, ia.name AS industry, count(DISTINCT shared) AS shared_industries
                // Check if same funding bracket
                OPTIONAL MATCH (a)-[:IN_FUNDING_BRACKET]->(fb:FundingBracket)<-[:IN_FUNDING_BRACKET]-(b)
                WITH a, b, c.name AS city, industry, shared_industries,
                     CASE WHEN fb IS NOT NULL THEN true ELSE false END AS same_bracket,
                     shared_industries * 2 + CASE WHEN fb IS NOT NULL THEN 2 ELSE 0 END AS score
                WHERE score >= 2
                MERGE (a)-[r:COMPETES_WITH]->(b)
                SET r.city = city, r.industry = industry,
                    r.shared_industries = shared_industries,
                    r.same_funding_bracket = same_bracket,
                    r.score = score
            """)
            cnt = s.run("MATCH ()-[r:COMPETES_WITH]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} COMPETES_WITH edges")

    def compute_similar_to(self):
        """Startup -> SIMILAR_TO -> Startup (cross-city structural similarity, top 5 per startup)."""
        print("\n=== Computing SIMILAR_TO edges (top 5 per startup) ===")
        with self.driver.session() as s:
            # Multi-factor similarity: shared investors (3x) + shared industries (2x)
            s.run("""
                MATCH (inv:Investor)-[:INVESTED_IN]->(a:Startup)
                MATCH (inv)-[:INVESTED_IN]->(b:Startup)
                WHERE a.startup_id < b.startup_id
                WITH a, b, count(DISTINCT inv) AS shared_investors
                WHERE shared_investors >= 1
                OPTIONAL MATCH (a)-[:IN_INDUSTRY]->(i:Industry)<-[:IN_INDUSTRY]-(b)
                WITH a, b, shared_investors, count(DISTINCT i) AS shared_industries,
                     shared_investors * 3 + count(DISTINCT i) * 2 AS score
                WHERE score >= 5
                MERGE (a)-[r:SIMILAR_TO]->(b)
                SET r.score = score, r.shared_investors = shared_investors, r.shared_industries = shared_industries
            """)
            cnt = s.run("MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} SIMILAR_TO edges")

    def compute_ecosystem_peers(self):
        """City -> ECOSYSTEM_PEER -> City (shared investors + similar industry mix)."""
        print("\n=== Computing ECOSYSTEM_PEER edges ===")
        with self.driver.session() as s:
            s.run("""
                MATCH (c1:City)<-[:LOCATED_IN]-(s1:Startup)<-[:INVESTED_IN]-(inv:Investor)-[:INVESTED_IN]->(s2:Startup)-[:LOCATED_IN]->(c2:City)
                WHERE c1.name < c2.name
                WITH c1, c2, count(DISTINCT inv) AS shared_investors
                WHERE shared_investors >= 2
                MERGE (c1)-[r:ECOSYSTEM_PEER]->(c2)
                SET r.shared_investors = shared_investors
            """)
            # Add industry similarity
            s.run("""
                MATCH (c1:City)-[sp1:SPECIALIZES_IN]->(ic:IndustryCategory)<-[sp2:SPECIALIZES_IN]-(c2:City)
                WHERE c1.name < c2.name
                WITH c1, c2, count(ic) AS shared_categories,
                     sum(abs(sp1.location_quotient - sp2.location_quotient)) AS lq_diff
                MATCH (c1)-[r:ECOSYSTEM_PEER]->(c2)
                SET r.shared_categories = shared_categories,
                    r.industry_similarity = round((1.0 / (1.0 + lq_diff)) * 100) / 100
            """)
            cnt = s.run("MATCH ()-[r:ECOSYSTEM_PEER]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} ECOSYSTEM_PEER edges")

    def compute_serial_founder_links(self):
        """Startup -> SERIAL_FOUNDER_LINK -> Startup (connected through shared founder)."""
        print("\n=== Computing SERIAL_FOUNDER_LINK edges ===")
        with self.driver.session() as s:
            s.run("""
                MATCH (a:Startup)-[:FOUNDED_BY]->(f:Founder)<-[:FOUNDED_BY]-(b:Startup)
                WHERE a.startup_id < b.startup_id
                MERGE (a)-[r:SERIAL_FOUNDER_LINK]->(b)
                SET r.founder = f.name
            """)
            cnt = s.run("MATCH ()-[r:SERIAL_FOUNDER_LINK]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"  Created {cnt} SERIAL_FOUNDER_LINK edges")

    # ------------------------------------------------------------------
    # Phase 4: Enrich node properties with computed metrics
    # ------------------------------------------------------------------
    def enrich_node_properties(self):
        """Add computed properties to Investor, City, and Startup nodes."""
        print("\n=== Enriching node properties ===")
        with self.driver.session() as s:
            # Investor: portfolio_size, primary_focus, geographic_reach
            s.run("""
                MATCH (inv:Investor)-[:INVESTED_IN]->(s:Startup)
                WITH inv, count(s) AS portfolio_size,
                     sum(s.funding_usd) AS total_funding,
                     count(DISTINCT s.city) AS geo_reach
                SET inv.portfolio_size = portfolio_size,
                    inv.portfolio_total_funding = total_funding,
                    inv.geographic_reach = geo_reach
            """)
            # Investor: primary_focus (most common category)
            s.run("""
                MATCH (inv:Investor)-[r:FOCUSES_ON]->(ic:IndustryCategory)
                WITH inv, ic.name AS cat, r.startup_count AS cnt
                ORDER BY inv.name, cnt DESC
                WITH inv, collect(cat)[0] AS top_cat
                SET inv.primary_focus = top_cat
            """)
            print("  Enriched Investor nodes")

            # City: computed stats
            s.run("""
                MATCH (c:City)<-[:LOCATED_IN {is_primary: true}]-(s:Startup)
                WITH c, count(s) AS cnt, sum(s.funding_usd) AS total,
                     avg(s.funding_usd) AS avg_f
                SET c.startup_count = cnt,
                    c.total_funding = total,
                    c.avg_funding = round(avg_f)
            """)
            # City: top_category
            s.run("""
                MATCH (c:City)-[sp:SPECIALIZES_IN]->(ic:IndustryCategory)
                WITH c, ic.name AS cat, sp.startup_count AS cnt
                ORDER BY c.name, cnt DESC
                WITH c, collect(cat)[0] AS top
                SET c.top_category = top
            """)
            print("  Enriched City nodes")

            # Startup: investor_count, competitor_count
            s.run("""
                MATCH (s:Startup)
                OPTIONAL MATCH (inv:Investor)-[:INVESTED_IN]->(s)
                WITH s, count(inv) AS inv_cnt
                SET s.investor_count = inv_cnt
            """)
            print("  Enriched Startup nodes")

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
        taxonomy_df = read_csv("industry_taxonomy.csv")

        print(f"  startups: {len(startups_df)}")
        print(f"  founders: {len(founders_df)}")
        print(f"  investors: {len(investors_df)}")
        print(f"  co_investments: {len(co_invest_df)}")
        print(f"  multi-city mappings: {len(cities_df)}")
        print(f"  taxonomy mappings: {len(taxonomy_df)}")

        self.create_constraints()

        # Phase 1: Core nodes and relationships
        self.ingest_regions(startups_df)
        self.ingest_countries(startups_df)
        self.ingest_cities(startups_df)
        self.ingest_industries(startups_df)
        self.ingest_funding_stages(startups_df)
        self.ingest_startups(startups_df)
        self.ingest_founders(founders_df)
        self.ingest_investors(investors_df)

        self.ingest_startup_city_rels(startups_df, cities_df)
        self.ingest_startup_industry_rels(startups_df)
        self.ingest_startup_stage_rels(startups_df)
        self.ingest_co_investments(co_invest_df)

        # Phase 2: Hierarchical structures
        self.ingest_industry_categories(taxonomy_df)
        self.ingest_funding_brackets(startups_df)
        self.ingest_founded_cohorts(startups_df)

        # Phase 3: Computed analytical edges
        self.compute_investor_focus()
        self.compute_investor_active_in()
        self.compute_investor_stage_profile()
        self.compute_city_specializations()
        self.compute_competes_with()
        self.compute_similar_to()
        self.compute_ecosystem_peers()
        self.compute_serial_founder_links()

        # Phase 4: Enrich node properties
        self.enrich_node_properties()

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
