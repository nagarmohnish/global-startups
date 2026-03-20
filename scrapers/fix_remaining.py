"""Fix remaining missing websites and descriptions with robust extraction."""
import json, os, re, sys, time, traceback, glob
sys.stdout.reconfigure(encoding="utf-8")

from ddgs import DDGS
from urllib.parse import urlparse

PROGRESS_FILE = "data/_fix_progress.json"

# Comprehensive blocklist for website detection
BLOCKED_DOMAINS = [
    # Search engines
    "google.com", "bing.com", "duckduckgo.com", "yahoo.com", "yandex.com",
    # Social media
    "linkedin.com", "twitter.com", "x.com", "facebook.com", "instagram.com",
    "youtube.com", "tiktok.com", "reddit.com", "quora.com", "medium.com",
    # Startup databases / listing sites
    "crunchbase.com", "pitchbook.com", "owler.com", "craft.co", "tracxn.com",
    "zoominfo.com", "dnb.com", "cbinsights.com", "dealroom.co", "golden.com",
    "signal.nfx.com", "harmonic.ai", "datafox.com", "similarweb.com",
    "f6s.com", "failory.com", "seedtable.com", "wellfound.com", "angellist.com",
    "startupranking.com", "startupblink.com", "startus-insights.com",
    "finder.startupnationcentral.org", "startupnationcentral.org",
    "eu-startups.com", "techeu.com", "sifted.eu", "builtin.com",
    "ycombinator.com", "techstars.com",
    # Job / review sites
    "glassdoor.com", "indeed.com", "g2.com", "capterra.com", "trustpilot.com",
    "alternativeto.net", "producthunt.com", "theorg.com",
    # Lead gen / data sites
    "leadiq.com", "rocketreach.co", "apollo.io", "lusha.com", "clearbit.com",
    # News / press
    "techcrunch.com", "venturebeat.com", "wired.com", "theverge.com",
    "zdnet.com", "bloomberg.com", "forbes.com", "reuters.com", "cnbc.com",
    "prnewswire.com", "businesswire.com", "globenewswire.com", "prweb.com",
    "newswire.com", "benzinga.com",
    # Others
    "wikipedia.org", "amazon.com", "apple.com", "play.google.com",
    "apps.apple.com", "about.me", "github.com", "amazonaws.com",
    "iagora.com", "electrive.com", "globaldata.com",
    "peterfisk.com", "yelp.com", "bbb.org",
]

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

def is_blocked_domain(url):
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        return any(bd in domain for bd in BLOCKED_DOMAINS)
    except:
        return True

def find_best_website(results, company_name):
    """Find the actual company website with strict domain matching."""
    cn = re.sub(r'[^a-z0-9]', '', company_name.lower())
    cn_words = [w.lower() for w in company_name.split() if len(w) > 2]

    candidates = []
    for r in results:
        href = r.get("href", "")
        if not href or is_blocked_domain(href):
            continue
        try:
            parsed = urlparse(href)
            domain = parsed.netloc.lower().replace("www.", "")
            domain_name = domain.split('.')[0]
            domain_clean = re.sub(r'[^a-z0-9]', '', domain_name)

            score = 0

            # Strong match: company name is in the domain
            if cn[:4] in domain_clean or domain_clean in cn:
                score += 10
            # Check if any word from company name is in domain
            for w in cn_words:
                if w in domain_clean:
                    score += 5
                    break

            # Prefer root pages
            path = parsed.path.rstrip('/')
            if not path:
                score += 3
            elif path.count('/') <= 1:
                score += 1
            else:
                score -= 2

            # Prefer common TLDs
            tld = domain.split('.')[-1]
            if tld in ('com', 'io', 'ai', 'co', 'tech', 'dev', 'app'):
                score += 2

            # Title match
            title = r.get("title", "").lower()
            if company_name.lower() in title:
                score += 3

            if score > 0:
                candidates.append((score, href, domain))
        except:
            continue

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        if candidates[0][0] >= 5:
            # Return just the root URL, not deep links
            best_url = candidates[0][1]
            try:
                parsed = urlparse(best_url)
                return f"{parsed.scheme}://{parsed.netloc}/"
            except:
                return best_url
    return None

def extract_clean_description(results, company_name):
    """Extract clean company description, rejecting search artifacts."""
    cn_lower = company_name.lower().split()[0]
    best_desc = None
    best_score = 0

    for r in results:
        body = r.get("body", "").strip()
        href = r.get("href", "")

        if not body or len(body) < 40:
            continue

        # Reject search artifacts
        if any(x in body for x in [
            "Missing:", "Show results with:", "Frequently Asked Questions",
            "How much funding has", "Who invested in", "Where is",
            "When was", "headquarters?", "funding rounds to date",
        ]):
            continue

        # Clean date prefixes
        if re.match(r'^\d+ (?:days?|hours?|weeks?|months?|years?) ago', body):
            body = re.sub(r'^\d+ (?:days?|hours?|weeks?|months?|years?) ago\s*[-·—]?\s*', '', body)
            if len(body) < 40:
                continue

        # Clean leading date patterns like "Oct 19, 2021 ·"
        body = re.sub(r'^[A-Z][a-z]{2} \d{1,2}, \d{4}\s*[-·—]?\s*', '', body)

        # Skip pure funding snippets
        if re.match(r'^.{0,20}(?:has raised|raised a total|total funding)', body):
            continue

        score = 0

        # Must mention the company
        if cn_lower in body.lower():
            score += 5
        else:
            continue

        # Prefer real descriptions
        desc_patterns = [
            r'\b(?:is a|is an|are a|was founded|develops|provides|offers|builds|creates|enables)\b',
            r'\b(?:platform|solution|service|technology|software|company|startup|product)\b',
            r'\b(?:helps|allows|empowers|connects|transforms|automates|simplifies)\b',
        ]
        for pattern in desc_patterns:
            if re.search(pattern, body.lower()):
                score += 3

        # Prefer from company's own website
        if not is_blocked_domain(href):
            domain = urlparse(href).netloc.lower().replace("www.", "")
            domain_clean = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
            cn_clean = re.sub(r'[^a-z0-9]', '', company_name.lower())
            if cn_clean[:4] in domain_clean or domain_clean in cn_clean:
                score += 5

        if 80 < len(body) < 300:
            score += 2
        elif len(body) >= 300:
            score += 1

        if score > best_score:
            best_score = score
            best_desc = body

    if best_desc:
        best_desc = re.sub(r'\s+', ' ', best_desc).strip()
        if len(best_desc) > 300:
            best_desc = best_desc[:297] + "..."
        return best_desc
    return None

def research_entry(name, city=""):
    found = {}
    ddgs = DDGS()

    # Search 1: official site
    try:
        query = f'{name} official site'
        results = list(ddgs.text(query, max_results=8))
        website = find_best_website(results, name)
        if website:
            found["Website"] = website
        desc = extract_clean_description(results, name)
        if desc:
            found["Description"] = desc
        time.sleep(1.5)
    except Exception as e:
        print(f"    Search 1 error: {e}")
        time.sleep(3)
        return found

    # Search 2: with city context
    if not found.get("Website") or not found.get("Description"):
        try:
            query = f'"{name}" startup {city}'
            results = list(ddgs.text(query, max_results=8))
            if not found.get("Website"):
                website = find_best_website(results, name)
                if website:
                    found["Website"] = website
            if not found.get("Description"):
                desc = extract_clean_description(results, name)
                if desc:
                    found["Description"] = desc
            time.sleep(1.5)
        except Exception as e:
            print(f"    Search 2 error: {e}")
            time.sleep(3)

    # Search 3: website-only search
    if not found.get("Website"):
        try:
            query = f'{name} .com site'
            results = list(ddgs.text(query, max_results=5))
            website = find_best_website(results, name)
            if website:
                found["Website"] = website
            time.sleep(1.5)
        except Exception:
            time.sleep(3)

    return found

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

def main():
    files = sorted(glob.glob("data/*.json"))
    files = [f for f in files if not os.path.basename(f).startswith("_")]

    # Reset progress for fresh run
    progress = {}

    to_fix = 0
    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            data = json.load(fh)
        for entry in data:
            name = entry.get("Name", "").strip()
            if not name:
                continue
            if is_missing(entry.get("Website", "")) or is_missing(entry.get("Description", "")):
                to_fix += 1

    print(f"Entries needing website or description fix: {to_fix}")

    fixed_total = 0
    processed = 0

    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            data = json.load(fh)

        city = city_from_filename(fp)
        file_key = os.path.basename(fp)
        if file_key not in progress:
            progress[file_key] = {}

        file_entries = []
        for entry in data:
            name = entry.get("Name", "").strip()
            if not name:
                continue
            needs_website = is_missing(entry.get("Website", ""))
            needs_desc = is_missing(entry.get("Description", ""))
            if needs_website or needs_desc:
                file_entries.append((entry, name, needs_website, needs_desc))

        if not file_entries:
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {fp} ({len(file_entries)} to fix)")
        print(f"{'='*60}")

        for i, (entry, name, needs_website, needs_desc) in enumerate(file_entries):
            missing = []
            if needs_website: missing.append("Website")
            if needs_desc: missing.append("Description")

            print(f"  [{i+1}/{len(file_entries)}] {name} (need: {', '.join(missing)})")
            processed += 1

            try:
                found = research_entry(name, city)
                result = {}

                if needs_website and found.get("Website"):
                    entry["Website"] = found["Website"]
                    result["Website"] = found["Website"]
                    print(f"    + Website: {found['Website'][:80]}")
                    fixed_total += 1

                if needs_desc and found.get("Description"):
                    entry["Description"] = found["Description"]
                    result["Description"] = found["Description"]
                    print(f"    + Description: {found['Description'][:80]}...")
                    fixed_total += 1

                if not result:
                    result["_status"] = "not_found"

                progress[file_key][f"fix_{name}"] = result
                save_progress(progress)

            except Exception as e:
                print(f"    ERROR: {e}")
                time.sleep(5)

        with open(fp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

        print(f"  Fixed in {file_key}: {sum(1 for e in file_entries if not is_missing(e[0].get('Website','')) or not is_missing(e[0].get('Description','')))}")

    print(f"\n{'='*60}")
    print(f"DONE. Processed {processed}, fixed {fixed_total}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
