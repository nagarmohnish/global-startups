# StartupGraph — Product Specification

## Public Intelligence Platform for the Global Startup Ecosystem

**Version:** 1.0 Draft
**Date:** March 20, 2026
**Author:** Rahul / LH2 Holdings

---

## 1. Product Vision

**One-liner:** The open, graph-powered alternative to Crunchbase — where anyone can explore the global startup ecosystem through relationships, not just records.

**Why this wins:** Crunchbase and PitchBook are expensive ($4K-$15K/yr), flat-data tools. StartupGraph is free, graph-native, and surfaces non-obvious connections — like which investors bridge two industries, which cities have structurally similar ecosystems, or which startups are silent competitors. The computed analytical edges (COMPETES_WITH, SIMILAR_TO, ECOSYSTEM_PEER, etc.) are the moat.

**Distribution thesis:** Launch as a free public tool to build brand, audience, and data network effects. Monetize later via premium tiers, API access, or sponsored placements — but the free experience must be genuinely valuable on its own.

---

## 2. Target Users & Jobs to Be Done

### User 1: Investors & VCs
| Job | Feature |
|-----|---------|
| "Find startups that match my thesis" | Smart filtered search + graph traversal |
| "Who else is investing in my space?" | Co-investor network explorer |
| "What's the competitive landscape for a deal I'm evaluating?" | COMPETES_WITH + SIMILAR_TO visualization |
| "Which markets are emerging before they're obvious?" | Industry trend heatmaps + LQ analysis |
| "Track companies I'm watching" | Watchlists with change alerts |

### User 2: Founders & Operators
| Job | Feature |
|-----|---------|
| "Who are my real competitors?" | Competition graph (same industry + city + funding stage) |
| "Which investors should I pitch?" | Investor-industry-stage matching |
| "What markets should I expand to?" | ECOSYSTEM_PEER city recommendations |
| "How does my startup compare to peers?" | Peer benchmarking (funding, team size, traction) |
| "Find co-founders or advisors in my space" | Founder network + SERIAL_FOUNDER_LINK |

### User 3: Ecosystem Builders (Govt, Accelerators, Media)
| Job | Feature |
|-----|---------|
| "How does our city's ecosystem rank?" | City benchmarking dashboard |
| "What should we specialize in?" | Location Quotient analysis |
| "Which investors are active in peer cities but not ours?" | Investor gap analysis |
| "Annual ecosystem report data" | Exportable charts + data downloads |

---

## 3. Core Feature Set

### 3.1 — Graph Explorer (Primary Interface)

The centerpiece. A visual, interactive knowledge graph where every entity is clickable, explorable, and connected.

**Search & Discovery**
- Universal search bar: type any startup, investor, city, industry, or founder name
- Autocomplete with entity type badges
- Advanced filters: funding stage, range, year founded, team size, region, industry
- Search results as ranked cards with key stats + "Explore in Graph" CTA

**Graph Visualization**
- Force-directed graph layout (D3.js or Sigma.js) centered on selected entity
- Node types visually distinct (color + shape + icon)
- Edge types labeled and color-coded
- Depth control: 1-hop, 2-hop, 3-hop neighborhood
- Click any node to re-center the graph
- Hover tooltips with entity summary
- Minimap for orientation in large graphs
- Graph export as PNG/SVG

**PathFinder**
- "How is X connected to Y?" — finds shortest path between any two entities
- Shows all relationship types along the path
- Multiple path discovery (not just shortest — show top 3-5 paths)
- Use case: "How is Revolut connected to General Catalyst?" → Revolut → Fintech → General Catalyst (via FOCUSES_ON) OR Revolut → London → General Catalyst (via ACTIVE_IN)

**Entity Detail Panels**
When you click any entity, a slide-out panel shows:

*Startup Panel:*
- Name, logo (scraped or placeholder), description, website link
- Key stats: Founded, Funding, Stage, Team Size, Industry
- Investors list (clickable)
- Founders list (clickable)
- Competitors (COMPETES_WITH) with similarity scores
- Similar startups (SIMILAR_TO) in other cities
- City ecosystem context

*Investor Panel:*
- Portfolio companies (with funding stages)
- Industry focus (FOCUSES_ON) — pie chart
- Geographic focus (ACTIVE_IN) — map
- Co-investors (co-investment network)
- Stage preference (INVESTS_AT_STAGE) — bar chart

*City Panel:*
- Startup count by industry — heatmap
- Specialization scores (Location Quotient)
- Top investors active in city
- Ecosystem peers (ECOSYSTEM_PEER)
- Funding distribution
- Founded year distribution (ecosystem maturity)

*Industry Panel:*
- Top startups by funding
- Geographic distribution
- Key investors
- Sub-taxonomy (PART_OF_CATEGORY)
- Trend: startups founded by year in this industry

### 3.2 — Dashboards & Analytics

**Global Overview Dashboard**
- World map with city nodes sized by startup count, colored by median funding
- Region comparison cards (the 6 regions with key metrics)
- Top 10 lists: most funded startups, most active investors, fastest-growing industries
- Time series: startups founded by year across regions
- Funding stage distribution (global)

**City Comparison Tool**
- Select 2-4 cities side by side
- Radar chart: industry diversity, median funding, investor density, ecosystem maturity
- Industry heatmap comparison
- Shared investors between selected cities
- ECOSYSTEM_PEER scores between them

**Industry Deep Dive**
- Select any of the 20 industry categories
- Geographic concentration map
- Funding distribution by stage
- Top players by funding
- Key investors in this space
- Sub-industry taxonomy tree

**Investor Intelligence**
- Investor leaderboard by portfolio size, total deployed, geographic spread
- Investor-industry matrix (heatmap)
- Co-investment network visualization (who invests together?)
- Stage preference analysis
- "Find investors like X" — similar investor discovery

### 3.3 — AI-Powered Insights

**Natural Language Query**
- Chat interface layered on top of the graph
- "Which fintech startups in Europe raised Series B in the last 2 years?"
- "Who are Revolut's biggest competitors by funding?"
- "What do Berlin and Tel Aviv's ecosystems have in common?"
- Translates natural language → Cypher → renders results as cards/charts/graph
- Powered by Claude API with Cypher generation prompt

**Smart Recommendations**
- For Startups: "Startups like yours" (SIMILAR_TO), "Investors who fund your type" (stage + industry match), "Markets to explore" (ECOSYSTEM_PEER cities)
- For Investors: "Deals matching your thesis" (FOCUSES_ON + stage), "Co-investment opportunities" (investors in your portfolio's competitors), "Emerging sectors" (fastest-growing industry categories)
- For Cities: "Your specialization gaps" (industries where LQ < 1 but peer cities have LQ > 1), "Investor gaps" (active in peers but not here)

**Ecosystem Reports (Auto-generated)**
- One-click PDF/Markdown report for any city
- Includes: industry breakdown, top startups, investor landscape, peer comparison, specialization analysis
- Updated dynamically from the graph
- Shareable URL for each report

### 3.4 — Portfolio & Watchlists

**Watchlists**
- Create named watchlists (e.g., "Series A Fintech Europe", "Berlin AI competitors")
- Add any entity: startups, investors, cities, industries
- Dashboard view of watchlist with aggregate stats
- Public/private watchlists (public ones become community content)

**Change Tracking & Alerts**
- When data refreshes (new scrape cycle), detect changes:
  - New startups added to a watched industry/city
  - Funding updates for watched startups
  - New investors entering a watched sector
  - Ecosystem rank changes for watched cities
- Email digest: daily or weekly summary of changes to watched entities
- In-app notification feed

**Comparison Mode**
- Select 2-5 startups from a watchlist to compare head-to-head
- Side-by-side cards with all key metrics
- Overlay on graph to see shared connections
- Export comparison as image or CSV

---

## 4. Information Architecture

```
StartupGraph.io
│
├── / (Landing Page + Global Dashboard)
│   ├── World map visualization
│   ├── Key stats banner
│   └── Trending / recently added
│
├── /explore (Graph Explorer)
│   ├── Search bar + filters
│   ├── Graph canvas
│   ├── Entity detail panel (slide-out)
│   └── PathFinder modal
│
├── /dashboards
│   ├── /dashboards/cities (City comparison)
│   ├── /dashboards/industries (Industry deep dive)
│   └── /dashboards/investors (Investor intelligence)
│
├── /ask (AI Query Interface)
│   ├── Chat-style query box
│   ├── Results as cards / charts / mini-graph
│   └── Query history
│
├── /startup/:slug (Startup profile page — SEO)
├── /investor/:slug (Investor profile page — SEO)
├── /city/:slug (City ecosystem page — SEO)
├── /industry/:slug (Industry overview page — SEO)
│
├── /watchlists
│   ├── My watchlists
│   ├── Public watchlists (community)
│   └── Alerts settings
│
├── /reports/:city (Auto-generated ecosystem reports)
│
└── /api (Public API documentation)
```

---

## 5. Technical Architecture

### 5.1 — System Overview

```
┌──────────────────────────────────────────────────────┐
│                     CDN (Cloudflare)                  │
└────────────┬─────────────────────┬───────────────────┘
             │                     │
┌────────────▼────────┐ ┌─────────▼──────────┐
│   React Frontend    │ │   Next.js SSR/SSG  │
│   (SPA — Explorer,  │ │   (SEO pages —     │
│    Dashboards, AI)  │ │    /startup/:slug  │
│                     │ │    /city/:slug)    │
└────────────┬────────┘ └─────────┬──────────┘
             │                     │
             └──────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │     API Gateway    │
              │   (FastAPI + Auth) │
              └─────────┬──────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
┌────────▼───┐ ┌───────▼───┐ ┌────────▼──────┐
│   Neo4j    │ │  Claude   │ │   Redis       │
│  (Graph)   │ │   API     │ │  (Cache +     │
│            │ │  (NL→Cypher)│ │   Sessions)  │
└────────────┘ └───────────┘ └───────────────┘
         │
┌────────▼───────────┐
│   PostgreSQL       │
│  (Users, Watchlists│
│   Alerts, Audit)   │
└────────────────────┘
```

### 5.2 — Stack Choices

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React + TypeScript + Tailwind | Already built; extend existing |
| **SSR/SEO** | Next.js (or Astro for static) | Profile pages need SEO; /startup/revolut must be indexable |
| **Graph Viz** | Sigma.js (WebGL) or react-force-graph | Handles 5K+ nodes; D3 falls over at scale |
| **Charts** | Recharts (existing) + D3 for custom | Recharts for standard; D3 for heatmaps/chord diagrams |
| **API** | FastAPI (existing) | Extend the 16 endpoints to ~40 |
| **Graph DB** | Neo4j 5 Community (existing) | Already modeled; extend with new query patterns |
| **Auth** | Clerk or NextAuth | Free tier available; social login |
| **User Data** | PostgreSQL (Supabase free tier) | Watchlists, alerts, user preferences |
| **Cache** | Redis (Upstash free tier) | Cache expensive graph queries (city comparisons, etc.) |
| **AI** | Claude API (Sonnet) | NL→Cypher translation + insight generation |
| **Search** | Meilisearch or Typesense | Fuzzy, fast autocomplete across 3K+ entities |
| **Hosting** | Railway or Fly.io | Neo4j + FastAPI + Next.js; free/cheap tiers |
| **CDN** | Cloudflare | Free tier; caching + DDoS |

### 5.3 — Data Pipeline (Refresh Cycle)

```
Weekly/Bi-weekly Cron
       │
       ▼
┌──────────────┐
│  Re-scrape   │  Run existing scrapers for new/updated data
│  3 Sources   │
└──────┬───────┘
       │
┌──────▼───────┐
│  Diff Engine │  Compare new scrape vs existing master
│              │  Detect: new startups, funding changes,
│              │          new investors, closed companies
└──────┬───────┘
       │
┌──────▼───────┐
│  Normalize   │  Run normalize_pipeline.py on new data
│  Pipeline    │
└──────┬───────┘
       │
┌──────▼───────┐
│  Graph       │  Incremental ingest (upsert, not rebuild)
│  Ingest      │  Recompute affected analytical edges
└──────┬───────┘
       │
┌──────▼───────┐
│  Alert       │  Compare watchlists vs changes
│  Engine      │  Queue notifications
└──────────────┘
```

---

## 6. SEO & Growth Strategy

### 6.1 — SEO Pages (The Organic Growth Engine)

This is critical for a free public tool. Every entity in the graph becomes a crawlable, indexable page:

- **3,022 startup pages:** `/startup/revolut`, `/startup/bytedance`, etc.
  - Title: "Revolut — Fintech Startup in London | StartupGraph"
  - Content: description, stats, investors, competitors, similar startups
  - Schema.org Organization markup

- **784 investor pages:** `/investor/general-catalyst`
  - Portfolio, industry focus, stage preference, co-investors

- **20 city ecosystem pages:** `/city/berlin`
  - Full ecosystem report, specializations, top startups, investors

- **20 industry pages:** `/industry/fintech`
  - Geographic distribution, top players, investor landscape

**Total: ~3,850 SEO-ready pages** — each targeting long-tail queries like "fintech startups Berlin," "General Catalyst portfolio," "AI startups Singapore."

### 6.2 — Content & Distribution

| Channel | Tactic |
|---------|--------|
| **SEO** | 3,850 entity pages + city ecosystem blog posts |
| **Twitter/X** | Weekly "Startup Graph of the Week" — interesting graph patterns |
| **LinkedIn** | Ecosystem reports for city/industry leaders |
| **ProductHunt** | Launch with graph explorer as hero feature |
| **Hacker News** | Open-source the data pipeline + graph schema |
| **Newsletter** | Weekly digest: new startups added, funding changes, ecosystem shifts |
| **Embeds** | Embeddable widgets for ecosystem reports (cities/accelerators embed on their sites) |

### 6.3 — Community Flywheel

- Users can submit corrections / additions (crowdsource data quality)
- Public watchlists become curated lists ("Best AI Startups in Europe")
- Referral: share your startup's profile page
- Data download (CSV) for academic/research use → attribution links back

---

## 7. Monetization (Future — After Audience)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Full explorer, 3 watchlists, 5 AI queries/day, all dashboards |
| **Pro** | $29/mo | Unlimited watchlists, 50 AI queries/day, export, API (1K calls/mo), alerts |
| **Team** | $99/mo | Shared watchlists, team alerts, API (10K calls/mo), custom reports |
| **API** | Usage-based | Direct graph access for programmatic users |
| **Sponsored** | Custom | Featured placements for accelerators, cities, service providers |

---

## 8. Phased Build Plan

### Phase 1: Foundation (Weeks 1-3)
**Goal:** Ship the MVP publicly with search, explore, and basic dashboards.

- [ ] Set up Next.js project with existing React components migrated
- [ ] Fulltext search — Meilisearch index across all entities
- [ ] Graph Explorer v2 — Sigma.js canvas with node/edge rendering, 1-2 hop navigation
- [ ] Entity pages (SSG) — static generation for all 3,850 entities (SEO-ready from day 1)
- [ ] Global dashboard — world map, region cards, key stats
- [ ] City comparison — select 2-4 cities, radar chart + shared investors
- [ ] Deploy — Neo4j + API + Frontend on Railway/Fly.io + Cloudflare CDN
- [ ] Analytics — Plausible or PostHog (privacy-friendly, free tier)

**Milestone:** Public URL, searchable, explorable, Google indexing started.

### Phase 2: Intelligence (Weeks 4-6)
**Goal:** Add AI layer and deeper analytics.

- [ ] NL→Cypher engine — Claude API with system prompt containing graph schema + example queries
- [ ] AI chat interface — `/ask` page with streaming responses
- [ ] Industry deep dive dashboard — geographic heatmap, funding distribution, taxonomy tree
- [ ] Investor intelligence — portfolio view, co-investment chord diagram, thesis analysis
- [ ] PathFinder v2 — multiple paths, relationship explanation
- [ ] Competition landscape — for any startup, show COMPETES_WITH graph with similarity scores

**Milestone:** "Ask anything" about the startup ecosystem; investor and industry dashboards live.

### Phase 3: Engagement (Weeks 7-9)
**Goal:** User accounts, watchlists, alerts — retention mechanics.

- [ ] Auth integration — Clerk/NextAuth, social login
- [ ] PostgreSQL setup — user profiles, watchlists, alert preferences
- [ ] Watchlist CRUD — create, add entities, dashboard view
- [ ] Change detection engine — diff new scrape vs previous, flag changes
- [ ] Alert system — email digests (daily/weekly) for watchlist changes
- [ ] Public watchlists — community-curated lists
- [ ] Comparison mode — select startups from watchlist, side-by-side view

**Milestone:** Users can sign up, build watchlists, get email alerts.

### Phase 4: Growth (Weeks 10-12)
**Goal:** SEO traction, community features, launch.

- [ ] Auto-generated ecosystem reports — one-click PDF for any city
- [ ] Embeddable widgets — iframe-able cards for cities/startups
- [ ] Data submission flow — "Add/correct a startup" form with moderation queue
- [ ] Newsletter — weekly digest of ecosystem changes
- [ ] ProductHunt launch prep — screenshots, video demo, launch copy
- [ ] Open-source data pipeline — publish normalize_pipeline.py + schema on GitHub
- [ ] Launch — ProductHunt, HN, Twitter, LinkedIn

**Milestone:** Public launch, 1K+ users in first month, SEO pages indexing.

### Phase 5: Scale (Months 4-6)
- [ ] More cities — expand from 20 to 50 (add Mumbai, Jakarta, Lagos, Dubai, Austin, Miami, etc.)
- [ ] More data sources — LinkedIn Company Pages, Crunchbase open data, AngelList
- [ ] Temporal graph — track how the ecosystem evolves over time
- [ ] Pro tier launch — paywall advanced features
- [ ] API launch — public REST API with rate limits

---

## 9. Key Technical Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Neo4j Community has no clustering | Single-node bottleneck | Redis cache for hot queries; read replicas later if needed |
| Graph viz performance at scale | Laggy with 5K+ nodes visible | Sigma.js (WebGL), pagination, limit visible nodes to 200 per view |
| NL→Cypher accuracy | Bad queries = wrong results | Schema-aware prompt + few-shot examples + fallback to canned queries |
| Data freshness | Stale data = no trust | Bi-weekly scrape cycle + "Last updated" badges on every entity |
| Scraper breakage | Source sites change layout | Generic scraper fallback + health checks + manual override |
| SEO competition | Crunchbase dominates SERPs | Long-tail focus ("fintech startups Berlin 2026"), unique content (graph insights) |
| Cold start (no users) | Empty watchlists, no community | Seed with curated public watchlists; ecosystem reports drive inbound |

---

## 10. Success Metrics

### Phase 1-2 (Month 1-2)
- 3,850 pages indexed by Google
- 1K unique visitors/week (organic + launch)
- Avg session duration > 3 min
- >50 graph explorations/day

### Phase 3-4 (Month 2-3)
- 500 registered users
- 200 watchlists created
- 50 AI queries/day
- 10 community watchlists with >5 followers

### Phase 5+ (Month 4-6)
- 5K registered users
- 50K monthly organic visits
- Featured in 3+ startup/VC newsletters
- First Pro tier conversions

---

## 11. What Makes This Different

| Feature | Crunchbase | PitchBook | StartupGraph |
|---------|-----------|-----------|-------------|
| **Price** | $4K/yr Pro | $15K+/yr | Free |
| **Graph-native** | No (flat tables) | No | Yes — every relationship is queryable |
| **Computed edges** | No | No | COMPETES_WITH, SIMILAR_TO, ECOSYSTEM_PEER, etc. |
| **Location Quotient** | No | No | Genuine specialization, not just count |
| **NL query** | No | Limited | Full Claude-powered NL→Cypher |
| **Open data** | Paywalled | Paywalled | Downloadable CSVs |
| **City ecosystem analysis** | Basic | Decent | Deep — peer comparison, investor gaps, LQ |
| **Real competition mapping** | Manual lists | Manual lists | Computed from graph structure |

---

## Appendix A: Extended API Endpoints

### Existing (16 endpoints) — keep all current endpoints

### New endpoints needed:

**Search & Discovery**
- `GET /search?q={query}&type={entity_type}&limit=20`
- `GET /autocomplete?q={prefix}&limit=10`

**Entity Profiles**
- `GET /startup/{slug}` — full startup profile with computed relationships
- `GET /investor/{slug}` — investor profile with portfolio + thesis
- `GET /city/{slug}` — city ecosystem profile
- `GET /industry/{slug}` — industry overview

**Graph Operations**
- `GET /graph/neighborhood/{node_id}?depth={1-3}`
- `GET /graph/path?from={id}&to={id}&max_depth=5`
- `GET /graph/similar/{startup_id}?limit=10`

**Analytics**
- `GET /analytics/city-comparison?cities=berlin,london,singapore`
- `GET /analytics/industry/{slug}/geographic`
- `GET /analytics/investor/{slug}/thesis`
- `GET /analytics/competition/{startup_id}`

**AI**
- `POST /ask` — { "question": "Which fintech..." } → structured results

**User Features**
- `POST /watchlists` — CRUD
- `GET /watchlists/{id}/changes`
- `POST /alerts/subscribe`

**Data Export**
- `GET /export/city/{slug}.csv`
- `GET /export/report/{slug}.pdf`

---

## Appendix B: NL→Cypher System Prompt (Sketch)

```
You are a Cypher query generator for a startup ecosystem knowledge graph.

## Graph Schema
Node types: Startup, Industry, IndustryCategory, City, Country, Region,
            Investor, Founder, FundingStage, FundingBracket, FoundedCohort

Key relationships:
- (Startup)-[:IN_INDUSTRY]->(Industry)
- (Startup)-[:LOCATED_IN]->(City)
- (Startup)-[:FUNDED_BY]->(Investor)
- (Startup)-[:COMPETES_WITH {score}]->(Startup)
- (Startup)-[:SIMILAR_TO {score}]->(Startup)
- (Investor)-[:FOCUSES_ON {startup_count}]->(IndustryCategory)
- (Investor)-[:ACTIVE_IN]->(City)
- (City)-[:SPECIALIZES_IN {location_quotient}]->(IndustryCategory)
- (City)-[:ECOSYSTEM_PEER {shared_investors}]->(City)

## Rules
1. Always use parameterized queries
2. Limit results to 25 unless specified
3. Return node properties, not raw nodes
4. For ambiguous entity names, use fuzzy matching
5. Always ORDER BY a meaningful metric (funding, count, score)
```

---

## Appendix C: Future Graph Schema Extensions

New node types:
- `User` — registered users (stored in PostgreSQL, linked by ID)
- `Watchlist` — user-created entity collections

New relationships:
- `(User)-[:WATCHES]->(Startup|Investor|City|Industry)`
- `(Startup)-[:UPDATED_ON {date, field, old_value, new_value}]->(ChangeLog)`

New computed edges (Phase 5):
- `TRENDING_IN` — startups with fastest funding growth in a city
- `EMERGING_CATEGORY` — industry categories with accelerating startup creation
- `INVESTOR_BRIDGE` — investors who uniquely connect two otherwise disconnected ecosystems
