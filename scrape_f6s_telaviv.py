import sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080}, locale="en-US",
    )
    page = context.new_page()
    stealth = Stealth()
    stealth.apply_stealth_sync(page)

    page.goto("https://www.f6s.com/companies/israel/tel-aviv/lo", timeout=30000)
    page.wait_for_timeout(5000)
    for _ in range(10):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

    blocks = page.query_selector_all(".company-block")
    print(f"Found {len(blocks)} company blocks")

    startups = []
    for block in blocks:
        s = {}
        name_el = block.query_selector("h2.company-entry-title a")
        if not name_el: continue
        s["Name"] = name_el.inner_text().strip()
        s["F6S URL"] = name_el.get_attribute("href") or ""

        tagline_el = block.query_selector("h3")
        s["Tagline"] = tagline_el.inner_text().strip() if tagline_el else ""

        desc_el = block.query_selector(".profile-description")
        desc = ""
        if desc_el:
            desc = desc_el.inner_text().strip()
            if desc.endswith("\nmore"): desc = desc[:-5].strip()
        s["Description"] = desc

        loc = block.evaluate("""el => { const divs = el.querySelectorAll('.centered-content'); for (const div of divs) { const svg = div.querySelector('use[*|href="#location"]'); if (svg) return div.textContent.trim(); } return ''; }""")
        s["Location"] = loc.strip()

        founded = block.evaluate("""el => { const divs = el.querySelectorAll('.centered-content'); for (const div of divs) { const svg = div.querySelector('use[*|href="#clock"]'); if (svg) return div.textContent.trim(); } return ''; }""")
        m = re.search(r"Founded\s+(\d{4})", founded)
        s["Founded"] = m.group(1) if m else ""

        funding = block.evaluate("""el => { const divs = el.querySelectorAll('.centered-content'); for (const div of divs) { const svg = div.querySelector('use[*|href="#trend"]'); if (svg) return div.textContent.trim(); } return ''; }""")
        fm = re.search(r"(\$[\d,.]+[kmb]?)", funding, re.IGNORECASE)
        s["Funding"] = fm.group(1) if fm else ""
        im = re.search(r"(?:Raised\s*from|raised\s*from)\s*(.*?)(?:See all|$)", funding, re.IGNORECASE)
        s["Investors"] = re.sub(r"\s*and\s*\d+\s*more\s*$", "", im.group(1).strip()).strip() if im else ""

        team_el = block.query_selector(".collection-team-summary-wrapper")
        if team_el:
            tt = team_el.inner_text().strip()
            tm = re.search(r"Meet\s+(.*?)\s+that\s+work", tt)
            s["Team Members"] = tm.group(1) if tm else ""
        else:
            s["Team Members"] = ""

        dm = re.search(r"\(([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\)", s["Name"])
        s["Website"] = f"https://{dm.group(1)}" if dm else ""

        startups.append(s)

    # Try to get websites from profiles before bot blocks
    print(f"Extracted {len(startups)}. Fetching websites from profiles...")
    bot_blocked = False
    for i, s in enumerate(startups):
        if s["Website"] or bot_blocked: continue
        f6s_url = s.get("F6S URL", "")
        if not f6s_url: continue
        try:
            page.goto(f6s_url, timeout=12000)
            page.wait_for_timeout(1500)
            body_text = page.inner_text("body")
            if "bot" in body_text.lower() and len(body_text) < 500:
                print(f"  [{i+1}] Bot blocked — stopping")
                bot_blocked = True
                continue
            social = {"f6s.com","f6s.ca","linkedin.com","facebook.com","twitter.com","x.com","hubspot.com","instagram.com","youtube.com","github.com","crunchbase.com","google.com"}
            links = page.query_selector_all("a[href]")
            for link in links:
                href = link.get_attribute("href") or ""
                if href and href.startswith("http") and not any(d in href for d in social):
                    s["Website"] = href
                    print(f"  [{i+1}] {s['Name']} -> {href}")
                    break
        except:
            bot_blocked = True

    browser.close()
    with open("f6s_telaviv.json", "w", encoding="utf-8") as f:
        json.dump(startups, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(startups)} to f6s_telaviv.json")
    websites = sum(1 for s in startups if s["Website"])
    print(f"Websites found: {websites}/{len(startups)}")
