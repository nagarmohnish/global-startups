"""Scrape Silicon Valley startups from Failory (SF + San Jose), Seedtable, and F6S."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

SOCIAL = {
    "f6s.com","f6s.ca","linkedin.com","facebook.com","twitter.com","x.com",
    "hubspot.com","instagram.com","youtube.com","github.com","crunchbase.com","google.com",
}

def scrape_failory(page, city_slug, label):
    print(f"=== FAILORY {label} ===")
    page.goto(f"https://www.failory.com/startups/{city_slug}", timeout=30000)
    page.wait_for_timeout(5000)
    for _ in range(15):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

    headings = page.query_selector_all("h3")
    featured_names = []
    for h in headings:
        text = h.inner_text().strip()
        m = re.match(r"(\d+)\.\s+(.+)", text)
        if m:
            featured_names.append(m.group(2).strip())

    detail_tables = page.query_selector_all("table:not(.failory-table)")
    results = []
    for i, table in enumerate(detail_tables):
        rows = table.query_selector_all("tr")
        data = {}
        for row in rows:
            cells = row.query_selector_all("td, th")
            if len(cells) >= 2:
                data[cells[0].inner_text().strip()] = cells[1].inner_text().strip()
        desc = table.evaluate(
            'el => { let prev = el.previousElementSibling;'
            ' while (prev) { if (prev.tagName === "P" && prev.textContent.trim().length > 20)'
            ' return prev.textContent.trim(); prev = prev.previousElementSibling; } return ""; }'
        )
        name = featured_names[i] if i < len(featured_names) else ""
        results.append({
            "Name": name, "Website": "", "Description": desc[:500],
            "Industry": "", "Founded": data.get("Year Founded", ""),
            "Funding": data.get("Funding Amount", ""),
            "Last Round": data.get("Last Funding Status", ""),
            "Team Size": data.get("Startup Size", ""),
            "Founders": data.get("Founders", ""),
            "Top Investors": data.get("Top Investors", ""),
        })

    trows = page.query_selector_all("table.failory-table tbody tr")
    for row in trows:
        name_el = row.query_selector("a.startup-name")
        if not name_el:
            continue
        name = name_el.inner_text().strip()
        href = name_el.get_attribute("href") or ""
        if "?ref=" in href:
            href = href.split("?ref=")[0]
        industry_el = row.query_selector("td.industry")
        year_el = row.query_selector("td.year")
        amount_el = row.query_selector("td.amount")
        round_el = row.query_selector("td.round")
        results.append({
            "Name": name, "Website": href,
            "Description": "",
            "Industry": industry_el.inner_text().strip() if industry_el else "",
            "Founded": year_el.inner_text().strip() if year_el else "",
            "Funding": amount_el.inner_text().strip() if amount_el else "",
            "Last Round": round_el.inner_text().strip() if round_el else "",
            "Team Size": "", "Founders": "", "Top Investors": "",
        })
    print(f"  Failory {label}: {len(results)} startups")
    return results


def scrape_seedtable(page, city_slug, label):
    print(f"=== SEEDTABLE {label} ===")
    try:
        page.goto(f"https://www.seedtable.com/best-startups-in-{city_slug}", timeout=30000)
        page.wait_for_timeout(5000)
    except Exception as e:
        print(f"  Seedtable {label}: failed to load - {e}")
        return []
    for _ in range(15):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

    text = page.inner_text("body")
    results = []
    sblocks = re.split(r"\n(?=[A-Z0-9][^\n]{1,80}\n\n\d+\n\nFunding Rounds)", text)
    for block in sblocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if len(lines) < 5 or "Funding Rounds" not in block:
            continue
        name = lines[0]
        money = ""; desc = ""; industries = []; people = []
        i = 1
        while i < len(lines):
            if lines[i].isdigit() and i + 1 < len(lines) and "Funding Rounds" in lines[i + 1]:
                i += 2; continue
            if lines[i].startswith("$") and i + 1 < len(lines) and "Money raised" in lines[i + 1]:
                money = lines[i]; i += 2; continue
            if lines[i] == "Industries:":
                i += 1
                while i < len(lines) and lines[i] not in ["Location:", "Key people:"] and not lines[i].startswith("$"):
                    industries.append(lines[i]); i += 1
                continue
            if lines[i] == "Key people:":
                i += 1
                while i < len(lines) and lines[i] not in ["Industries:", "Location:"] and not lines[i].isdigit():
                    if len(lines[i]) > 2:
                        people.append(re.sub(r"\s*Linkedin\s*", "", lines[i]).strip())
                    i += 1
                continue
            if lines[i] == "Location:":
                i += 1
                while i < len(lines) and lines[i] not in ["Industries:", "Key people:"] and not lines[i].startswith("$"):
                    i += 1
                continue
            if lines[i] not in ["Funding Rounds", "Money raised"] and not lines[i].isdigit() and len(lines[i]) > 30:
                desc = lines[i]
            i += 1
        if name and len(name) < 100:
            results.append({
                "Name": name.replace(" (company)", ""), "Website": "", "Description": desc,
                "Industry": ", ".join(industries), "Founded": "", "Funding": money,
                "Last Round": "",
                "Founders": ", ".join([p for p in people if "****" not in p][:3]),
                "Top Investors": "", "Team Size": "",
            })
    print(f"  Seedtable {label}: {len(results)} startups")
    return results


def scrape_f6s(page, city_slug, label):
    print(f"=== F6S {label} ===")
    try:
        page.goto(f"https://www.f6s.com/companies/united-states/{city_slug}/lo", timeout=30000)
        page.wait_for_timeout(5000)
    except Exception as e:
        print(f"  F6S {label}: failed to load - {e}")
        return []

    body = page.inner_text("body")
    if "bot" in body.lower() and len(body) < 500:
        print(f"  F6S {label}: BOT BLOCKED on listing")
        return []

    for _ in range(10):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

    blocks = page.query_selector_all(".company-block")
    results = []
    for block in blocks:
        name_el = block.query_selector("h2.company-entry-title a")
        if not name_el:
            continue
        s = {"Name": name_el.inner_text().strip(), "F6S URL": name_el.get_attribute("href") or ""}

        tagline_el = block.query_selector("h3")
        s["Tagline"] = tagline_el.inner_text().strip() if tagline_el else ""

        desc_el = block.query_selector(".profile-description")
        desc = ""
        if desc_el:
            desc = desc_el.inner_text().strip()
            if desc.endswith("\nmore"):
                desc = desc[:-5].strip()
        s["Description"] = desc

        founded = block.evaluate(
            'el => { const divs = el.querySelectorAll(".centered-content");'
            ' for (const div of divs) { const svg = div.querySelector(\'use[*|href="#clock"]\');'
            ' if (svg) return div.textContent.trim(); } return ""; }'
        )
        m = re.search(r"Founded\s+(\d{4})", founded)
        s["Founded"] = m.group(1) if m else ""

        funding = block.evaluate(
            'el => { const divs = el.querySelectorAll(".centered-content");'
            ' for (const div of divs) { const svg = div.querySelector(\'use[*|href="#trend"]\');'
            ' if (svg) return div.textContent.trim(); } return ""; }'
        )
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

        results.append({
            "Name": re.sub(r"\s*\(.*?\)", "", s["Name"]).strip(),
            "Website": s["Website"],
            "Description": s["Description"],
            "Industry": "",
            "Founded": s["Founded"],
            "Funding": s["Funding"],
            "Last Round": "",
            "Founders": "",
            "Top Investors": s["Investors"],
            "Team Size": s["Team Members"],
            "_f6s_url": s["F6S URL"],
        })

    bot_blocked = False
    for i, r in enumerate(results):
        if r["Website"] or bot_blocked:
            continue
        f6s_url = r.get("_f6s_url", "")
        if not f6s_url:
            continue
        try:
            page.goto(f6s_url, timeout=12000)
            page.wait_for_timeout(1500)
            bt = page.inner_text("body")
            if "bot" in bt.lower() and len(bt) < 500:
                bot_blocked = True
                print(f"  Bot blocked after {i} profile lookups")
                continue
            for link in page.query_selector_all("a[href]"):
                href = link.get_attribute("href") or ""
                if href and href.startswith("http") and not any(d in href for d in SOCIAL):
                    r["Website"] = href
                    break
        except:
            bot_blocked = True

    for r in results:
        r.pop("_f6s_url", None)
    w = sum(1 for r in results if r["Website"])
    print(f"  F6S {label}: {len(results)} startups, {w} with websites")
    return results


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}, locale="en-US",
        )
        page = context.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        # Failory - two cities
        failory_sf = scrape_failory(page, "san-francisco", "SAN FRANCISCO")
        failory_sj = scrape_failory(page, "san-jose", "SAN JOSE")

        # Seedtable - try both
        seedtable_sf = scrape_seedtable(page, "san-francisco", "SAN FRANCISCO")
        seedtable_sj = scrape_seedtable(page, "san-jose", "SAN JOSE")

        # F6S - try both
        f6s_sf = scrape_f6s(page, "san-francisco", "SAN FRANCISCO")
        f6s_sj = scrape_f6s(page, "san-jose", "SAN JOSE")

        browser.close()

    all_sources = {
        "failory_sf": failory_sf, "failory_sj": failory_sj,
        "seedtable_sf": seedtable_sf, "seedtable_sj": seedtable_sj,
        "f6s_sf": f6s_sf, "f6s_sj": f6s_sj,
    }
    for key, data in all_sources.items():
        with open(f"{key}_siliconvalley.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in all_sources.values())
    print(f"\nTotal raw: {total}")
    for k, v in all_sources.items():
        print(f"  {k}: {len(v)}")
