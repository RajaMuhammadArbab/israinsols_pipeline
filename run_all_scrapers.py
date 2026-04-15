"""
Run all scrapers at once: Fiverr, Upwork, Freelancer, etc.
Scrapes multiple platforms concurrently, saves leads, and sends alerts.

Usage:
    python run_all_scrapers.py
"""
import asyncio
import os
import django
import time
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from leads.scraper.fiverr import FiverrScraper
from leads.scraper.upwork import UpworkScraper
from leads.scraper.freelancer import FreelancerScraper
from leads.tasks import _save_new_leads, _send_single_alert_sync
from leads.models import ScrapedLead

# Platform configurations
PLATFORMS = {
    'fiverr': {
        'queries': [
            'web development',
            'python developer',
            'react developer',
            'wordpress developer',
            'shopify developer',
        ],
        'scraper_class': FiverrScraper,
        'kwargs': {'headless': True, 'max_pages': 3},
    },
    'upwork': {
        'queries': [
            'python django web development',
            'react developer frontend',
            'web scraping automation',
            'shopify developer',
        ],
        'scraper_class': UpworkScraper,
        'kwargs': {
            'headless': True,
            'max_pages': 2,
            'proxy': os.getenv('SCRAPER_PROXY') or None,
        },
    },
    'freelancer': {
        'queries': [
            'python django web development',
            'react developer frontend',
            'web scraping automation python',
            'shopify store setup',
            'mobile app development',
        ],
        'scraper_class': FreelancerScraper,
        'kwargs': {'max_results': 50, 'max_pages': 2},
    },
}


async def scrape_platform(platform_name, config):
    """Scrape one platform with multiple queries."""
    scraper_class = config['scraper_class']
    queries = list(config['queries'])
    kwargs = config.get('kwargs', {})

    random.shuffle(queries)
    all_leads = []
    for query in queries:
        print(f"🔍 {platform_name.upper()}: '{query}'")
        scraper = scraper_class(search_query=query, **kwargs)
        leads = await scraper.scrape()
        print(f"   Found {len(leads)} leads")
        all_leads.extend(leads)

    return all_leads


async def main():
    print("=" * 70)
    print("Multi-Platform Scraper — Scrape All, Save, Alert")
    print("=" * 70)

    # Scrape all platforms concurrently
    tasks = []
    for platform_name, config in PLATFORMS.items():
        task = scrape_platform(platform_name, config)
        tasks.append(task)

    print("🚀 Starting concurrent scraping...")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect all leads
    all_leads = []
    for i, result in enumerate(results):
        platform_name = list(PLATFORMS.keys())[i]
        if isinstance(result, Exception):
            print(f"❌ Error scraping {platform_name}: {result}")
        else:
            all_leads.extend(result)
            print(f"✅ {platform_name.upper()}: {len(result)} leads")

    if not all_leads:
        print("\nNo leads found from any platform. Exiting.")
        return

    # Save and alert synchronously (Django ORM not async-safe)
    from asgiref.sync import sync_to_async
    await sync_to_async(save_leads)(all_leads)


def save_leads(all_leads):
    """Sync function for DB operations (alerts sent automatically in _save_new_leads)"""
    print(f"\n💾 Saving {len(all_leads)} leads to database...")
    result = _save_new_leads(all_leads)
    print(f"   Total scraped:  {result['total']}")
    print(f"   New saved:    {result['saved']}")
    print(f"   Duplicates:   {result['duplicates']}")
    print(f"   Alerts sent:  {result['saved']} (immediate)")

    print(f"\n{'='*50}")
    print("Done! Leads saved and alerts sent automatically.")


if __name__ == '__main__':
    asyncio.run(main())
