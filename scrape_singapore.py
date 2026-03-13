"""Scrape Singapore startups from Failory, F6S, and Seedtable."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

SOCIAL = {
    "f6s.com","f6s.ca","linkedin.com","facebook.com","twitter.com","x.com",
    "hubspot.com","instagram.com","youtube.com","github.com","crunchbase.com","google.com",
}

def scrape_failory(page):
    print("=== FAILORY SINGAPORE ===")
    page.goto("https://www.failory.com/startups/singapore", timeout=30000)
    page.wait_for_timeout(5000)
    for _ in range(15):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

    # Featured
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

    # Table
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
    print(f"  Failory: {len(results)} startups")
    return results


def scrape_f6s(page, context):
    print("=== F6S SINGAPORE ===")
    page.goto("https://www.f6s.com/companies/singapore/lo", timeout=30000)
    page.wait_for_timeout(5000)

    body = page.inner_text("body")
    if "bot" in body.lower() and len(body) < 500:
        print("  F6S: BOT BLOCKED on listing")
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

        loc = block.evaluate(
            'el => { const divs = el.querySelectorAll(".centered-content");'
            ' for (const div of divs) { const svg = div.querySelector(\'use[*|href="#location"]\');'
            ' if (svg) return div.textContent.trim(); } return ""; }'
        )
        s["Location"] = loc.strip()

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
        results.append(s)

    # Profile lookups
    bot_blocked = False
    for i, s in enumerate(results):
        if s["Website"] or bot_blocked:
            continue
        try:
            page.goto(s["F6S URL"], timeout=12000)
            page.wait_for_timeout(1500)
            bt = page.inner_text("body")
            if "bot" in bt.lower() and len(bt) < 500:
                bot_blocked = True
                print(f"  Bot blocked after {i} profile lookups")
                continue
            for link in page.query_selector_all("a[href]"):
                href = link.get_attribute("href") or ""
                if href and href.startswith("http") and not any(d in href for d in SOCIAL):
                    s["Website"] = href
                    break
        except:
            bot_blocked = True

    w = sum(1 for s in results if s["Website"])
    print(f"  F6S: {len(results)} startups, {w} with websites")
    return results


def scrape_seedtable(page):
    print("=== SEEDTABLE SINGAPORE ===")
    page.goto("https://www.seedtable.com/best-startups-in-singapore", timeout=30000)
    page.wait_for_timeout(5000)
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
    print(f"  Seedtable: {len(results)} startups")
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

        failory = scrape_failory(page)
        f6s = scrape_f6s(page, context)
        seedtable = scrape_seedtable(page)

        browser.close()

    with open("failory_singapore.json", "w", encoding="utf-8") as f:
        json.dump(failory, f, ensure_ascii=False, indent=2)
    with open("f6s_singapore.json", "w", encoding="utf-8") as f:
        json.dump(f6s, f, ensure_ascii=False, indent=2)
    with open("seedtable_singapore.json", "w", encoding="utf-8") as f:
        json.dump(seedtable, f, ensure_ascii=False, indent=2)

    print(f"\nTotal raw: Failory={len(failory)}, F6S={len(f6s)}, Seedtable={len(seedtable)}")
    print(f"Sum: {len(failory) + len(f6s) + len(seedtable)}")
