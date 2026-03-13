"""
Scrape Seedtable Seoul startups listing and export to JSON.
Uses Playwright with stealth to load the page, then extracts
structured startup data from the DOM.
"""

import sys
import json
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://www.seedtable.com/best-startups-in-seoul"
OUTPUT_FILE = "seedtable_seoul.json"


def create_browser(p):
    """Create a stealth browser context."""
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )
    page = context.new_page()
    stealth = Stealth()
    stealth.apply_stealth_sync(page)
    return browser, context, page


def scroll_to_bottom(page, max_scrolls=20):
    """Scroll page to ensure all content is loaded."""
    for i in range(max_scrolls):
        prev_height = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == prev_height:
            print(f"  Scrolling done after {i+1} scrolls")
            break


def dump_page_structure(page):
    """Dump relevant page structure for debugging."""
    # Save full HTML for debug
    html = page.content()
    with open("page_debug_seedtable.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  Page HTML saved to page_debug_seedtable.html")

    # Print some structural hints
    info = page.evaluate("""() => {
        const result = {};
        // Check for tables
        result.tables = document.querySelectorAll('table').length;
        // Check for common card/list patterns
        result.articles = document.querySelectorAll('article').length;
        result.cards = document.querySelectorAll('[class*="card"]').length;
        result.items = document.querySelectorAll('[class*="item"]').length;
        result.companies = document.querySelectorAll('[class*="company"], [class*="startup"]').length;
        result.rows = document.querySelectorAll('[class*="row"]').length;
        result.links = document.querySelectorAll('a').length;

        // Get first 3 table structures if any
        const tables = document.querySelectorAll('table');
        result.tableDetails = [];
        tables.forEach((t, i) => {
            if (i < 3) {
                const headers = Array.from(t.querySelectorAll('th')).map(th => th.textContent.trim());
                const firstRow = t.querySelector('tbody tr');
                const firstCells = firstRow ? Array.from(firstRow.querySelectorAll('td')).map(td => td.textContent.trim().substring(0, 80)) : [];
                result.tableDetails.push({headers, firstCells, rowCount: t.querySelectorAll('tbody tr').length});
            }
        });

        // Check for any list-like containers
        const allElements = document.querySelectorAll('*');
        const classCount = {};
        allElements.forEach(el => {
            if (el.children.length > 5) {
                const cls = el.className;
                if (cls && typeof cls === 'string' && cls.length < 100) {
                    if (!classCount[cls]) classCount[cls] = 0;
                    classCount[cls]++;
                }
            }
        });

        // Get h1, h2 text for context
        result.headings = Array.from(document.querySelectorAll('h1, h2')).map(h => h.textContent.trim()).slice(0, 10);

        return result;
    }""")
    print(f"  Page structure: {json.dumps(info, indent=2)}")
    return info


def extract_startups_from_table(page):
    """Try extracting startup data from table elements."""
    startups = page.evaluate("""() => {
        const results = [];
        const tables = document.querySelectorAll('table');

        for (const table of tables) {
            const headers = Array.from(table.querySelectorAll('thead th, thead td, tr:first-child th, tr:first-child td'))
                .map(h => h.textContent.trim());

            if (headers.length < 2) continue;

            const rows = table.querySelectorAll('tbody tr');
            for (const row of rows) {
                const cells = Array.from(row.querySelectorAll('td'));
                if (cells.length < 2) continue;

                const entry = {};
                cells.forEach((cell, i) => {
                    const key = headers[i] || `col_${i}`;
                    // Also grab any links
                    const link = cell.querySelector('a');
                    entry[key] = cell.textContent.trim();
                    if (link && link.href) {
                        entry[key + '_link'] = link.href;
                    }
                });
                if (Object.values(entry).some(v => v && v.length > 0)) {
                    results.push(entry);
                }
            }
        }
        return results;
    }""")
    return startups


def extract_startups_generic(page):
    """Generic extraction: look for repeated card/item structures."""
    startups = page.evaluate("""() => {
        const results = [];

        // Strategy 1: Look for links with startup names + surrounding data
        // Seedtable typically has a list of companies with details
        const allLinks = document.querySelectorAll('a[href*="/startups/"], a[href*="company"]');

        // Strategy 2: Look for repeated div structures
        // Find parent containers that have many similar children
        function findRepeatingContainers() {
            const candidates = [];
            const allDivs = document.querySelectorAll('div, section, ul');
            for (const container of allDivs) {
                const children = container.children;
                if (children.length >= 5) {
                    const firstTag = children[0].tagName;
                    const firstClass = children[0].className;
                    let matching = 0;
                    for (const child of children) {
                        if (child.tagName === firstTag && child.className === firstClass) matching++;
                    }
                    if (matching >= 5 && matching / children.length > 0.7) {
                        candidates.push({container, count: matching, childClass: firstClass});
                    }
                }
            }
            // Sort by count descending
            candidates.sort((a, b) => b.count - a.count);
            return candidates;
        }

        const containers = findRepeatingContainers();
        // Try the top candidate
        for (const {container, count} of containers.slice(0, 3)) {
            const children = Array.from(container.children);
            for (const child of children) {
                const text = child.textContent.trim();
                if (text.length < 5) continue;

                const links = Array.from(child.querySelectorAll('a'));
                const entry = {_rawText: text.substring(0, 500)};

                for (const link of links) {
                    const href = link.href;
                    const linkText = link.textContent.trim();
                    if (href && !href.includes('seedtable.com') && linkText) {
                        entry._externalLink = href;
                        entry._externalLinkText = linkText;
                    }
                    if (linkText && linkText.length > 1 && linkText.length < 100) {
                        if (!entry._name) entry._name = linkText;
                    }
                }

                // Try to find structured data within the child
                const spans = Array.from(child.querySelectorAll('span, p, div, td'));
                entry._texts = spans.map(s => s.textContent.trim()).filter(t => t.length > 0 && t.length < 200).slice(0, 15);

                if (entry._name || entry._rawText.length > 10) {
                    results.push(entry);
                }
            }
            if (results.length >= 5) break;
        }

        return {containers: containers.slice(0,5).map(c => ({count: c.count, childClass: c.childClass, sample: c.container.children[0].textContent.trim().substring(0, 200)})), items: results.slice(0, 5)};
    }""")
    return startups


def extract_seedtable_startups(page):
    """
    Extract startups from Seedtable page.
    First try table extraction, then fall back to card/list extraction.
    Uses page structure analysis to determine the best approach.
    """
    # Try table extraction first
    table_data = extract_startups_from_table(page)
    if table_data and len(table_data) >= 5:
        print(f"  Found {len(table_data)} startups in table format")
        print(f"  Sample keys: {list(table_data[0].keys())}")
        print(f"  Sample entry: {json.dumps(table_data[0], indent=2, ensure_ascii=False)}")
        return normalize_data(table_data)

    # If table didn't work, try generic extraction
    print("  No table data found, trying generic extraction...")
    generic = extract_startups_generic(page)
    print(f"  Generic extraction result: {json.dumps(generic, indent=2, ensure_ascii=False)[:2000]}")

    # Final approach: extract everything via comprehensive JS
    print("  Trying comprehensive extraction...")
    startups = page.evaluate("""() => {
        const results = [];

        // Look for all elements that might be startup entries
        // Seedtable uses various layouts - try to find the main content area
        const main = document.querySelector('main, [role="main"], .content, #content, article') || document.body;

        // Find all heading + detail pairs
        const headings = main.querySelectorAll('h2, h3, h4');
        for (const h of headings) {
            const name = h.textContent.trim();
            if (name.length < 2 || name.length > 100) continue;

            // Look at siblings after this heading
            let sibling = h.nextElementSibling;
            const details = [];
            let description = '';
            let website = '';
            const links = h.querySelectorAll('a');
            for (const a of links) {
                if (a.href && !a.href.includes('seedtable')) website = a.href;
            }

            let count = 0;
            while (sibling && count < 10) {
                if (['H2','H3','H4'].includes(sibling.tagName)) break;
                const text = sibling.textContent.trim();
                if (text.length > 0) details.push(text);

                const sLinks = sibling.querySelectorAll('a');
                for (const a of sLinks) {
                    if (a.href && !a.href.includes('seedtable') && !website) {
                        website = a.href;
                    }
                }
                sibling = sibling.nextElementSibling;
                count++;
            }

            if (details.length > 0 || website) {
                results.push({name, details: details.join(' | '), website});
            }
        }

        return results;
    }""")

    if startups and len(startups) >= 3:
        print(f"  Found {len(startups)} entries via heading extraction")
        return normalize_heading_data(startups)

    return []


def normalize_data(raw_data):
    """Normalize table data to standard format."""
    startups = []
    for entry in raw_data:
        keys_lower = {k.lower().strip(): v for k, v in entry.items()}

        # Try to map common column names
        name = (keys_lower.get('name') or keys_lower.get('company') or
                keys_lower.get('startup') or keys_lower.get('company name') or
                keys_lower.get('col_0') or '')

        website = (keys_lower.get('website') or keys_lower.get('url') or
                   keys_lower.get('name_link') or keys_lower.get('company_link') or
                   keys_lower.get('startup_link') or keys_lower.get('col_0_link') or '')

        description = (keys_lower.get('description') or keys_lower.get('about') or
                       keys_lower.get('what they do') or '')

        industry = (keys_lower.get('industry') or keys_lower.get('category') or
                    keys_lower.get('sector') or keys_lower.get('tags') or
                    keys_lower.get('industries') or '')

        founded = (keys_lower.get('founded') or keys_lower.get('year') or
                   keys_lower.get('founded year') or keys_lower.get('year founded') or '')

        funding = (keys_lower.get('funding') or keys_lower.get('total funding') or
                   keys_lower.get('funding amount') or keys_lower.get('raised') or '')

        employees = (keys_lower.get('employees') or keys_lower.get('team size') or
                     keys_lower.get('team') or keys_lower.get('size') or
                     keys_lower.get('number of employees') or '')

        startup = {
            "Name": name.strip(),
            "Website": website.strip(),
            "Description": description.strip(),
            "Industry": industry.strip(),
            "Founded": founded.strip(),
            "Funding": funding.strip(),
            "Employees": employees.strip(),
        }

        # Include any extra fields not yet captured
        mapped_keys = {'name', 'company', 'startup', 'company name', 'col_0',
                       'website', 'url', 'name_link', 'company_link', 'startup_link', 'col_0_link',
                       'description', 'about', 'what they do',
                       'industry', 'category', 'sector', 'tags', 'industries',
                       'founded', 'year', 'founded year', 'year founded',
                       'funding', 'total funding', 'funding amount', 'raised',
                       'employees', 'team size', 'team', 'size', 'number of employees'}

        for k, v in keys_lower.items():
            if k not in mapped_keys and not k.endswith('_link') and v:
                # Add as extra field with capitalized key
                clean_key = k.title().replace('_', ' ')
                startup[clean_key] = v.strip()

        if startup["Name"]:
            startups.append(startup)

    return startups


def normalize_heading_data(raw_data):
    """Normalize heading-based data to standard format."""
    startups = []
    for entry in raw_data:
        startup = {
            "Name": entry.get('name', '').strip(),
            "Website": entry.get('website', '').strip(),
            "Description": entry.get('details', '').strip(),
            "Industry": "",
            "Founded": "",
            "Funding": "",
            "Employees": "",
        }

        # Try to parse details for structured info
        details = entry.get('details', '')
        # Look for year patterns
        year_match = re.search(r'(?:founded|since|est\.?)\s*:?\s*((?:19|20)\d{2})', details, re.I)
        if year_match:
            startup["Founded"] = year_match.group(1)

        # Look for funding patterns
        funding_match = re.search(r'(\$[\d.]+\s*[BMKbmk](?:illion)?)', details, re.I)
        if funding_match:
            startup["Funding"] = funding_match.group(1)

        if startup["Name"]:
            startups.append(startup)

    return startups


def scrape_seedtable_seoul():
    """Main scraping function."""
    print("=" * 60)
    print("Seedtable Seoul Startups Scraper")
    print("=" * 60)

    with sync_playwright() as p:
        browser, context, page = create_browser(p)

        print(f"\nLoading {URL}...")
        page.goto(URL, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)

        print("Scrolling to load all content...")
        scroll_to_bottom(page)

        print("\nAnalyzing page structure...")
        structure = dump_page_structure(page)

        print("\nExtracting startup data...")
        startups = extract_seedtable_startups(page)

        browser.close()

    if not startups:
        print("\nERROR: No startups extracted. Check page_debug_seedtable.html for the page content.")
        return []

    # Deduplicate by name
    seen = set()
    unique = []
    for s in startups:
        if s["Name"] and s["Name"] not in seen:
            seen.add(s["Name"])
            unique.append(s)

    print(f"\n{'='*60}")
    print(f"Results: {len(unique)} unique startups extracted")
    print(f"{'='*60}")

    # Show fields available
    all_keys = set()
    for s in unique:
        all_keys.update(s.keys())
    print(f"Fields: {sorted(all_keys)}")

    # Show first 5
    print("\nFirst 5 startups:")
    for s in unique[:5]:
        print(f"  {s['Name']}: {s.get('Website', 'N/A')} | {s.get('Industry', 'N/A')} | {s.get('Funding', 'N/A')}")

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {OUTPUT_FILE}")

    return unique


if __name__ == "__main__":
    scrape_seedtable_seoul()
