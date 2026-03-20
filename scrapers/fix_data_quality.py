"""Fix data quality issues: bad websites (listing/news sites) and bad descriptions (search artifacts)."""
import json, os, re, sys, time, glob, traceback
sys.stdout.reconfigure(encoding="utf-8")

from urllib.parse import urlparse
from ddgs import DDGS

# Domains that are NOT actual company websites
BAD_WEBSITE_DOMAINS = [
    "leadiq.com", "startupnationcentral.org", "prnewswire.com",
    "businesswire.com", "globenewswire.com", "prweb.com", "newswire.com",
    "iagora.com", "techstars.com", "electrive.com", "eu-startups.com",
    "startus-insights.com", "dealroom.co", "golden.com", "signal.nfx.com",
    "theorg.com", "rocketreach.co", "apollo.io", "cbinsights.com",
    "tracxn.com", "datafox.com", "harmonic.ai", "builtin.com",
    "techcrunch.com", "venturebeat.com", "wired.com", "theverge.com",
    "zdnet.com", "bloomberg.com", "forbes.com", "reuters.com", "cnbc.com",
    "crunchbase.com", "pitchbook.com", "owler.com", "craft.co",
    "zoominfo.com", "dnb.com", "similarweb.com", "g2.com",
    "producthunt.com", "alternativeto.net", "capterra.com",
    "trustpilot.com", "glassdoor.com", "indeed.com",
    "wellfound.com", "angellist.com", "f6s.com", "failory.com",
    "seedtable.com", "startupranking.com", "startupblink.com",
    "ycombinator.com", "techeu.com", "sifted.eu",
    "linkedin.com", "twitter.com", "x.com", "facebook.com",
    "youtube.com", "wikipedia.org", "google.com", "bing.com",
    "duckduckgo.com", "github.com", "amazonaws.com",
    "about.me", "medium.com", "reddit.com", "quora.com",
    "amazon.com", "apple.com", "play.google.com", "apps.apple.com",
    "yelp.com", "bbb.org", "peterfisk.com",
    "globaldata.com", "companiesmarketcap.com", "stockanalysis.com",
    "macrotrends.net", "statista.com", "finder.com",
    "goodfirms.co", "clutch.co", "ambitionbox.com",
    "tofler.in", "zauba.com", "justdial.com",
    "sec.gov", "sec.report", "marketwatch.com",
    "yahoo.com", "finance.yahoo.com",
]

PROGRESS_FILE = "data/_fix_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def is_bad_website(url):
    """Check if a URL points to a listing/news site rather than the company's own site."""
    if not url or url in ("N/A", "", "-"):
        return False
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        return any(bd in domain for bd in BAD_WEBSITE_DOMAINS)
    except Exception:
        return False

def is_bad_description(desc):
    """Check if a description contains search artifacts or is not a real description."""
    if not desc or desc in ("N/A", "", "-"):
        return False
    # Search engine artifacts
    if "Missing:" in desc and "Show results with:" in desc:
        return True
    if "Show results with:" in desc:
        return True
    # Search question snippets (from Crunchbase/Tracxn FAQ pages)
    if re.search(r"(?:How much funding has|Who invested in|Where is .+(?:headquarters|located)\?|When was .+ founded\?|What is .+ revenue)", desc):
        return True
    # Date prefix from search snippets
    if re.search(r"^\d+ (?:days?|hours?|weeks?|months?) ago", desc):
        return True
    # Pure funding info without company description
    if re.search(r"^(?:.*?has raised a total of|.*?funding rounds? to date)", desc) and not re.search(r"(?:is a|develops|provides|offers|platform|solution|company|startup|service)", desc.lower()):
        return True
    # Contains source site references as main content
    if re.search(r"^(?:Frequently Asked Questions|FAQ)", desc):
        return True
    return False

def find_company_website(name, city=""):
    """Search for the actual company website."""
    ddgs = DDGS()

    # Search 1: Direct website search
    try:
        results = list(ddgs.text(f'{name} official site', max_results=10))
        time.sleep(1.5)
    except Exception:
        time.sleep(3)
        return None

    # Collect candidates with scoring
    candidates = []
    cn = re.sub(r'[^a-z0-9]', '', name.lower())
    cn_words = [w for w in re.sub(r'[^a-z0-9\s]', '', name.lower()).split() if len(w) > 2]

    for r in results:
        href = r.get("href", "")
        if not href:
            continue
        try:
            parsed = urlparse(href)
            domain = parsed.netloc.lower().replace("www.", "")

            # Skip known bad domains
            if any(bd in domain for bd in BAD_WEBSITE_DOMAINS):
                continue

            domain_name = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])

            # Score the candidate
            score = 0

            # Strong match: company name is in domain
            if cn[:4] in domain_name or domain_name in cn:
                score += 10

            # Partial match: any significant word from company name in domain
            for word in cn_words:
                if len(word) > 3 and word in domain_name:
                    score += 5

            # Prefer shorter domains (less likely to be subdirectory pages)
            if parsed.path in ('', '/', '/en', '/en/'):
                score += 2

            # Prefer common TLDs
            if domain.endswith(('.com', '.io', '.ai', '.co', '.org', '.tech', '.app')):
                score += 1

            if score > 0:
                candidates.append((score, href, domain))
        except Exception:
            continue

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]

    # Search 2: More specific search if no good candidate
    try:
        results = list(ddgs.text(f'"{name}" homepage {city}', max_results=5))
        time.sleep(1.5)
    except Exception:
        time.sleep(3)
        return None

    for r in results:
        href = r.get("href", "")
        if not href:
            continue
        try:
            domain = urlparse(href).netloc.lower().replace("www.", "")
            if any(bd in domain for bd in BAD_WEBSITE_DOMAINS):
                continue
            domain_name = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
            if cn[:4] in domain_name or domain_name in cn:
                return href
        except Exception:
            continue

    return None

def find_company_description(name, city="", website=""):
    """Find a proper company description."""
    ddgs = DDGS()

    queries = [
        f'"{name}" "is a" company startup',
        f'"{name}" about company {city}',
    ]
    if website:
        queries.insert(0, f'site:{urlparse(website).netloc} {name} about')

    for query in queries:
        try:
            results = list(ddgs.text(query, max_results=8))
            time.sleep(1.5)
        except Exception:
            time.sleep(3)
            continue

        for r in results:
            body = r.get("body", "")
            if not body or len(body) < 40:
                continue

            # Skip if it's a search artifact
            if is_bad_description(body):
                continue

            # Must mention the company name
            if name.lower().split()[0] not in body.lower():
                continue

            # Should contain descriptive language
            if re.search(r'(?:is a|provides|offers|develops|platform|solution|company|startup|service|technology|software|helps|enables|builds|creates)', body.lower()):
                desc = body.strip()
                # Clean up common prefixes
                desc = re.sub(r'^\d+ (?:days?|hours?|weeks?|months?|years?) ago\s*[-–—·]?\s*', '', desc)
                desc = re.sub(r'^(?:About|Overview|Description)[:\s]+', '', desc, flags=re.IGNORECASE)
                if len(desc) > 300:
                    desc = desc[:297] + "..."
                if len(desc) > 40:
                    return desc

    return None

def city_from_filename(filename):
    base = os.path.basename(filename).replace(".json", "")
    city_map = {
        "beijing": "Beijing", "berlin": "Berlin", "boston": "Boston",
        "guangzhou": "Guangzhou", "hangzhou": "Hangzhou", "london": "London",
        "los_angeles": "Los Angeles", "madrid": "Madrid",
        "new_york": "New York", "paris": "Paris", "saopaulo": "Sao Paulo",
        "seoul": "Seoul", "shanghai": "Shanghai", "shenzhen": "Shenzhen",
        "singapore": "Singapore", "siliconvalley": "Silicon Valley",
        "stockholm": "Stockholm", "telaviv": "Tel Aviv", "tokyo": "Tokyo",
        "zurich": "Zurich",
    }
    for key, city in city_map.items():
        if key in base:
            return city
    return ""

def main():
    files = sorted(glob.glob("data/*.json"))
    files = [f for f in files if not os.path.basename(f).startswith("_")]

    # First pass: identify all issues
    print("=== AUDIT PHASE ===")
    bad_websites = []
    bad_descs = []

    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            data = json.load(fh)
        for entry in data:
            name = entry.get("Name", "")
            if is_bad_website(entry.get("Website", "")):
                bad_websites.append((fp, name))
            if is_bad_description(entry.get("Description", "")):
                bad_descs.append((fp, name))

    print(f"Bad websites to fix: {len(bad_websites)}")
    print(f"Bad descriptions to fix: {len(bad_descs)}")

    # Combine into unique (file, name) pairs needing work
    needs_fix = {}
    for fp, name in bad_websites:
        key = (fp, name)
        if key not in needs_fix:
            needs_fix[key] = {"website": True, "description": False}
        else:
            needs_fix[key]["website"] = True
    for fp, name in bad_descs:
        key = (fp, name)
        if key not in needs_fix:
            needs_fix[key] = {"website": False, "description": True}
        else:
            needs_fix[key]["description"] = True

    print(f"Total entries to fix: {len(needs_fix)}\n")

    # Second pass: fix issues
    print("=== FIX PHASE ===")
    progress = load_progress()
    fixed_count = 0

    # Group by file for efficient processing
    by_file = {}
    for (fp, name), issues in needs_fix.items():
        if fp not in by_file:
            by_file[fp] = []
        by_file[fp].append((name, issues))

    for fp in sorted(by_file.keys()):
        entries_to_fix = by_file[fp]
        city = city_from_filename(fp)
        file_key = os.path.basename(fp)

        print(f"\n{'='*60}")
        print(f"Fixing: {fp} ({len(entries_to_fix)} entries)")
        print(f"{'='*60}")

        with open(fp, encoding="utf-8") as fh:
            data = json.load(fh)

        if file_key not in progress:
            progress[file_key] = {}

        modified = False
        for name, issues in entries_to_fix:
            # Check if already fixed in this run
            if name in progress[file_key]:
                prev = progress[file_key][name]
                # Apply cached fixes
                for entry in data:
                    if entry.get("Name") == name:
                        if prev.get("Website"):
                            entry["Website"] = prev["Website"]
                        if prev.get("Description"):
                            entry["Description"] = prev["Description"]
                        modified = True
                continue

            # Find the entry in data
            entry = None
            for e in data:
                if e.get("Name") == name:
                    entry = e
                    break
            if not entry:
                continue

            fix_what = []
            if issues["website"]:
                fix_what.append("website")
            if issues["description"]:
                fix_what.append("description")

            print(f"  Fixing {name} ({', '.join(fix_what)})")

            result = {}

            # Fix website
            if issues["website"]:
                entry["Website"] = ""  # Clear bad website first
                new_url = find_company_website(name, city)
                if new_url and not is_bad_website(new_url):
                    entry["Website"] = new_url
                    result["Website"] = new_url
                    print(f"    + Website: {new_url}")
                    modified = True
                else:
                    result["Website"] = ""
                    print(f"    - Website: not found")

            # Fix description
            if issues["description"]:
                entry["Description"] = ""  # Clear bad description first
                website = entry.get("Website", "")
                new_desc = find_company_description(name, city, website)
                if new_desc and not is_bad_description(new_desc):
                    entry["Description"] = new_desc
                    result["Description"] = new_desc
                    print(f"    + Description: {new_desc[:80]}...")
                    modified = True
                else:
                    result["Description"] = ""
                    print(f"    - Description: not found")

            progress[file_key][name] = result
            save_progress(progress)
            fixed_count += 1

        if modified:
            with open(fp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)

    # Final audit
    print(f"\n{'='*60}")
    print(f"FIX COMPLETE - Processed {fixed_count} entries")
    print(f"{'='*60}")

    # Recount issues
    remaining_bad_web = 0
    remaining_bad_desc = 0
    total_entries = 0
    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            data = json.load(fh)
        for entry in data:
            total_entries += 1
            if is_bad_website(entry.get("Website", "")):
                remaining_bad_web += 1
            if is_bad_description(entry.get("Description", "")):
                remaining_bad_desc += 1

    print(f"\nRemaining bad websites: {remaining_bad_web}/{total_entries}")
    print(f"Remaining bad descriptions: {remaining_bad_desc}/{total_entries}")

if __name__ == "__main__":
    main()
