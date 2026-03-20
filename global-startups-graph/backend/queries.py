"""Neo4j query layer for Global Startups Knowledge Graph."""
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class StartupGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def _query(self, cypher, **params):
        with self.driver.session() as s:
            result = s.run(cypher, **params)
            return [dict(r) for r in result]

    # ==================================================================
    # Discovery queries
    # ==================================================================

    def industry_by_region(self):
        records = self._query("""
            MATCH (s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
            MATCH (s)-[:LOCATED_IN {is_primary: true}]->(c:City)-[:IN_COUNTRY]->(co:Country)-[:IN_REGION]->(r:Region)
            RETURN r.name AS region, i.name AS industry, count(s) AS count
            ORDER BY r.name, count DESC
        """)
        result = {}
        for r in records:
            result.setdefault(r["region"], {})[r["industry"]] = r["count"]
        return result

    def top_industries_by_funding(self, limit=10):
        records = self._query("""
            MATCH (s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
            WHERE s.funding_usd IS NOT NULL
            WITH i.name AS industry,
                 sum(s.funding_usd) AS total_funding,
                 avg(s.funding_usd) AS avg_funding,
                 count(s) AS startup_count,
                 collect(s.funding_usd) AS fundings
            RETURN industry, total_funding, avg_funding, startup_count,
                   fundings[toInteger(size(fundings)/2)] AS median_funding
            ORDER BY total_funding DESC
            LIMIT $limit
        """, limit=limit)
        return records

    def industry_performance(self, industry):
        # Basic stats
        stats = self._query("""
            MATCH (s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry {name: $industry})
            RETURN count(s) AS total,
                   sum(s.funding_usd) AS total_funding,
                   avg(s.funding_usd) AS avg_funding
        """, industry=industry)

        # By stage
        by_stage = self._query("""
            MATCH (s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry {name: $industry})
            MATCH (s)-[:AT_STAGE]->(fs:FundingStage)
            RETURN fs.name AS stage, count(s) AS count
            ORDER BY count DESC
        """, industry=industry)

        # By region
        by_region = self._query("""
            MATCH (s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry {name: $industry})
            MATCH (s)-[:LOCATED_IN {is_primary: true}]->(c:City)-[:IN_COUNTRY]->(co:Country)-[:IN_REGION]->(r:Region)
            RETURN r.name AS region, count(s) AS count, sum(s.funding_usd) AS total_funding
            ORDER BY count DESC
        """, industry=industry)

        # Top investors
        top_investors = self._query("""
            MATCH (inv:Investor)-[:INVESTED_IN]->(s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry {name: $industry})
            RETURN inv.name AS investor, count(DISTINCT s) AS startup_count
            ORDER BY startup_count DESC
            LIMIT 10
        """, industry=industry)

        stat = stats[0] if stats else {}
        return {
            "industry": industry,
            "total_startups": stat.get("total", 0),
            "total_funding": stat.get("total_funding"),
            "avg_funding": stat.get("avg_funding"),
            "by_stage": {r["stage"]: r["count"] for r in by_stage},
            "by_region": by_region,
            "top_investors": top_investors,
        }

    def startups_in_industry(self, industry, sort_by="funding_usd", limit=50):
        order = "s.funding_usd DESC" if sort_by == "funding_usd" else "s.name ASC"
        return self._query(f"""
            MATCH (s:Startup)-[:IN_INDUSTRY {{is_primary: true}}]->(i:Industry {{name: $industry}})
            OPTIONAL MATCH (s)-[:LOCATED_IN {{is_primary: true}}]->(c:City)
            OPTIONAL MATCH (s)-[:AT_STAGE]->(fs:FundingStage)
            RETURN s.startup_id AS startup_id, s.name AS name,
                   c.name AS city, c.country AS country,
                   s.funding_usd AS funding_usd, fs.name AS funding_stage,
                   s.founded_year AS founded_year, s.revenue_usd AS revenue_usd,
                   s.team_size_category AS team_size_category,
                   s.description AS description, s.website AS website
            ORDER BY {order}
            LIMIT $limit
        """, industry=industry, limit=limit)

    # ==================================================================
    # Geographic queries
    # ==================================================================

    def city_specializations(self):
        records = self._query("""
            MATCH (s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
            MATCH (s)-[:LOCATED_IN {is_primary: true}]->(c:City)
            WITH c.name AS city, i.name AS industry,
                 count(s) AS cnt, sum(s.funding_usd) AS funding
            ORDER BY city, cnt DESC
            WITH city, collect({industry: industry, count: cnt, funding: funding}) AS industries
            RETURN city, industries[0..3] AS top_by_count
        """)
        result = {}
        for r in records:
            result[r["city"]] = {
                "top_by_count": r["top_by_count"],
            }
        return result

    def region_comparison(self):
        return self._query("""
            MATCH (s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City)-[:IN_COUNTRY]->(co:Country)-[:IN_REGION]->(r:Region)
            WITH r.name AS region, count(s) AS startup_count,
                 sum(s.funding_usd) AS total_funding,
                 avg(s.funding_usd) AS avg_funding,
                 collect(c.name) AS cities
            OPTIONAL MATCH (s2:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
            WHERE (s2)-[:LOCATED_IN]->(:City)-[:IN_COUNTRY]->(:Country)-[:IN_REGION]->(:Region {name: region})
            WITH region, startup_count, total_funding, avg_funding, cities,
                 i.name AS industry, count(s2) AS ind_count
            ORDER BY region, ind_count DESC
            WITH region, startup_count, total_funding, avg_funding,
                 collect(industry)[0] AS top_industry
            RETURN region, startup_count, total_funding, avg_funding, top_industry
            ORDER BY startup_count DESC
        """)

    # ==================================================================
    # Investor network queries
    # ==================================================================

    def investor_portfolio(self, investor_name):
        startups = self._query("""
            MATCH (inv:Investor {name: $name})-[:INVESTED_IN]->(s:Startup)
            OPTIONAL MATCH (s)-[:LOCATED_IN {is_primary: true}]->(c:City)
            OPTIONAL MATCH (s)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
            RETURN s.startup_id AS startup_id, s.name AS name,
                   c.name AS city, i.name AS industry,
                   s.funding_usd AS funding_usd, s.funding_stage AS funding_stage
            ORDER BY s.funding_usd DESC
        """, name=investor_name)

        co_investors = self._query("""
            MATCH (inv:Investor {name: $name})-[:CO_INVESTED_WITH]-(other:Investor)
            RETURN other.name AS name, count(*) AS shared
            ORDER BY shared DESC
            LIMIT 10
        """, name=investor_name)

        industries = list({s["industry"] for s in startups if s.get("industry")})
        cities = list({s["city"] for s in startups if s.get("city")})
        total = sum(s["funding_usd"] for s in startups if s.get("funding_usd"))

        return {
            "investor": investor_name,
            "startups": startups,
            "industries": industries,
            "cities": cities,
            "co_investors": co_investors,
            "total_deployed": total,
        }

    def co_investor_network(self, investor_name, depth=2):
        records = self._query("""
            MATCH path = (inv:Investor {name: $name})-[:CO_INVESTED_WITH*1..""" + str(depth) + """]->(other:Investor)
            WITH other, min(length(path)) AS dist
            OPTIONAL MATCH (other)-[:CO_INVESTED_WITH]-(peer:Investor)
            WHERE peer <> inv
            RETURN other.name AS name, dist,
                   count(DISTINCT peer) AS connections
            ORDER BY dist, connections DESC
            LIMIT 50
        """, name=investor_name)
        return {"center": investor_name, "depth": depth, "nodes": records}

    def top_investor_pairs(self, limit=20):
        return self._query("""
            MATCH (a:Investor)-[r:CO_INVESTED_WITH]->(b:Investor)
            WITH a.name AS investor_a, b.name AS investor_b, r.count AS co_investment_count
            ORDER BY co_investment_count DESC
            LIMIT $limit
            OPTIONAL MATCH (a2:Investor {name: investor_a})-[:INVESTED_IN]->(s:Startup)<-[:INVESTED_IN]-(b2:Investor {name: investor_b})
            RETURN investor_a, investor_b, co_investment_count,
                   collect(DISTINCT s.name) AS shared_startups
        """, limit=limit)

    def investors_by_industry(self, industry):
        return self._query("""
            MATCH (inv:Investor)-[:INVESTED_IN]->(s:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry {name: $industry})
            RETURN inv.name AS investor, count(DISTINCT s) AS startup_count,
                   sum(s.funding_usd) AS total_funding
            ORDER BY startup_count DESC
            LIMIT 20
        """, industry=industry)

    # ==================================================================
    # Founder queries
    # ==================================================================

    def serial_founders(self):
        return self._query("""
            MATCH (s:Startup)-[:FOUNDED_BY]->(f:Founder)
            WITH f.name AS founder, collect(s.name) AS startups, count(s) AS cnt
            WHERE cnt > 1
            RETURN founder, startups, cnt
            ORDER BY cnt DESC
        """)

    def founder_investor_paths(self, founder_name):
        return self._query("""
            MATCH (f:Founder {name: $name})<-[:FOUNDED_BY]-(s:Startup)<-[:INVESTED_IN]-(inv:Investor)
            RETURN f.name AS founder, s.name AS startup, inv.name AS investor,
                   s.funding_usd AS funding_usd
            ORDER BY s.funding_usd DESC
        """, name=founder_name)

    # ==================================================================
    # Cross-cutting / path queries
    # ==================================================================

    def shortest_path(self, entity_a, entity_b):
        records = self._query("""
            MATCH (a), (b)
            WHERE (a.name = $a OR a.startup_id = $a)
              AND (b.name = $b OR b.startup_id = $b)
            WITH a, b LIMIT 1
            MATCH path = shortestPath((a)-[*..6]-(b))
            RETURN [n IN nodes(path) |
                CASE
                    WHEN n:Startup THEN {type: 'Startup', name: n.name, id: n.startup_id}
                    WHEN n:Investor THEN {type: 'Investor', name: n.name}
                    WHEN n:Founder THEN {type: 'Founder', name: n.name}
                    WHEN n:City THEN {type: 'City', name: n.name}
                    WHEN n:Industry THEN {type: 'Industry', name: n.name}
                    WHEN n:Region THEN {type: 'Region', name: n.name}
                    WHEN n:Country THEN {type: 'Country', name: n.name}
                    WHEN n:FundingStage THEN {type: 'FundingStage', name: n.name}
                    ELSE {type: 'Unknown', name: ''}
                END
            ] AS path_nodes,
            [r IN relationships(path) | type(r)] AS rel_types,
            length(path) AS path_length
        """, a=entity_a, b=entity_b)
        return records[0] if records else None

    def common_investors(self, startup_a_id, startup_b_id):
        return self._query("""
            MATCH (inv:Investor)-[:INVESTED_IN]->(a:Startup {startup_id: $a})
            MATCH (inv)-[:INVESTED_IN]->(b:Startup {startup_id: $b})
            RETURN inv.name AS investor, a.name AS startup_a, b.name AS startup_b
        """, a=startup_a_id, b=startup_b_id)

    def similar_startups(self, startup_id, limit=10):
        return self._query("""
            MATCH (s:Startup {startup_id: $id})

            // Industry similarity
            OPTIONAL MATCH (s)-[:IN_INDUSTRY]->(i:Industry)<-[:IN_INDUSTRY]-(other:Startup)
            WHERE other <> s
            WITH s, other, count(DISTINCT i) AS shared_industries

            // Investor similarity
            OPTIONAL MATCH (inv:Investor)-[:INVESTED_IN]->(s)
            OPTIONAL MATCH (inv)-[:INVESTED_IN]->(other)
            WITH s, other, shared_industries, count(DISTINCT inv) AS shared_investors

            // City similarity
            OPTIONAL MATCH (s)-[:LOCATED_IN]->(c:City)<-[:LOCATED_IN]-(other)
            WITH other,
                 shared_industries,
                 shared_investors,
                 count(DISTINCT c) AS same_city,
                 shared_industries * 2 + shared_investors * 3 + count(DISTINCT c) AS score
            WHERE score > 0

            OPTIONAL MATCH (other)-[:LOCATED_IN {is_primary: true}]->(oc:City)
            OPTIONAL MATCH (other)-[:IN_INDUSTRY {is_primary: true}]->(oi:Industry)

            RETURN other.startup_id AS startup_id, other.name AS name,
                   oc.name AS city, oi.name AS industry,
                   other.funding_usd AS funding_usd,
                   shared_industries, shared_investors, same_city, score
            ORDER BY score DESC
            LIMIT $limit
        """, id=startup_id, limit=limit)

    def industry_investor_overlap(self, industry_a, industry_b):
        records = self._query("""
            MATCH (inv:Investor)-[:INVESTED_IN]->(s1:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i1:Industry {name: $a})
            MATCH (inv)-[:INVESTED_IN]->(s2:Startup)-[:IN_INDUSTRY {is_primary: true}]->(i2:Industry {name: $b})
            WHERE s1 <> s2
            RETURN inv.name AS investor,
                   count(DISTINCT s1) AS count_in_a,
                   count(DISTINCT s2) AS count_in_b
            ORDER BY count_in_a + count_in_b DESC
            LIMIT 10
        """, a=industry_a, b=industry_b)
        return {
            "industry_a": industry_a,
            "industry_b": industry_b,
            "bridging_investors": records,
        }

    def ecosystem_summary(self, city):
        stats = self._query("""
            MATCH (s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City {name: $city})
            RETURN count(s) AS startup_count,
                   sum(s.funding_usd) AS total_funding,
                   avg(s.funding_usd) AS avg_funding
        """, city=city)

        industries = self._query("""
            MATCH (s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City {name: $city})
            MATCH (s)-[:IN_INDUSTRY {is_primary: true}]->(i:Industry)
            RETURN i.name AS industry, count(s) AS count, sum(s.funding_usd) AS funding
            ORDER BY count DESC
        """, city=city)

        top_startups = self._query("""
            MATCH (s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City {name: $city})
            RETURN s.startup_id AS startup_id, s.name AS name,
                   s.funding_usd AS funding_usd, s.funding_stage AS funding_stage
            ORDER BY s.funding_usd DESC
            LIMIT 10
        """, city=city)

        investors = self._query("""
            MATCH (inv:Investor)-[:INVESTED_IN]->(s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City {name: $city})
            RETURN inv.name AS investor, count(DISTINCT s) AS startups
            ORDER BY startups DESC
            LIMIT 10
        """, city=city)

        founder_count = self._query("""
            MATCH (s:Startup)-[:LOCATED_IN {is_primary: true}]->(c:City {name: $city})
            MATCH (s)-[:FOUNDED_BY]->(f:Founder)
            RETURN count(DISTINCT f) AS count
        """, city=city)

        stat = stats[0] if stats else {}
        return {
            "city": city,
            "startup_count": stat.get("startup_count", 0),
            "total_funding": stat.get("total_funding"),
            "avg_funding": stat.get("avg_funding"),
            "industries": industries,
            "top_startups": top_startups,
            "top_investors": investors,
            "founder_count": founder_count[0]["count"] if founder_count else 0,
        }

    # ==================================================================
    # Search
    # ==================================================================

    def search(self, query, limit=20):
        results = []

        # Full-text search on startups
        try:
            startups = self._query("""
                CALL db.index.fulltext.queryNodes('startupSearch', $q)
                YIELD node, score
                RETURN node.startup_id AS id, node.name AS name,
                       'Startup' AS type, score
                ORDER BY score DESC
                LIMIT $limit
            """, q=query, limit=limit)
            results.extend(startups)
        except Exception:
            pass

        # Full-text search on investors
        try:
            investors = self._query("""
                CALL db.index.fulltext.queryNodes('investorSearch', $q)
                YIELD node, score
                RETURN node.name AS id, node.name AS name,
                       'Investor' AS type, score
                ORDER BY score DESC
                LIMIT $limit
            """, q=query, limit=limit)
            results.extend(investors)
        except Exception:
            pass

        # Full-text search on founders
        try:
            founders = self._query("""
                CALL db.index.fulltext.queryNodes('founderSearch', $q)
                YIELD node, score
                RETURN node.name AS id, node.name AS name,
                       'Founder' AS type, score
                ORDER BY score DESC
                LIMIT $limit
            """, q=query, limit=limit)
            results.extend(founders)
        except Exception:
            pass

        # Exact match on cities/industries
        cities = self._query("""
            MATCH (c:City)
            WHERE toLower(c.name) CONTAINS toLower($q)
            RETURN c.name AS id, c.name AS name, 'City' AS type, 1.0 AS score
        """, q=query)
        results.extend(cities)

        industries = self._query("""
            MATCH (i:Industry)
            WHERE toLower(i.name) CONTAINS toLower($q)
            RETURN i.name AS id, i.name AS name, 'Industry' AS type, 1.0 AS score
        """, q=query)
        results.extend(industries)

        # Sort by score and deduplicate
        seen = set()
        unique = []
        for r in sorted(results, key=lambda x: -x.get("score", 0)):
            key = (r["type"], r["id"])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique[:limit]
