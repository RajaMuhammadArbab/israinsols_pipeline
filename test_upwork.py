"""
Test Upwork Playwright scraper — real client job postings.
Usage: python test_upwork.py
"""
import asyncio, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from leads.scraper.upwork import UpworkScraper

async def main():
    print("=" * 65)
    print("Upwork Playwright Scraper Test — Real Client Job Postings")
    print("=" * 65)

    scraper = UpworkScraper(
        search_query="python django web development",
        max_pages=1,
        headless=True,
    )

    leads = await scraper.scrape()

    print(f"\n--- RESULT ---")
    print(f"Jobs found: {len(leads)}")

    for i, lead in enumerate(leads[:7], 1):
        skills = lead.get('tech_stack', [])
        skills_str = ', '.join(skills[:5]) if isinstance(skills, list) else skills
        print(f"\n  [{i}] {lead['title'][:65]}")
        print(f"       Budget  : {lead.get('budget') or 'Not specified'}")
        print(f"       Country : {lead.get('client_country') or 'Not specified'}")
        print(f"       Skills  : {skills_str or 'Not specified'}")
        print(f"       Posted  : {lead.get('posted_date', '')}")
        print(f"       URL     : {lead['url'][:75]}")

    if not leads:
        print("\n[!] No jobs found — check debug_upwork_page*.html for what Cloudflare returned")

if __name__ == "__main__":
    asyncio.run(main())
