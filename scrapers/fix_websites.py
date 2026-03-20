"""Re-research missing websites with strict domain matching."""
import json, os, re, sys, time, glob
sys.stdout.reconfigure(encoding="utf-8")
from urllib.parse import urlparse
from ddgs import DDGS

BAD_DOMAINS = [
    "leadiq", "startupnationcentral", "prnewswire", "businesswire",
    "globenewswire", "prweb", "newswire", "iagora", "techstars",
    "electrive", "eu-startups", "startus-insights", "dealroom",
    "golden.com", "signal.nfx", "theorg", "rocketreach", "apollo.io",
    "cbinsights", "tracxn", "datafox", "harmonic.ai", "builtin",
    "techcrunch", "venturebeat", "wired.com", "theverge", "zdnet",
    "bloomberg", "forbes.com", "reuters", "cnbc", "bbc.com",
    "crunchbase", "pitchbook", "owler", "craft.co", "zoominfo",
    "dnb.com", "similarweb", "g2.com", "producthunt", "alternativeto",
    "capterra", "trustpilot", "glassdoor", "indeed.com", "wellfound",
    "angellist", "f6s.com", "failory", "seedtable", "startupranking",
    "ycombinator", "techeu", "sifted.eu", "tech.eu",
    "linkedin", "twitter.com", "x.com", "facebook.com",
    "youtube.com", "wikipedia.org", "instagram.com",
    "google.com", "bing.com", "duckduckgo",
    "amazon.com", "apple.com", "play.google", "apps.apple",
    "microsoft.com", "reddit.com", "quora.com", "medium.com",
    "about.me", "github.com", "gitlab.com",
    "yelp.com", "bbb.org", "goodfirms", "clutch.co",
    "prnewswire", "prlog", "preqin", "eqs-news",
    "vestbee", "foundersbeta", "yogonet", "why.berlin",
    "finsmes", "justretail", "solvusoft", "fashionunited",
    "remarkboard", "startupsucht", "join.com", "iagora",
    "esportsinsider", "x-rates", "parsers.vc", "briefnews",
    "startups.gallery", "madrimasd", "quasar.fi", "euroquity",
    "coreangels", "e-negociosnet", "novobrief", "workatastartup",
    "hackernoon", "startupxplore", "sp-edge", "thecompanycheck",
    "elreferente", "emis.com", "wimpykid", "boringbusinessnerd",
    "bitget.com", "fundup.ai", "startupluxembourg",
    "berlinstartupjobs", "theberlinlife", "startbase",
    "siliconcanals", "inc42", "startup-map", "autohome",
    "baidu.com", "bingquiz", "xhamster",
    "sec.gov", "sec.report", "marketwatch", "yahoo.com",
    "statista", "macrotrends", "companiesmarketcap",
    "stockanalysis", "finder.com", "globaldata",
    "tofler", "zauba", "justdial", "ambitionbox",
    "cathayinnovation", "empresadois", "ping.ooo",
    "wbresearch",
]

PROGRESS_FILE = "data/_fix_websites_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def is_bad_domain(domain):
    return any(bd in domain for bd in BAD_DOMAINS)

def domain_matches_company(domain, name):
    """Strict check: does the domain belong to this company?"""
    domain_name = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
    cn = re.sub(r'[^a-z0-9]', '', name.lower())
    cn_words = [w for w in re.sub(r'[^a-z0-9\s]', '', name.lower()).split() if len(w) > 2]

    # Direct match
    if len(cn) >= 4 and cn[:5] in domain_name:
        return True
    if len(domain_name) >= 4 and domain_name in cn:
        return True
    # Word match - any significant word from company name in domain
    for w in cn_words:
        if len(w) >= 3 and w in domain_name:
            return True
    # Domain word in company name
    for w in re.findall(r'[a-z]{4,}', domain_name):
        if w in cn:
            return True
    return False

def search_website(name, city):
    """Find the company's actual website with strict matching."""
    ddgs = DDGS()
    cn = re.sub(r'[^a-z0-9]', '', name.lower())

    queries = [
        f'{name} official website',
        f'"{name}" site homepage {city}',
    ]

    for query in queries:
        try:
            results = list(ddgs.text(query, max_results=10))
            time.sleep(2)
        except Exception as e:
            time.sleep(3)
            continue

        best = None
        best_score = 0

        for r in results:
            href = r.get("href", "")
            if not href:
                continue
            try:
                parsed = urlparse(href)
                domain = parsed.netloc.lower().replace("www.", "")

                if is_bad_domain(domain):
                    continue

                if not domain_matches_company(domain, name):
                    continue

                # Score it
                domain_name = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
                score = 0
                if cn[:5] in domain_name:
                    score += 10
                if domain_name in cn:
                    score += 8
                if parsed.path in ('', '/', '/en', '/en/'):
                    score += 3
                if domain.endswith(('.com', '.io', '.ai', '.co', '.org', '.tech', '.app')):
                    score += 1

                if score > best_score:
                    best_score = score
                    best = f"{parsed.scheme}://{parsed.netloc}/"
            except Exception:
                continue

        if best:
            return best

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

    progress = load_progress()
    total_fixed = 0
    total_processed = 0

    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            data = json.load(fh)

        city = city_from_filename(fp)
        file_key = os.path.basename(fp)
        if file_key not in progress:
            progress[file_key] = {}

        modified = False
        needs_fix = [(i, e) for i, e in enumerate(data)
                     if not e.get("Website") or e.get("Website", "").strip() in ("N/A", "", "-")]

        if not needs_fix:
            continue

        print(f"\n{'='*50}")
        print(f"{fp} - {len(needs_fix)} missing websites")
        print(f"{'='*50}")

        for idx, entry in needs_fix:
            name = entry.get("Name", "").strip()
            if not name:
                continue

            if name in progress[file_key]:
                cached = progress[file_key][name]
                if cached and cached != "not_found":
                    entry["Website"] = cached
                    modified = True
                continue

            total_processed += 1
            url = search_website(name, city)

            if url:
                entry["Website"] = url
                progress[file_key][name] = url
                print(f"  + {name}: {url}")
                total_fixed += 1
                modified = True
            else:
                progress[file_key][name] = "not_found"
                print(f"  - {name}: not found")

            save_progress(progress)

        if modified:
            with open(fp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"DONE. Processed {total_processed}, fixed {total_fixed}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
