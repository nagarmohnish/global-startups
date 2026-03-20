"""Research and fill missing startup data using web search."""
import json, os, re, sys, time, traceback
sys.stdout.reconfigure(encoding="utf-8")

from ddgs import DDGS
import requests
from bs4 import BeautifulSoup

COL_ORDER = ["Name","Website","Industry","Description","Founded","Funding","Last Round","Founders","Top Investors","Team Size"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Progress tracking
PROGRESS_FILE = "data/_research_progress.json"

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

def extract_from_search_results(results, company_name):
    """Extract structured data from search result snippets."""
    info = {}

    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        text = f"{title} {body}".lower()

        # Website - collect candidates, pick best one later
        if href:
            skip_domains = ["crunchbase.com", "linkedin.com", "twitter.com", "x.com",
                          "facebook.com", "youtube.com", "wikipedia.org", "bloomberg.com",
                          "techcrunch.com", "forbes.com", "f6s.com", "failory.com",
                          "seedtable.com", "google.com", "bing.com", "duckduckgo.com",
                          "pitchbook.com", "wellfound.com", "angellist.com", "zoominfo.com",
                          "glassdoor.com", "indeed.com", "github.com", "amazonaws.com",
                          "tracxn.com", "owler.com", "dnb.com", "craft.co", "globaldata.com",
                          "about.me", "medium.com", "reddit.com", "quora.com",
                          "peterfisk.com", "theflying", "amazon.com", "apple.com",
                          "play.google.com", "apps.apple.com", "cbinsights.com"]
            if not any(d in href.lower() for d in skip_domains):
                if "website_candidates" not in info:
                    info["website_candidates"] = []
                info["website_candidates"].append(href)

        # Founded year
        if not info.get("Founded"):
            founded_match = re.search(r'(?:founded|established|started|launched)\s+(?:in\s+)?(\d{4})', text)
            if founded_match:
                year = int(founded_match.group(1))
                if 1990 <= year <= 2026:
                    info["Founded"] = str(year)

        # Funding
        if not info.get("Funding"):
            funding_match = re.search(r'(?:raised?|funding|total\s+funding)[:\s]+\$?([\d,.]+)\s*(billion|million|[bmk])\b', text)
            if funding_match:
                amount = funding_match.group(1).replace(",", "")
                unit = funding_match.group(2).lower()
                if unit in ("billion", "b"):
                    info["Funding"] = f"${amount}B"
                elif unit in ("million", "m"):
                    info["Funding"] = f"${amount}M"
                elif unit == "k":
                    info["Funding"] = f"${amount}K"

        # Industry
        if not info.get("Industry"):
            ind_match = re.search(r'(?:industries?|sector|category|field)[:\s]+([A-Za-z\s,&/]+?)(?:\.|,\s*(?:founded|based|raised|total|the))', text)
            if ind_match:
                industry = ind_match.group(1).strip().title()
                if 3 < len(industry) < 80:
                    info["Industry"] = industry
            else:
                # Try common industry keywords
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
                }
                for kw, ind in industry_kws.items():
                    if kw in text:
                        info["Industry"] = ind
                        break

        # Description - prefer Crunchbase descriptions
        if not info.get("Description"):
            if len(body) > 50 and company_name.lower().split()[0] in body.lower():
                # Clean up the snippet
                desc = body.strip()
                if len(desc) > 300:
                    desc = desc[:297] + "..."
                info["Description"] = desc

        # Team size
        if not info.get("Team Size"):
            team_match = re.search(r'(\d+[\+]?)\s*(?:employees?|team\s*(?:members?|size)|people|staff)', text)
            if team_match:
                info["Team Size"] = team_match.group(1) + " employees"
            else:
                team_range = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*(?:employees?|team|people|staff)', text)
                if team_range:
                    info["Team Size"] = f"{team_range.group(1)}-{team_range.group(2)} employees"

        # Founders
        if not info.get("Founders"):
            founder_match = re.search(r'(?:founded?\s+by|co-?founders?|founders?)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s*(?:,|and)\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)*)',
                                     f"{title} {body}")
            if founder_match:
                info["Founders"] = founder_match.group(1).strip()

        # Last Round
        if not info.get("Last Round"):
            round_match = re.search(r'(series\s+[a-z]|seed|pre-seed|angel|ipo|venture\s+round|grant|debt|convertible|bridge)\s+(?:round|funding)?', text)
            if round_match:
                info["Last Round"] = round_match.group(1).strip().title()

    # Select best website from candidates
    candidates = info.pop("website_candidates", [])
    if candidates and not info.get("Website"):
        cn = re.sub(r'[^a-z0-9]', '', company_name.lower())
        best = None
        for url in candidates:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.lower().replace("www.", "")
                domain_clean = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
                if cn[:4] in domain_clean or domain_clean in cn:
                    best = url
                    break
            except Exception:
                pass
        info["Website"] = best or candidates[0]

    return info

def fetch_crunchbase_info(company_name, crunchbase_url=None):
    """Try to extract info from Crunchbase page."""
    info = {}
    try:
        if not crunchbase_url:
            return info
        resp = requests.get(crunchbase_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return info
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(" ", strip=True).lower()

        # Try to extract founded year
        founded = re.search(r'founded\s+(?:date|year)?[:\s]*(\d{4})', text)
        if founded:
            info["Founded"] = founded.group(1)

        # Try to extract description from meta
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"].strip()
            if len(desc) > 30:
                info["Description"] = desc[:300] + "..." if len(desc) > 300 else desc
    except Exception:
        pass
    return info

def research_startup(name, city="", existing=None):
    """Research a single startup and return found data."""
    if existing is None:
        existing = {}

    missing_fields = [f for f in COL_ORDER[1:] if is_missing(existing.get(f, ""))]
    if not missing_fields:
        return {}

    found = {}
    ddgs = DDGS()

    # Search 1: General company search
    try:
        query = f'"{name}" startup company {city}'
        results = list(ddgs.text(query, max_results=8))
        extracted = extract_from_search_results(results, name)
        for k, v in extracted.items():
            if k in missing_fields and is_missing(found.get(k, "")):
                found[k] = v

        # Look for Crunchbase URL in results
        cb_url = None
        for r in results:
            if "crunchbase.com/organization/" in r.get("href", ""):
                cb_url = r["href"]
                break

        time.sleep(1.5)
    except Exception as e:
        print(f"    Search error: {e}")
        time.sleep(3)
        return found

    # Check what's still missing
    still_missing = [f for f in missing_fields if is_missing(found.get(f, ""))]
    if not still_missing:
        return found

    # Search 2: Crunchbase-specific search for remaining fields
    try:
        query = f'"{name}" crunchbase funding founders {city}'
        results = list(ddgs.text(query, max_results=5))
        extracted = extract_from_search_results(results, name)
        for k, v in extracted.items():
            if k in still_missing and is_missing(found.get(k, "")):
                found[k] = v

        # Update Crunchbase URL if found
        if not cb_url:
            for r in results:
                if "crunchbase.com/organization/" in r.get("href", ""):
                    cb_url = r["href"]
                    break

        time.sleep(1.5)
    except Exception as e:
        print(f"    Crunchbase search error: {e}")
        time.sleep(3)

    # Search 3: Try to get website if still missing
    still_missing = [f for f in missing_fields if is_missing(found.get(f, ""))]
    if "Website" in still_missing:
        try:
            query = f'{name} official website'
            results = list(ddgs.text(query, max_results=5))
            extracted = extract_from_search_results(results, name)
            if extracted.get("Website"):
                found["Website"] = extracted["Website"]
            time.sleep(1.5)
        except Exception:
            time.sleep(3)

    # Search 4: Founders and investors if still missing
    still_missing = [f for f in missing_fields if is_missing(found.get(f, ""))]
    if any(f in still_missing for f in ["Founders", "Top Investors"]):
        try:
            query = f'"{name}" founders investors funding round {city}'
            results = list(ddgs.text(query, max_results=5))
            extracted = extract_from_search_results(results, name)
            for k, v in extracted.items():
                if k in still_missing and is_missing(found.get(k, "")):
                    found[k] = v
            time.sleep(1.5)
        except Exception:
            time.sleep(3)

    return found

def city_from_filename(filename):
    """Extract city name for search context."""
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

def process_file(filepath):
    """Process a single JSON file and fill in missing data."""
    progress = load_progress()

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

        # Check if already researched
        if name in progress[file_key]:
            # Apply previously found data
            prev = progress[file_key][name]
            applied = False
            for field, val in prev.items():
                if field in COL_ORDER and is_missing(entry.get(field, "")) and not is_missing(val):
                    entry[field] = val
                    applied = True
            if applied:
                updated += 1
            continue

        # Check if any fields are missing
        missing = [f for f in COL_ORDER[1:] if is_missing(entry.get(f, ""))]
        if not missing:
            progress[file_key][name] = {"_status": "complete"}
            continue

        print(f"  [{i+1}/{total}] Researching: {name} (missing: {', '.join(missing)})")

        try:
            found = research_startup(name, city, entry)

            if found:
                for field, val in found.items():
                    if field in COL_ORDER and is_missing(entry.get(field, "")) and not is_missing(val):
                        entry[field] = val
                        print(f"    + {field}: {val[:80]}{'...' if len(str(val))>80 else ''}")
                updated += 1

            # Save progress
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
    import glob

    files = sorted(glob.glob("data/*.json"))
    files = [f for f in files if not os.path.basename(f).startswith("_")]

    print(f"Processing {len(files)} data files...\n")

    grand_total = 0
    for filepath in files:
        print(f"\n{'='*60}")
        print(f"Processing: {filepath}")
        print(f"{'='*60}")

        try:
            count = process_file(filepath)
            grand_total += count
            print(f"  Updated {count} entries in {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  FILE ERROR: {e}")
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"TOTAL: Updated {grand_total} entries across all files")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
