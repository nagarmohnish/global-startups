"""Research v2: Fill Website, Industry, Description, Revenue, Funding for all entries."""
import json, os, re, sys, time, traceback, glob
sys.stdout.reconfigure(encoding="utf-8")

from ddgs import DDGS

TARGET_FIELDS = ["Website", "Industry", "Description", "Revenue", "Funding"]

PROGRESS_FILE = "data/_research_v2_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def is_missing(val):
    return not val or val in ("N/A", "", "n/a", "Unknown", "-")

def extract_data(results, company_name):
    """Extract Website, Industry, Description, Revenue, Funding from search results."""
    info = {}

    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        text = f"{title} {body}".lower()

        # Website candidates
        if href:
            skip_domains = [
                "crunchbase.com", "linkedin.com", "twitter.com", "x.com",
                "facebook.com", "youtube.com", "wikipedia.org", "bloomberg.com",
                "techcrunch.com", "forbes.com", "f6s.com", "failory.com",
                "seedtable.com", "google.com", "bing.com", "duckduckgo.com",
                "pitchbook.com", "wellfound.com", "angellist.com", "zoominfo.com",
                "glassdoor.com", "indeed.com", "github.com", "amazonaws.com",
                "tracxn.com", "owler.com", "dnb.com", "craft.co", "globaldata.com",
                "about.me", "medium.com", "reddit.com", "quora.com",
                "peterfisk.com", "amazon.com", "apple.com",
                "play.google.com", "apps.apple.com", "cbinsights.com",
                "yelp.com", "bbb.org", "trustpilot.com",
            ]
            if not any(d in href.lower() for d in skip_domains):
                if "website_candidates" not in info:
                    info["website_candidates"] = []
                info["website_candidates"].append(href)

        # Funding
        if not info.get("Funding"):
            funding_match = re.search(r'(?:raised?|funding|total\s+funding|funding\s+total)[:\s]+\$?([\d,.]+)\s*(billion|million|[bmk])\b', text)
            if funding_match:
                amount = funding_match.group(1).replace(",", "")
                unit = funding_match.group(2).lower()
                if unit in ("billion", "b"):
                    info["Funding"] = f"${amount}B"
                elif unit in ("million", "m"):
                    info["Funding"] = f"${amount}M"
                elif unit == "k":
                    info["Funding"] = f"${amount}K"

        # Revenue
        if not info.get("Revenue"):
            # Pattern: revenue of $X million/billion, $X million in revenue, annual revenue $X
            rev_patterns = [
                r'(?:annual\s+)?revenue[:\s]+\$?([\d,.]+)\s*(billion|million|[bmk])\b',
                r'(?:annual\s+)?revenue\s+(?:of|is|was|around|approximately|about|estimated\s+at)\s+\$?([\d,.]+)\s*(billion|million|[bmk])\b',
                r'\$?([\d,.]+)\s*(billion|million)\s+(?:in\s+)?(?:annual\s+)?revenue',
                r'(?:arr|annual\s+recurring\s+revenue|mrr)[:\s]+\$?([\d,.]+)\s*(billion|million|[bmk])\b',
                r'revenue[:\s]+\$?([\d,.]+)\s*(billion|million|[bmk])',
                r'generates?\s+\$?([\d,.]+)\s*(billion|million)\s+(?:in\s+)?revenue',
                r'(?:revenue|sales|turnover)\s+(?:reached|exceeded|surpassed|hit)\s+\$?([\d,.]+)\s*(billion|million|[bmk])',
            ]
            for pat in rev_patterns:
                rev_match = re.search(pat, text)
                if rev_match:
                    amount = rev_match.group(1).replace(",", "")
                    unit = rev_match.group(2).lower()
                    if unit in ("billion", "b"):
                        info["Revenue"] = f"${amount}B"
                    elif unit in ("million", "m"):
                        info["Revenue"] = f"${amount}M"
                    elif unit == "k":
                        info["Revenue"] = f"${amount}K"
                    break

        # Industry
        if not info.get("Industry"):
            ind_match = re.search(r'(?:industries?|sector|category|field)[:\s]+([A-Za-z\s,&/]+?)(?:\.|,\s*(?:founded|based|raised|total|the))', text)
            if ind_match:
                industry = ind_match.group(1).strip().title()
                if 3 < len(industry) < 80:
                    info["Industry"] = industry
            else:
                industry_kws = {
                    "fintech": "Fintech", "healthtech": "HealthTech", "health tech": "HealthTech",
                    "edtech": "EdTech", "biotech": "Biotech", "medtech": "MedTech",
                    "artificial intelligence": "AI", " ai ": "AI", "machine learning": "AI/ML",
                    "e-commerce": "E-Commerce", "ecommerce": "E-Commerce",
                    "saas": "SaaS", "cybersecurity": "Cybersecurity", "cyber security": "Cybersecurity",
                    "blockchain": "Blockchain", "cryptocurrency": "Blockchain/Crypto",
                    "logistics": "Logistics", "insurtech": "InsurTech", "proptech": "PropTech",
                    "agritech": "AgriTech", "agtech": "AgriTech", "cleantech": "CleanTech",
                    "renewable energy": "CleanTech", "solar": "Energy", "electric vehicle": "EV/Mobility",
                    "autonomous": "Autonomous Vehicles", "robotics": "Robotics",
                    "food tech": "FoodTech", "foodtech": "FoodTech", "delivery": "Delivery/Logistics",
                    "gaming": "Gaming", "social media": "Social Media",
                    "cloud computing": "Cloud Computing", "iot": "IoT",
                    "semiconductor": "Semiconductors", "hardware": "Hardware",
                    "pharmaceutical": "Pharma", "drug discovery": "Pharma/Biotech",
                    "real estate": "Real Estate", "travel": "Travel/Tourism",
                    "automotive": "Automotive", "drone": "Drones/UAV",
                    "fashion": "Fashion", "beauty": "Beauty/Cosmetics",
                    "marketing": "Marketing/AdTech", "advertising": "Marketing/AdTech",
                    "payment": "Payments/Fintech", "banking": "Banking/Fintech",
                    "insurance": "Insurance", "telecom": "Telecom",
                    "construction": "Construction", "manufacturing": "Manufacturing",
                    "education": "Education", "healthcare": "Healthcare",
                    "software": "Software", "data analytics": "Data Analytics",
                    "deep tech": "Deep Tech", "quantum": "Quantum Computing",
                    "space": "SpaceTech", "legal tech": "LegalTech", "legaltech": "LegalTech",
                    "hr tech": "HRTech", "hrtech": "HRTech", "regtech": "RegTech",
                    "climate": "ClimateTech", "sustainability": "Sustainability",
                    "3d printing": "3D Printing", "ar/vr": "AR/VR", "virtual reality": "AR/VR",
                    "augmented reality": "AR/VR", "metaverse": "AR/VR",
                    "devops": "DevOps", "infrastructure": "Infrastructure",
                    "security": "Security", "supply chain": "Supply Chain",
                    "marketplace": "Marketplace", "platform": "Platform",
                    "analytics": "Analytics", "big data": "Big Data",
                    "mobility": "Mobility", "transportation": "Transportation",
                    "fitness": "Fitness/Wellness", "wellness": "Fitness/Wellness",
                    "mental health": "Mental Health", "telemedicine": "Telemedicine",
                    "biomedical": "Biomedical", "diagnostics": "Diagnostics",
                    "genomics": "Genomics", "life sciences": "Life Sciences",
                    "materials": "Advanced Materials", "battery": "Battery/Energy Storage",
                    "energy storage": "Battery/Energy Storage",
                    "nuclear": "Nuclear Energy", "hydrogen": "Hydrogen/Energy",
                    "carbon capture": "Carbon Capture", "recycling": "Recycling/CircularEconomy",
                    "waste": "Waste Management", "water": "Water/CleanTech",
                    "agriculture": "Agriculture", "farming": "Agriculture",
                    "food": "Food/FoodTech", "restaurant": "Food/Restaurant",
                    "retail": "Retail", "consumer": "Consumer",
                    "media": "Media", "entertainment": "Entertainment",
                    "music": "Music", "video": "Video/Streaming",
                    "sports": "Sports", "pet": "PetTech",
                    "recruiting": "Recruiting/HRTech", "hiring": "Recruiting/HRTech",
                    "crypto": "Crypto/Web3", "web3": "Crypto/Web3", "nft": "Crypto/Web3",
                    "defi": "DeFi/Crypto",
                }
                for kw, ind in industry_kws.items():
                    if kw in text:
                        info["Industry"] = ind
                        break

        # Description
        if not info.get("Description"):
            if len(body) > 50 and company_name.lower().split()[0] in body.lower():
                desc = body.strip()
                if len(desc) > 300:
                    desc = desc[:297] + "..."
                info["Description"] = desc

    # Select best website
    candidates = info.pop("website_candidates", [])
    if candidates and not info.get("Website"):
        from urllib.parse import urlparse
        cn = re.sub(r'[^a-z0-9]', '', company_name.lower())
        best = None
        for url in candidates:
            try:
                domain = urlparse(url).netloc.lower().replace("www.", "")
                domain_clean = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
                if cn[:4] in domain_clean or domain_clean in cn:
                    best = url
                    break
            except Exception:
                pass
        info["Website"] = best or candidates[0]

    return info

def city_from_filename(filename):
    base = os.path.basename(filename).replace(".json", "")
    city_map = {
        "beijing": "Beijing China", "berlin": "Berlin Germany",
        "boston": "Boston USA", "guangzhou": "Guangzhou China",
        "hangzhou": "Hangzhou China", "london": "London UK",
        "los_angeles": "Los Angeles USA", "madrid": "Madrid Spain",
        "new_york": "New York USA", "new_york_city": "New York USA",
        "paris": "Paris France", "saopaulo": "Sao Paulo Brazil",
        "seoul": "Seoul South Korea", "shanghai": "Shanghai China",
        "shenzhen": "Shenzhen China", "singapore": "Singapore",
        "siliconvalley": "Silicon Valley USA", "sf_siliconvalley": "Silicon Valley USA",
        "sj_siliconvalley": "Silicon Valley USA", "stockholm": "Stockholm Sweden",
        "telaviv": "Tel Aviv Israel", "tokyo": "Tokyo Japan",
        "zurich": "Zurich Switzerland",
    }
    for key, city in city_map.items():
        if key in base:
            return city
    return ""

def research_startup(name, city="", existing=None):
    """Research a startup for the 5 target fields."""
    if existing is None:
        existing = {}

    missing_fields = [f for f in TARGET_FIELDS if is_missing(existing.get(f, ""))]
    if not missing_fields:
        return {}

    found = {}
    ddgs = DDGS()

    # Search 1: General company info
    try:
        query = f'"{name}" startup company {city}'
        results = list(ddgs.text(query, max_results=8))
        extracted = extract_data(results, name)
        for k, v in extracted.items():
            if k in missing_fields and is_missing(found.get(k, "")):
                found[k] = v
        time.sleep(1.5)
    except Exception as e:
        print(f"    Search error: {e}")
        time.sleep(3)
        return found

    # Search 2: Revenue + funding specific
    still_missing = [f for f in missing_fields if is_missing(found.get(f, ""))]
    if any(f in still_missing for f in ["Revenue", "Funding"]):
        try:
            query = f'"{name}" revenue funding annual {city}'
            results = list(ddgs.text(query, max_results=8))
            extracted = extract_data(results, name)
            for k, v in extracted.items():
                if k in still_missing and is_missing(found.get(k, "")):
                    found[k] = v
            time.sleep(1.5)
        except Exception as e:
            print(f"    Revenue search error: {e}")
            time.sleep(3)

    # Search 3: Crunchbase for remaining
    still_missing = [f for f in missing_fields if is_missing(found.get(f, ""))]
    if still_missing:
        try:
            query = f'"{name}" crunchbase funding revenue {city}'
            results = list(ddgs.text(query, max_results=5))
            extracted = extract_data(results, name)
            for k, v in extracted.items():
                if k in still_missing and is_missing(found.get(k, "")):
                    found[k] = v
            time.sleep(1.5)
        except Exception as e:
            print(f"    Crunchbase search error: {e}")
            time.sleep(3)

    # Search 4: Website if still missing
    still_missing = [f for f in missing_fields if is_missing(found.get(f, ""))]
    if "Website" in still_missing:
        try:
            query = f'{name} official website'
            results = list(ddgs.text(query, max_results=5))
            extracted = extract_data(results, name)
            if extracted.get("Website"):
                found["Website"] = extracted["Website"]
            time.sleep(1.5)
        except Exception:
            time.sleep(3)

    return found

def process_file(filepath, progress):
    """Process a single JSON file."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print(f"  Skipping {filepath} (empty)")
        return 0

    city = city_from_filename(filepath)
    file_key = os.path.basename(filepath)
    if file_key not in progress:
        progress[file_key] = {}

    updated = 0
    total = len(data)

    for i, entry in enumerate(data):
        name = entry.get("Name", "").strip()
        if not name:
            continue

        # Check if already researched in this run
        if name in progress[file_key]:
            prev = progress[file_key][name]
            for field, val in prev.items():
                if field in TARGET_FIELDS and is_missing(entry.get(field, "")) and not is_missing(val):
                    entry[field] = val
            continue

        # Check what's missing
        missing = [f for f in TARGET_FIELDS if is_missing(entry.get(f, ""))]
        if not missing:
            progress[file_key][name] = {"_status": "complete"}
            continue

        print(f"  [{i+1}/{total}] {name} (missing: {', '.join(missing)})")

        try:
            found = research_startup(name, city, entry)

            if found:
                for field, val in found.items():
                    if field in TARGET_FIELDS and is_missing(entry.get(field, "")) and not is_missing(val):
                        entry[field] = val
                        print(f"    + {field}: {str(val)[:80]}")
                updated += 1

            progress[file_key][name] = found if found else {"_status": "no_data_found"}
            save_progress(progress)

        except Exception as e:
            print(f"    ERROR: {e}")
            traceback.print_exc()
            time.sleep(5)

    # Save updated file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return updated

def main():
    files = sorted(glob.glob("data/*.json"))
    files = [f for f in files if not os.path.basename(f).startswith("_")]

    print(f"Research v2 - Target fields: {TARGET_FIELDS}")
    print(f"Processing {len(files)} data files...\n")

    # Count what needs to be done
    total_entries = 0
    total_missing = 0
    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
            for entry in data:
                total_entries += 1
                if any(is_missing(entry.get(field, "")) for field in TARGET_FIELDS):
                    total_missing += 1
    print(f"Total entries: {total_entries}, needing research: {total_missing}\n")

    progress = load_progress()
    grand_total = 0

    for filepath in files:
        print(f"\n{'='*60}")
        print(f"Processing: {filepath}")
        print(f"{'='*60}")

        try:
            count = process_file(filepath, progress)
            grand_total += count
            print(f"  Updated {count} entries in {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  FILE ERROR: {e}")
            traceback.print_exc()

    # Final stats
    print(f"\n{'='*60}")
    print(f"RESEARCH COMPLETE - Updated {grand_total} entries")
    print(f"{'='*60}")

    # Print fill rates
    totals = {f: 0 for f in TARGET_FIELDS}
    filled = {f: 0 for f in TARGET_FIELDS}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
            for entry in data:
                for field in TARGET_FIELDS:
                    totals[field] += 1
                    if not is_missing(entry.get(field, "")):
                        filled[field] += 1
    print("\nFill rates:")
    for field in TARGET_FIELDS:
        pct = round(filled[field] / totals[field] * 100) if totals[field] else 0
        print(f"  {field}: {filled[field]}/{totals[field]} ({pct}%)")

if __name__ == "__main__":
    main()
