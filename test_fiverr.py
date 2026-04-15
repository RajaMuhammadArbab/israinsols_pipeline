"""
Quick test — run this to verify the PerimeterX bypass works.
Usage: python test_fiverr.py
"""
import asyncio
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from leads.scraper.fiverr import FiverrScraper


async def main():
    print("=" * 60)
    print("Fiverr PX Bypass Test")
    print("=" * 60)

    scraper = FiverrScraper(
        search_query="python web development",
        headless=True,   # set False to watch the browser live
        max_pages=1,
    )

    leads = await scraper.scrape()

    print(f"\n--- RESULT ---")
    print(f"Leads found: {len(leads)}")

    for i, lead in enumerate(leads[:5], 1):
        title  = lead.get("title", "")[:65]
        budget = lead.get("budget", "N/A")
        seller = lead.get("seller") or lead.get("client_name") or "unknown"
        rating = lead.get("rating", "")
        print(f"  [{i}] {title}")
        print(f"       Seller: {seller} | Budget: {budget} | Rating: {rating}")

    if not leads:
        print("\n[!] No leads scraped.")
        import pathlib
        debug_files = list(pathlib.Path(".").glob("debug_fiverr_*.html"))
        if debug_files:
            print(f"    Debug HTML saved: {[str(f) for f in debug_files]}")
            print("    Open the HTML in a browser to inspect what Fiverr returned.")
        else:
            print("    No debug file either — check the logs above for errors.")


if __name__ == "__main__":
    asyncio.run(main())
