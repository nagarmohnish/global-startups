"""
Global Startups Data Normalization Pipeline
Cleans, normalizes, and restructures 3,141 startups across 20 cities
into analysis-ready outputs.
"""
import json, os, re, sys, warnings
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
from thefuzz import fuzz

warnings.filterwarnings("ignore", category=UserWarning)
sys.stdout.reconfigure(encoding="utf-8")

INPUT_FILE = "global_startups_final.xlsx"
OUTPUT_DIR = "structured_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Logging
LOG_LINES = []

def log(msg):
    LOG_LINES.append(msg)
    print(msg)

def save_log():
    with open(os.path.join(OUTPUT_DIR, "cleaning_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG_LINES))

# ============================================================
# CITY / REGION / COUNTRY MAPPINGS
# ============================================================

CITY_TO_COUNTRY = {
    "Tel Aviv": "Israel", "Beijing": "China", "Seoul": "South Korea",
    "Singapore": "Singapore", "Shanghai": "China", "Tokyo": "Japan",
    "Paris": "France", "Zurich": "Switzerland", "Berlin": "Germany",
    "Sao Paulo": "Brazil", "Madrid": "Spain", "Silicon Valley": "United States",
    "Shenzhen": "China", "NYC": "United States", "London": "United Kingdom",
    "Boston": "United States", "Los Angeles": "United States",
    "Hangzhou": "China", "Stockholm": "Sweden", "Guangzhou": "China",
}

CITY_TO_REGION = {
    "Silicon Valley": "North America", "NYC": "North America",
    "Boston": "North America", "Los Angeles": "North America",
    "London": "Europe", "Berlin": "Europe", "Paris": "Europe",
    "Zurich": "Europe", "Stockholm": "Europe", "Madrid": "Europe",
    "Beijing": "East Asia", "Shanghai": "East Asia", "Shenzhen": "East Asia",
    "Hangzhou": "East Asia", "Guangzhou": "East Asia", "Tokyo": "East Asia",
    "Seoul": "East Asia",
    "Singapore": "Southeast Asia",
    "Sao Paulo": "Latin America",
    "Tel Aviv": "Middle East",
}

# ============================================================
# CURRENCY CONVERSION RATES (to USD)
# ============================================================

CURRENCY_RATES = {
    "$": 1.0, "US$": 1.0, "USD": 1.0,
    "€": 1.08, "EUR": 1.08,
    "£": 1.27, "GBP": 1.27,
    "CN¥": 0.14, "CNY": 0.14, "CN\uFFFD": 0.14, "¥": 0.14,
    "R$": 0.18, "BRL": 0.18,
    "SEK": 0.095, "CHF": 1.12, "SGD": 0.75,
    "A$": 0.65, "AUD": 0.65, "MYR": 0.22,
    "₩": 0.00074, "KRW": 0.00074,
    "₹": 0.012, "INR": 0.012,
    "JPY": 0.0067, "JP¥": 0.0067,
}

# ============================================================
# INDUSTRY TAXONOMY
# ============================================================

INDUSTRY_TAXONOMY = {
    "AI/ML": [
        "artificial intelligence", "machine learning", "nlp", "natural language",
        "computer vision", "deep learning", "generative ai", "llm", "large language",
        "neural network", "ai", "ml", "chatbot", "conversational ai", "speech recognition",
        "image recognition", "predictive analytics", "data science", "ai avatar",
        "ai email", "ai image", "ai text", "ai video", "aiot", "aiops",
        "recommendation engine", "autonomous systems",
    ],
    "Fintech": [
        "fintech", "banking", "payments", "payment", "cryptocurrency", "blockchain",
        "defi", "insurtech", "neobank", "lending", "credit", "financial services",
        "financial technology", "crypto", "web3", "nft", "digital banking",
        "wealth management", "trading", "investment management", "regtech",
        "accounting", "billing", "invoicing", "payroll", "expense management",
        "anti-money laundering", "compliance", "digital wallet", "remittance",
        "crowdfunding", "equity crowdfunding", "peer-to-peer lending",
        "stock trading", "asset management", "venture capital",
        "initial coin offering", "token", "decentralized",
    ],
    "Healthcare/Biotech": [
        "healthcare", "biotech", "pharma", "pharmaceutical", "drug discovery",
        "medtech", "clinical trials", "genomics", "digital health", "telemedicine",
        "medical device", "diagnostics", "life sciences", "biomedical",
        "mental health", "health tech", "healthtech", "hospital", "patient",
        "therapy", "therapeutics", "oncology", "alzheimer", "gene therapy",
        "protein", "antibody", "vaccine", "bioinformatics", "health insurance",
        "dental", "veterinary", "elder care", "assisted living", "fertility",
        "clinical decision", "medical imaging", "pathology", "radiology",
        "electronic health record", "ehr", "nursing", "rehabilitation",
        "wearable health", "remote patient", "telehealth",
    ],
    "SaaS/Software": [
        "saas", "software", "cloud", "platform", "developer tools", "devops",
        "paas", "iaas", "low-code", "no-code", "api", "middleware",
        "enterprise software", "project management", "collaboration",
        "productivity", "crm", "erp", "database", "data management",
        "business intelligence", "analytics platform", "workflow",
        "application software", "it services", "information technology",
        "cloud computing", "infrastructure", "data integration",
        "open source", "version control", "testing", "qa", "monitoring",
    ],
    "E-Commerce/Retail": [
        "e-commerce", "ecommerce", "retail", "marketplace", "d2c",
        "consumer", "online shopping", "fashion", "beauty", "cosmetics",
        "luxury", "consumer goods", "grocery", "delivery", "quick commerce",
        "social commerce", "live shopping", "subscription box",
    ],
    "Cybersecurity": [
        "cybersecurity", "cyber security", "security", "identity",
        "privacy", "encryption", "firewall", "threat detection",
        "access control", "authentication", "zero trust",
        "penetration testing", "vulnerability", "fraud detection",
        "data protection", "endpoint security", "network security",
    ],
    "Robotics/Hardware": [
        "robotics", "hardware", "drones", "iot", "internet of things",
        "semiconductors", "3d printing", "wearables", "sensor",
        "embedded systems", "electronics", "chip", "integrated circuit",
        "manufacturing equipment", "industrial automation", "cobot",
        "lidar", "radar", "optics", "photonics",
    ],
    "EV/Mobility": [
        "electric vehicle", "ev", "mobility", "autonomous vehicle",
        "transportation", "logistics", "fleet management", "ride-sharing",
        "ride-hailing", "scooter", "bicycle", "micromobility",
        "autonomous driving", "self-driving", "connected car",
        "vehicle", "automotive", "car sharing", "last mile",
        "shipping", "freight", "supply chain", "warehouse",
        "trucking", "courier",
    ],
    "CleanTech/Energy": [
        "clean energy", "climate", "sustainability", "solar",
        "battery", "carbon", "renewable", "wind energy", "hydrogen",
        "energy storage", "cleantech", "green", "environmental",
        "recycling", "waste management", "water treatment", "circular economy",
        "carbon capture", "nuclear", "smart grid", "energy efficiency",
        "electric power", "geothermal",
    ],
    "EdTech": [
        "education", "edtech", "e-learning", "elearning", "online learning",
        "tutoring", "language learning", "skill development", "mooc",
        "corporate training", "lms", "learning management",
    ],
    "Media/Entertainment": [
        "media", "gaming", "content", "streaming", "social",
        "advertising", "adtech", "video", "music", "podcast",
        "entertainment", "digital media", "publishing", "news",
        "animation", "ar/vr", "virtual reality", "augmented reality",
        "metaverse", "esports", "creator economy", "influencer",
        "marketing", "social media", "social network",
    ],
    "Real Estate/PropTech": [
        "real estate", "proptech", "construction", "property",
        "mortgage", "contech", "building", "smart building",
        "architecture", "facility management", "co-working", "coworking",
        "apartment", "housing",
    ],
    "FoodTech/AgTech": [
        "food", "agriculture", "foodtech", "agtech", "agritech",
        "farming", "crop", "aquaculture", "alternative protein",
        "plant-based", "cell-based", "vertical farming", "precision agriculture",
        "restaurant", "meal", "kitchen", "beverage", "nutrition",
        "food delivery", "ghost kitchen", "seafood",
    ],
    "SpaceTech": [
        "space", "satellite", "aerospace", "rocket", "launch vehicle",
        "earth observation", "orbital",
    ],
    "Defense": [
        "defense", "defence", "military", "weapons", "ballistic",
        "naval", "army",
    ],
    "Telecom": [
        "telecom", "5g", "connectivity", "wireless", "broadband",
        "network infrastructure", "fiber optic",
    ],
    "HR/Workforce": [
        "hr", "human resources", "recruitment", "workforce", "hiring",
        "talent", "staffing", "job", "employee engagement", "people analytics",
        "benefits", "compensation", "applicant tracking",
    ],
    "Legal": [
        "legaltech", "legal", "law", "compliance", "contract management",
        "regulatory",
    ],
    "Insurance": [
        "insurance", "insurtech", "underwriting", "claims",
    ],
}

# Precompile lowercase keyword lists
_TAXONOMY_COMPILED = {
    cat: [kw.lower() for kw in keywords]
    for cat, keywords in INDUSTRY_TAXONOMY.items()
}

# ============================================================
# FUNDING ROUND NORMALIZATION
# ============================================================

ROUND_MAP = {
    "pre-seed": "Pre-Seed", "pre seed": "Pre-Seed",
    "seed": "Seed", "angel": "Seed",
    "series a": "Series A", "series b": "Series B",
    "series c": "Series C", "series d": "Series D",
    "series e": "Series E+", "series f": "Series E+",
    "series g": "Series E+", "series h": "Series E+",
    "series i": "Series E+",
    "venture round": "Venture Round", "venture": "Venture Round",
    "growth equity": "Growth Equity", "growth": "Growth Equity",
    "private equity": "Private Equity",
    "debt financing": "Debt Financing", "debt": "Debt Financing",
    "convertible note": "Convertible Note", "convertible": "Convertible Note",
    "bridge": "Bridge Round",
    "ipo": "IPO",
    "secondary market": "Secondary Market",
    "corporate round": "Corporate Round",
    "initial coin offering": "ICO",
    "grant": "Grant",
    "product crowdfunding": "Crowdfunding",
    "equity crowdfunding": "Crowdfunding",
    "undisclosed": "Undisclosed",
}


# ============================================================
# STAGE 1: Combine & Add Metadata
# ============================================================

def stage1_combine():
    log("\n" + "=" * 60)
    log("STAGE 1: Combine & Add Metadata")
    log("=" * 60)

    xls = pd.ExcelFile(INPUT_FILE)
    frames = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet)
        df["City"] = sheet
        df["Country"] = CITY_TO_COUNTRY.get(sheet, "Unknown")
        df["Region"] = CITY_TO_REGION.get(sheet, "Unknown")
        frames.append(df)
        log(f"  {sheet}: {len(df)} rows")

    combined = pd.concat(frames, ignore_index=True)
    combined["startup_id"] = [f"S{i+1:04d}" for i in range(len(combined))]

    log(f"\n  Total combined: {len(combined)} rows")
    log(f"  Columns: {list(combined.columns)}")

    # Sample
    log("\n  Sample (first 3):")
    for _, r in combined.head(3).iterrows():
        log(f"    {r['startup_id']} | {r['Name']} | {r['City']} | {r['Country']} | {r['Region']}")

    return combined


# ============================================================
# STAGE 2: Deduplication
# ============================================================

def _normalize_name(name):
    """Normalize company name for dedup matching."""
    if pd.isna(name):
        return ""
    n = str(name).lower().strip()
    # Remove parenthetical suffixes
    n = re.sub(r"\s*\(.*?\)", "", n)
    # Remove common suffixes
    n = re.sub(
        r"\s*(ltd\.?|inc\.?|co\.?|corp\.?|pte\.?|ag|gmbh|sa|sas|sl|llc|ab|"
        r"corporation|technologies|technology|tech|security|ai|limited|group|"
        r"holding[s]?|company|co\.,?\s*ltd\.?)\s*\.?$",
        "", n, flags=re.IGNORECASE,
    )
    return re.sub(r"[^a-z0-9]", "", n)


def _normalize_domain(url):
    """Extract clean domain from URL."""
    if pd.isna(url) or not url or url == "N/A":
        return ""
    try:
        from urllib.parse import urlparse
        domain = urlparse(str(url)).netloc.lower().replace("www.", "")
        return domain.split(":")[0]  # Remove port
    except Exception:
        return ""


def stage2_dedup(df):
    log("\n" + "=" * 60)
    log("STAGE 2: Deduplication")
    log("=" * 60)

    df["_norm_name"] = df["Name"].apply(_normalize_name)
    df["_domain"] = df["Website"].apply(_normalize_domain)

    # Count non-null fields for each row (to pick the richest record)
    info_cols = ["Website", "Industry", "Description", "Founded", "Funding",
                 "Revenue", "Last Round", "Founders", "Top Investors", "Team Size"]
    df["_completeness"] = df[info_cols].notna().sum(axis=1)
    # Also penalize N/A values
    for col in info_cols:
        df["_completeness"] -= (df[col] == "N/A").astype(int)

    # Group by normalized name
    groups = defaultdict(list)
    for idx, row in df.iterrows():
        key = row["_norm_name"]
        if key:
            groups[key].append(idx)

    # Also check domain-based matches for entries with different names
    domain_groups = defaultdict(list)
    for idx, row in df.iterrows():
        d = row["_domain"]
        if d and d not in ("", "n/a"):
            domain_groups[d].append(idx)

    # Merge domain groups into name groups
    for domain, indices in domain_groups.items():
        if len(indices) > 1:
            # Find all unique name groups these belong to
            name_keys = set()
            for idx in indices:
                nk = df.loc[idx, "_norm_name"]
                if nk:
                    name_keys.add(nk)
            if len(name_keys) > 1:
                # Merge into the first group
                master_key = min(name_keys)
                for nk in name_keys:
                    if nk != master_key:
                        groups[master_key].extend(groups.pop(nk, []))

    # Deduplicate
    keep_indices = []
    city_mapping = []  # (startup_id, city)
    dupes_removed = 0

    for key, indices in groups.items():
        unique_indices = list(set(indices))
        if len(unique_indices) == 1:
            keep_indices.append(unique_indices[0])
            continue

        # Pick the row with highest completeness
        best_idx = max(unique_indices, key=lambda i: df.loc[i, "_completeness"])
        keep_indices.append(best_idx)

        # Merge data from other rows into the best row
        for idx in unique_indices:
            if idx == best_idx:
                continue
            for col in info_cols:
                best_val = df.loc[best_idx, col]
                other_val = df.loc[idx, col]
                if (pd.isna(best_val) or best_val == "N/A" or best_val == "") and \
                   (not pd.isna(other_val) and other_val != "N/A" and other_val != ""):
                    df.loc[best_idx, col] = other_val

        # Record all cities
        cities = list(set(df.loc[i, "City"] for i in unique_indices))
        if len(cities) > 1:
            sid = df.loc[best_idx, "startup_id"]
            for c in cities:
                city_mapping.append({"startup_id": sid, "city": c})

        dupes_removed += len(unique_indices) - 1

        if dupes_removed <= 20 and len(unique_indices) > 1:
            names = [str(df.loc[i, "Name"]) for i in unique_indices]
            cities_str = [str(df.loc[i, "City"]) for i in unique_indices]
            log(f"  Dedup: {names} in {cities_str} → kept {df.loc[best_idx, 'Name']}")

    # Also add entries with no normalized name
    for idx, row in df.iterrows():
        if not row["_norm_name"] and idx not in keep_indices:
            keep_indices.append(idx)

    keep_indices = sorted(set(keep_indices))
    deduped = df.loc[keep_indices].copy().reset_index(drop=True)

    # Reassign startup_ids
    deduped["startup_id"] = [f"S{i+1:04d}" for i in range(len(deduped))]

    # Update city mapping with new IDs
    old_to_new = {df.loc[keep_indices[i], "startup_id"]: f"S{i+1:04d}" for i in range(len(keep_indices)) if i < len(keep_indices)}

    city_df = pd.DataFrame(city_mapping)
    if not city_df.empty:
        city_df["startup_id"] = city_df["startup_id"].map(
            lambda x: old_to_new.get(x, x)
        )

    # Cleanup temp columns
    deduped.drop(columns=["_norm_name", "_domain", "_completeness"], inplace=True)

    log(f"\n  Duplicates found and removed: {dupes_removed}")
    log(f"  Rows after dedup: {len(deduped)}")
    log(f"  Multi-city startups: {len(city_df['startup_id'].unique()) if not city_df.empty else 0}")

    return deduped, city_df


# ============================================================
# STAGE 3: Normalize Funding & Revenue
# ============================================================

def _parse_money(val):
    """Parse a money string like '$34M', 'CN¥1.5B', 'R$20m' into (amount_usd, raw)."""
    if pd.isna(val):
        return np.nan, ""
    raw = str(val).strip()
    if not raw or raw in ("N/A", "n/a", "—", "–", "-", "nan", "NaN", ""):
        return np.nan, raw

    s = raw

    # Try to find currency symbol/code at the start
    rate = 1.0
    matched_currency = False
    for symbol, r in sorted(CURRENCY_RATES.items(), key=lambda x: -len(x[0])):
        if s.startswith(symbol):
            rate = r
            s = s[len(symbol):]
            matched_currency = True
            break

    # Handle mojibake for CN¥ (shows as CN\uFFFD)
    if not matched_currency:
        if s.startswith("CN"):
            rate = 0.14
            s = re.sub(r"^CN.?", "", s)
            matched_currency = True
        # Check for other mojibake currency symbols
        elif re.match(r"^[^\d\s.,]", s):
            # Unknown currency prefix, try to skip it
            m = re.match(r"^([^\d\s.,]+)", s)
            if m:
                prefix = m.group(1)
                for symbol, r in CURRENCY_RATES.items():
                    if symbol in prefix:
                        rate = r
                        break
                s = s[len(prefix):]

    s = s.strip()

    # Extract number and multiplier
    m = re.match(r"^([\d,.]+)\s*([bBmMkKtT](?:illion|illion)?)?", s)
    if not m:
        return np.nan, raw

    try:
        num = float(m.group(1).replace(",", ""))
    except ValueError:
        return np.nan, raw

    suffix = (m.group(2) or "").lower()
    if suffix.startswith("b"):
        num *= 1_000_000_000
    elif suffix.startswith("m"):
        num *= 1_000_000
    elif suffix.startswith("k") or suffix.startswith("t"):
        num *= 1_000

    usd = num * rate

    # Sanity check: reject absurdly large values for startups
    if usd > 500_000_000_000:  # > $500B
        return np.nan, raw

    return usd, raw


def stage3_funding_revenue(df):
    log("\n" + "=" * 60)
    log("STAGE 3: Normalize Funding & Revenue")
    log("=" * 60)

    funding_results = df["Funding"].apply(_parse_money)
    df["funding_usd"] = funding_results.apply(lambda x: x[0])
    df["funding_raw"] = funding_results.apply(lambda x: x[1])

    revenue_results = df["Revenue"].apply(_parse_money)
    df["revenue_usd"] = revenue_results.apply(lambda x: x[0])
    df["revenue_raw"] = revenue_results.apply(lambda x: x[1])

    # Log unparseable values
    unparseable_funding = df[df["funding_usd"].isna() & df["funding_raw"].ne("") & df["funding_raw"].ne("N/A")]
    unparseable_revenue = df[df["revenue_usd"].isna() & df["revenue_raw"].ne("") & df["revenue_raw"].ne("N/A")]

    if len(unparseable_funding) > 0:
        log(f"\n  Unparseable funding values ({len(unparseable_funding)}):")
        for _, r in unparseable_funding.head(10).iterrows():
            log(f"    {r['Name']}: {repr(r['funding_raw'])}")

    if len(unparseable_revenue) > 0:
        log(f"\n  Unparseable revenue values ({len(unparseable_revenue)}):")
        for _, r in unparseable_revenue.head(10).iterrows():
            log(f"    {r['Name']}: {repr(r['revenue_raw'])}")

    # Stats
    log(f"\n  Funding: {df['funding_usd'].notna().sum()}/{len(df)} parsed ({df['funding_usd'].notna().mean()*100:.1f}%)")
    log(f"  Revenue: {df['revenue_usd'].notna().sum()}/{len(df)} parsed ({df['revenue_usd'].notna().mean()*100:.1f}%)")

    # Sample
    log("\n  Sample conversions:")
    sample = df[df["funding_usd"].notna()].head(5)
    for _, r in sample.iterrows():
        log(f"    {r['Name']}: {r['funding_raw']} → ${r['funding_usd']:,.0f}")

    return df


# ============================================================
# STAGE 4: Normalize Founded Year
# ============================================================

def stage4_founded(df):
    log("\n" + "=" * 60)
    log("STAGE 4: Normalize Founded Year")
    log("=" * 60)

    def parse_year(val):
        if pd.isna(val):
            return np.nan
        try:
            y = int(float(val))
            return y
        except (ValueError, TypeError):
            return np.nan

    df["founded_year"] = df["Founded"].apply(parse_year)

    # Flag suspicious years
    suspicious = df[
        df["founded_year"].notna() &
        ((df["founded_year"] < 1990) | (df["founded_year"] > 2026))
    ]
    if len(suspicious) > 0:
        log(f"\n  Suspicious founded years ({len(suspicious)}):")
        for _, r in suspicious.iterrows():
            log(f"    {r['Name']}: {int(r['founded_year'])}")
            # Set to NaN if clearly wrong
            if r["founded_year"] < 1900 or r["founded_year"] > 2027:
                df.loc[_, "founded_year"] = np.nan

    valid = df["founded_year"].notna().sum()
    log(f"\n  Founded year: {valid}/{len(df)} parsed ({valid/len(df)*100:.1f}%)")
    log(f"  Range: {int(df['founded_year'].min())}-{int(df['founded_year'].max())}")

    return df


# ============================================================
# STAGE 5: Standardize Team Size
# ============================================================

def stage5_team_size(df):
    log("\n" + "=" * 60)
    log("STAGE 5: Standardize Team Size")
    log("=" * 60)

    # Named bucket patterns
    bucket_patterns = {
        r"founding\s*team\s*\(?\s*1\s*[-–]\s*10\s*\)?": (1, 10),
        r"lean\s*team\s*\(?\s*11\s*[-–]\s*50\s*\)?": (11, 50),
        r"mid[-\s]*size\s*team\s*\(?\s*51\s*[-–]\s*250\s*\)?": (51, 250),
        r"large\s*team\s*\(?\s*251\s*[-–]\s*1[,.]?000\s*\)?": (251, 1000),
        r"major\s*org\w*\s*\(?\s*1[,.]?001\s*[-–]\s*5[,.]?000\s*\)?": (1001, 5000),
    }

    def categorize(mn, mx):
        avg = (mn + mx) / 2
        if avg <= 10: return "1-10"
        if avg <= 50: return "11-50"
        if avg <= 250: return "51-250"
        if avg <= 1000: return "251-1000"
        if avg <= 5000: return "1001-5000"
        return "5000+"

    def parse_team(val):
        if pd.isna(val) or str(val).strip() in ("N/A", "nan", "", "—", "-"):
            return np.nan, np.nan, "", str(val) if not pd.isna(val) else ""

        s = str(val).strip()
        raw = s

        # Check named buckets
        for pattern, (lo, hi) in bucket_patterns.items():
            if re.search(pattern, s, re.IGNORECASE):
                return lo, hi, categorize(lo, hi), raw

        # Range pattern: "10-50 employees"
        m = re.search(r"(\d{1,6})\s*[-–]\s*(\d{1,6})", s)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            return lo, hi, categorize(lo, hi), raw

        # Single number: "38 employees", "500+", etc.
        m = re.search(r"(\d{1,6})\s*\+?\s*(?:employees?|people|staff|team)?", s, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            if n == 0:
                return np.nan, np.nan, "", raw
            # Use as both min and max (point estimate)
            return n, n, categorize(n, n), raw

        return np.nan, np.nan, "", raw

    results = df["Team Size"].apply(parse_team)
    df["team_size_min"] = results.apply(lambda x: x[0])
    df["team_size_max"] = results.apply(lambda x: x[1])
    df["team_size_category"] = results.apply(lambda x: x[2])
    df["team_size_raw"] = results.apply(lambda x: x[3])

    valid = df["team_size_min"].notna().sum()
    log(f"\n  Team size: {valid}/{len(df)} parsed ({valid/len(df)*100:.1f}%)")

    # Distribution
    cat_counts = df["team_size_category"].value_counts()
    log("\n  Category distribution:")
    for cat, count in cat_counts.items():
        if cat:
            log(f"    {cat}: {count}")

    return df


# ============================================================
# STAGE 6: Standardize Industry Taxonomy
# ============================================================

def _classify_industry(raw_industry):
    """Map a raw industry string to canonical categories."""
    if pd.isna(raw_industry) or str(raw_industry).strip() in ("N/A", "", "nan"):
        return "Other", ["Other"], str(raw_industry) if not pd.isna(raw_industry) else ""

    raw = str(raw_industry).strip()
    # Split by comma
    tags = [t.strip() for t in raw.split(",") if t.strip()]

    matched = []
    for tag in tags:
        tag_lower = tag.lower().strip()
        best_cat = None
        best_score = 0

        for category, keywords in _TAXONOMY_COMPILED.items():
            for kw in keywords:
                score = 0
                if kw == tag_lower:
                    # Exact match — highest priority
                    score = len(kw) * 10
                elif kw in tag_lower:
                    # Keyword is substring of tag — check word boundary
                    # Use regex to ensure word boundary match
                    if re.search(r'\b' + re.escape(kw) + r'\b', tag_lower):
                        score = len(kw) * 5
                    elif len(kw) >= 4:
                        # Allow partial for longer keywords (e.g., "fintech" in "insurfintech")
                        score = len(kw) * 2
                elif tag_lower in kw and len(tag_lower) >= 3:
                    # Tag is substring of keyword — only if tag is a meaningful word
                    # and the keyword is closely related (not "ai" in "training")
                    if re.search(r'\b' + re.escape(tag_lower) + r'\b', kw):
                        score = len(tag_lower) * 3

                if score > best_score:
                    best_score = score
                    best_cat = category

        if best_cat and best_cat not in matched:
            matched.append(best_cat)

    if not matched:
        matched = ["Other"]

    primary = matched[0]
    return primary, matched, raw


def stage6_industry(df):
    log("\n" + "=" * 60)
    log("STAGE 6: Standardize Industry Taxonomy")
    log("=" * 60)

    results = df["Industry"].apply(_classify_industry)
    df["primary_industry"] = results.apply(lambda x: x[0])
    df["industry_tags"] = results.apply(lambda x: x[1])
    df["industry_raw"] = results.apply(lambda x: x[2])

    # Build taxonomy mapping table
    tag_to_cat = {}
    for _, row in df.iterrows():
        raw = row["industry_raw"]
        if raw and raw != "N/A":
            tags = [t.strip() for t in raw.split(",")]
            for tag in tags:
                if tag and tag not in tag_to_cat:
                    result = _classify_industry(tag)
                    tag_to_cat[tag] = result[0]

    taxonomy_df = pd.DataFrame([
        {"raw_tag": tag, "canonical_category": cat}
        for tag, cat in sorted(tag_to_cat.items())
    ])

    # Stats
    log(f"\n  Unique raw tags: {len(tag_to_cat)}")
    log(f"  Mapped to 'Other': {sum(1 for v in tag_to_cat.values() if v == 'Other')}")

    cat_counts = df["primary_industry"].value_counts()
    log("\n  Primary industry distribution:")
    for cat, count in cat_counts.items():
        log(f"    {cat}: {count}")

    return df, taxonomy_df


# ============================================================
# STAGE 7: Standardize Funding Round
# ============================================================

def stage7_funding_round(df):
    log("\n" + "=" * 60)
    log("STAGE 7: Standardize Funding Round")
    log("=" * 60)

    def normalize_round(val):
        if pd.isna(val) or str(val).strip() in ("N/A", "nan", "", "—", "–", "-", "\uFFFD"):
            return "", str(val) if not pd.isna(val) else ""
        raw = str(val).strip()
        key = raw.lower().strip()

        # Direct lookup
        if key in ROUND_MAP:
            return ROUND_MAP[key], raw

        # Partial match
        for pattern, stage in ROUND_MAP.items():
            if pattern in key:
                return stage, raw

        log(f"    Unknown round: {repr(raw)}")
        return "Other", raw

    results = df["Last Round"].apply(normalize_round)
    df["funding_stage"] = results.apply(lambda x: x[0])
    df["last_round_raw"] = results.apply(lambda x: x[1])

    valid = df[df["funding_stage"].ne("")]["funding_stage"].value_counts()
    log("\n  Funding stage distribution:")
    for stage, count in valid.items():
        log(f"    {stage}: {count}")

    return df


# ============================================================
# STAGE 8: Parse Founders & Investors
# ============================================================

def _split_people(val):
    """Split a comma/and separated string of names."""
    if pd.isna(val) or str(val).strip() in ("N/A", "nan", "", "—", "–", "-"):
        return []
    s = str(val).strip()
    # Split by comma, semicolon, or " and "
    parts = re.split(r"[,;]|\band\b", s)
    names = []
    for p in parts:
        p = p.strip()
        if p and p not in ("NaN", "nan", "N/A", "—", "-") and len(p) > 1:
            names.append(p)
    return names


def stage8_founders_investors(df):
    log("\n" + "=" * 60)
    log("STAGE 8: Parse Founders & Investors")
    log("=" * 60)

    # --- FOUNDERS ---
    founder_rows = []
    founder_names = {}  # normalized_name → canonical_name
    founder_id_counter = 0

    for _, row in df.iterrows():
        names = _split_people(row.get("Founders"))
        for name in names:
            norm = name.lower().strip()
            if norm not in founder_names:
                founder_id_counter += 1
                founder_names[norm] = {
                    "founder_id": f"F{founder_id_counter:04d}",
                    "founder_name": name,
                }
            founder_rows.append({
                "founder_id": founder_names[norm]["founder_id"],
                "founder_name": founder_names[norm]["founder_name"],
                "startup_id": row["startup_id"],
                "startup_name": row["Name"],
                "city": row["City"],
            })

    founders_df = pd.DataFrame(founder_rows) if founder_rows else pd.DataFrame(
        columns=["founder_id", "founder_name", "startup_id", "startup_name", "city"]
    )

    # --- INVESTORS ---
    investor_rows = []
    investor_names = {}  # normalized → canonical
    investor_id_counter = 0

    # Helper to deduplicate investor names (keep longer version)
    def get_investor_canonical(name):
        nonlocal investor_id_counter
        norm = name.lower().strip()

        # Check for existing match (fuzzy)
        for existing_norm, info in investor_names.items():
            if norm == existing_norm:
                return info
            # Check if one is a substring of the other
            if norm in existing_norm or existing_norm in norm:
                # Keep the longer one
                if len(name) > len(info["investor_name"]):
                    info["investor_name"] = name
                return info
            # Fuzzy match for close names
            if fuzz.ratio(norm, existing_norm) > 85:
                if len(name) > len(info["investor_name"]):
                    info["investor_name"] = name
                return info

        investor_id_counter += 1
        info = {
            "investor_id": f"I{investor_id_counter:04d}",
            "investor_name": name,
        }
        investor_names[norm] = info
        return info

    for _, row in df.iterrows():
        names = _split_people(row.get("Top Investors"))
        for name in names:
            info = get_investor_canonical(name)
            investor_rows.append({
                "investor_id": info["investor_id"],
                "investor_name": info["investor_name"],
                "startup_id": row["startup_id"],
                "startup_name": row["Name"],
                "city": row["City"],
                "funding_stage": row.get("funding_stage", ""),
            })

    investors_df = pd.DataFrame(investor_rows) if investor_rows else pd.DataFrame(
        columns=["investor_id", "investor_name", "startup_id", "startup_name", "city", "funding_stage"]
    )

    # --- CO-INVESTMENT EDGES ---
    co_invest_rows = []
    # Group investors by startup
    startup_investors = defaultdict(list)
    for _, row in investors_df.iterrows():
        startup_investors[row["startup_id"]].append(
            (row["investor_name"], row["city"])
        )

    for sid, invs in startup_investors.items():
        if len(invs) >= 2:
            inv_names = list(set(i[0] for i in invs))
            city = invs[0][1]
            for a, b in combinations(sorted(inv_names), 2):
                co_invest_rows.append({
                    "investor_a": a,
                    "investor_b": b,
                    "startup_id": sid,
                    "city": city,
                })

    co_invest_df = pd.DataFrame(co_invest_rows) if co_invest_rows else pd.DataFrame(
        columns=["investor_a", "investor_b", "startup_id", "city"]
    )

    log(f"\n  Unique founders: {len(founder_names)}")
    log(f"  Founder-startup links: {len(founders_df)}")
    log(f"  Unique investors: {len(investor_names)}")
    log(f"  Investor-startup links: {len(investors_df)}")
    log(f"  Co-investment edges: {len(co_invest_df)}")

    # Add pipe-separated lists to main df
    founder_map = founders_df.groupby("startup_id")["founder_name"].apply(lambda x: " | ".join(x)).to_dict()
    investor_map = investors_df.groupby("startup_id")["investor_name"].apply(lambda x: " | ".join(x)).to_dict()
    df["founders_list"] = df["startup_id"].map(founder_map).fillna("")
    df["investors_list"] = df["startup_id"].map(investor_map).fillna("")

    return df, founders_df, investors_df, co_invest_df


# ============================================================
# STAGE 9: Output Files
# ============================================================

def stage9_output(df, city_df, founders_df, investors_df, co_invest_df, taxonomy_df):
    log("\n" + "=" * 60)
    log("STAGE 9: Output Files")
    log("=" * 60)

    # Master table column order
    master_cols = [
        "startup_id", "Name", "Website", "City", "Country", "Region",
        "primary_industry", "industry_tags", "industry_raw",
        "Description", "founded_year",
        "funding_usd", "funding_raw", "revenue_usd", "revenue_raw",
        "funding_stage", "last_round_raw",
        "team_size_min", "team_size_max", "team_size_category", "team_size_raw",
        "founders_list", "investors_list",
    ]

    # Rename for output
    master = df[master_cols].copy()
    master = master.rename(columns={"Name": "name", "Website": "website",
                                     "City": "city", "Country": "country",
                                     "Region": "region", "Description": "description"})

    # Convert industry_tags list to pipe-separated string
    master["industry_tags"] = master["industry_tags"].apply(
        lambda x: " | ".join(x) if isinstance(x, list) else str(x)
    )

    # Save CSV
    master.to_csv(os.path.join(OUTPUT_DIR, "startups_master.csv"), index=False, encoding="utf-8-sig")
    log(f"  Saved startups_master.csv ({len(master)} rows)")

    # Save Parquet
    master.to_parquet(os.path.join(OUTPUT_DIR, "startups_master.parquet"), index=False)
    log(f"  Saved startups_master.parquet")

    # City mapping
    if not city_df.empty:
        city_df.to_csv(os.path.join(OUTPUT_DIR, "startup_cities.csv"), index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(columns=["startup_id", "city"]).to_csv(
            os.path.join(OUTPUT_DIR, "startup_cities.csv"), index=False
        )
    log(f"  Saved startup_cities.csv ({len(city_df)} rows)")

    # Founders
    founders_df.to_csv(os.path.join(OUTPUT_DIR, "founders.csv"), index=False, encoding="utf-8-sig")
    log(f"  Saved founders.csv ({len(founders_df)} rows)")

    # Investors
    investors_df.to_csv(os.path.join(OUTPUT_DIR, "investors.csv"), index=False, encoding="utf-8-sig")
    log(f"  Saved investors.csv ({len(investors_df)} rows)")

    # Co-investments
    co_invest_df.to_csv(os.path.join(OUTPUT_DIR, "co_investments.csv"), index=False, encoding="utf-8-sig")
    log(f"  Saved co_investments.csv ({len(co_invest_df)} rows)")

    # Taxonomy
    taxonomy_df.to_csv(os.path.join(OUTPUT_DIR, "industry_taxonomy.csv"), index=False, encoding="utf-8-sig")
    log(f"  Saved industry_taxonomy.csv ({len(taxonomy_df)} rows)")

    # Data quality report
    quality_rows = []
    for city in master["city"].unique():
        city_data = master[master["city"] == city]
        row = {"city": city, "total": len(city_data)}
        for col in ["website", "primary_industry", "description", "founded_year",
                     "funding_usd", "revenue_usd", "funding_stage",
                     "team_size_min", "founders_list", "investors_list"]:
            non_null = city_data[col].notna() & city_data[col].ne("") & city_data[col].ne(0)
            row[f"{col}_pct"] = round(non_null.sum() / len(city_data) * 100, 1)
        quality_rows.append(row)

    quality_df = pd.DataFrame(quality_rows).sort_values("total", ascending=False)
    quality_df.to_csv(os.path.join(OUTPUT_DIR, "data_quality_report.csv"), index=False)
    log(f"  Saved data_quality_report.csv")

    # Save cleaning log
    save_log()
    log(f"  Saved cleaning_log.txt")

    return master


# ============================================================
# STAGE 10: Validation & Summary Stats
# ============================================================

def stage10_validation(master, founders_df, investors_df, co_invest_df):
    log("\n" + "=" * 60)
    log("STAGE 10: Validation & Summary Stats")
    log("=" * 60)

    # 1. Total
    log(f"\n  1. Total startups (after dedup): {len(master)}")

    # 2. Per city
    log("\n  2. Startups per city:")
    for city, count in master["city"].value_counts().items():
        log(f"     {city}: {count}")

    # 3. Per industry
    log("\n  3. Startups per primary industry:")
    for ind, count in master["primary_industry"].value_counts().items():
        log(f"     {ind}: {count}")

    # 4. Per region
    log("\n  4. Startups per region:")
    for reg, count in master["region"].value_counts().items():
        log(f"     {reg}: {count}")

    # 5. Funding stats by region
    log("\n  5. Funding (USD) by region:")
    for reg in master["region"].unique():
        rdata = master[master["region"] == reg]["funding_usd"].dropna()
        if len(rdata) > 0:
            log(f"     {reg}: median=${rdata.median():,.0f}, mean=${rdata.mean():,.0f}, "
                f"min=${rdata.min():,.0f}, max=${rdata.max():,.0f} (n={len(rdata)})")

    # 6. Data completeness
    log("\n  6. Data completeness:")
    key_fields = ["website", "primary_industry", "description", "founded_year",
                   "funding_usd", "revenue_usd", "funding_stage",
                   "team_size_min", "founders_list", "investors_list"]
    for col in key_fields:
        non_null = master[col].notna() & master[col].ne("") & master[col].ne(0)
        pct = non_null.sum() / len(master) * 100
        log(f"     {col}: {pct:.1f}%")

    # 7. Top 10 investors
    log("\n  7. Top 10 most active investors:")
    if not investors_df.empty:
        top_inv = investors_df["investor_name"].value_counts().head(10)
        for name, count in top_inv.items():
            log(f"     {name}: {count} startups")

    # 8. Top 10 co-investor pairs
    log("\n  8. Top 10 co-investor pairs:")
    if not co_invest_df.empty:
        pair_counts = co_invest_df.groupby(["investor_a", "investor_b"]).size().sort_values(ascending=False).head(10)
        for (a, b), count in pair_counts.items():
            log(f"     {a} + {b}: {count} co-investments")

    # 9. Founded year distribution
    log("\n  9. Founded year distribution:")
    years = master["founded_year"].dropna()
    bins = {"pre-2010": (0, 2009), "2010-2015": (2010, 2015),
            "2016-2020": (2016, 2020), "2021-2023": (2021, 2023), "2024+": (2024, 9999)}
    for label, (lo, hi) in bins.items():
        count = ((years >= lo) & (years <= hi)).sum()
        log(f"     {label}: {count}")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    log("=" * 60)
    log("GLOBAL STARTUPS NORMALIZATION PIPELINE")
    log("=" * 60)

    # Stage 1
    df = stage1_combine()

    # Stage 2
    df, city_df = stage2_dedup(df)

    # Stage 3
    df = stage3_funding_revenue(df)

    # Stage 4
    df = stage4_founded(df)

    # Stage 5
    df = stage5_team_size(df)

    # Stage 6
    df, taxonomy_df = stage6_industry(df)

    # Stage 7
    df = stage7_funding_round(df)

    # Stage 8
    df, founders_df, investors_df, co_invest_df = stage8_founders_investors(df)

    # Stage 9
    master = stage9_output(df, city_df, founders_df, investors_df, co_invest_df, taxonomy_df)

    # Stage 10
    stage10_validation(master, founders_df, investors_df, co_invest_df)

    # Final save of log
    save_log()

    log("\n" + "=" * 60)
    log("PIPELINE COMPLETE")
    log("=" * 60)


if __name__ == "__main__":
    main()
