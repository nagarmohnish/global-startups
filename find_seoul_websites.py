import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import time
import asyncio
from urllib.parse import quote_plus, urlparse
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

SKIP_DOMAINS = [
    'linkedin.com', 'facebook.com', 'twitter.com', 'x.com',
    'f6s.com', 'crunchbase.com', 'instagram.com', 'youtube.com',
    'github.com', 'medium.com', 'tiktok.com', 'pinterest.com',
    'glassdoor.com', 'indeed.com', 'bing.com', 'microsoft.com',
    'google.com', 'naver.com', 'reddit.com', 'wikipedia.org',
    'bloomberg.com', 'techcrunch.com', 'pitchbook.com',
    'tracxn.com', 'wellfound.com', 'angellist.com',
    'theorg.com', 'cbinsights.com', 'dealroom.co',
    'apnews.com', 'reuters.com',
]

def is_social_or_aggregator(url):
    try:
        domain = urlparse(url).netloc.lower()
        return any(skip in domain for skip in SKIP_DOMAINS)
    except:
        return True

async def search_website(page, company_name):
    query = f"{company_name} startup Seoul official website"
    search_url = f"https://www.bing.com/search?q={quote_plus(query)}"

    try:
        await page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
        await page.wait_for_selector('li.b_algo h2 a', timeout=10000)

        links = await page.query_selector_all('li.b_algo h2 a')

        for link in links:
            href = await link.get_attribute('href')
            if href and not is_social_or_aggregator(href):
                return href
    except Exception as e:
        print(f"  Error searching for {company_name}: {e}")

    return None

async def main():
    json_path = 'c:/Personal/Projects/global_startups/seoul_startups.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        startups = json.load(f)

    missing = [(i, s) for i, s in enumerate(startups) if s.get('Website', '') == '']
    total_missing = len(missing)
    print(f"Total startups: {len(startups)}")
    print(f"Missing websites: {total_missing}")
    print()

    found_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
            locale='en-US',
        )
        page = await context.new_page()
        await stealth_async(page)

        for idx, (orig_idx, startup) in enumerate(missing):
            name = startup['Name']
            print(f"[{idx+1}/{total_missing}] Searching: {name}")

            website = await search_website(page, name)

            if website:
                startups[orig_idx]['Website'] = website
                found_count += 1
                print(f"  Found: {website}")
            else:
                print(f"  Not found")

            # Small delay between searches
            if idx < len(missing) - 1:
                await asyncio.sleep(2)

        await browser.close()

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(startups, f, ensure_ascii=False, indent=2)

    print()
    print(f"=== Results ===")
    print(f"Missing websites: {total_missing}")
    print(f"Websites found:   {found_count}")
    print(f"Still missing:    {total_missing - found_count}")
    print(f"Updated {json_path}")

if __name__ == '__main__':
    asyncio.run(main())
