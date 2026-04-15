"""
Django Management Command: run_scraper

Usage:
    python manage.py run_scraper                          # Demo scraper (testing)
    python manage.py run_scraper --type upwork --query "react developer"
    python manage.py run_scraper --type upwork_rss --query "python developer"
    python manage.py run_scraper --type fiverr --query "react developer"
    python manage.py run_scraper --type agency --url "https://example.com/services"
"""
import os
import sys
import io
import logging
import asyncio
from django.core.management.base import BaseCommand

# ============================================================
# FORCE UTF-8 FOR CONSOLE AND LOGGING (Fixes UnicodeEncodeError)
# ============================================================
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
root_logger.addHandler(console_handler)
root_logger.setLevel(logging.INFO)

os.environ['PYTHONUTF8'] = '1'
# ============================================================


class Command(BaseCommand):
    help = 'Run the lead scraper manually'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='demo',
            choices=['demo', 'upwork', 'upwork_rss', 'fiverr', 'freelancer', 'agency'],
            help='Scraper type (default: demo)',
        )
        parser.add_argument(
            '--query',
            type=str,
            default='web development',
            help='Search query for Upwork/RSS/Fiverr scraper',
        )
        parser.add_argument(
            '--url',
            type=str,
            default='',
            help='Target URL for agency scraper',
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=2,
            help='Max pages (for browser-based scrapers)',
        )
        parser.add_argument(
            '--visible',
            action='store_true',
            help='Run browser in visible mode (only for browser scrapers)',
        )

    def handle(self, *args, **options):
        scraper_type = options['type']
        headless = not options['visible']

        self.stdout.write(self.style.WARNING(
            f"\n🤖 Starting {scraper_type} scraper...\n"
        ))

        if scraper_type == 'demo':
            from leads.scraper.base import DemoScraper
            scraper = DemoScraper(
                headless=headless,
                max_pages=options['pages'],
            )
        elif scraper_type == 'upwork':
            from leads.scraper.upwork import UpworkScraper
            scraper = UpworkScraper(
                search_query=options['query'],
                headless=headless,
                max_pages=options['pages'],
            )
        elif scraper_type == 'upwork_rss':
            from leads.scraper.upwork_rss import UpworkRSSScraper
            scraper = UpworkRSSScraper(
                search_query=options['query'],
            )
        elif scraper_type == 'fiverr':
            from leads.scraper.fiverr import FiverrScraper
            scraper = FiverrScraper(
                search_query=options['query'],
                headless=headless,
                max_pages=options['pages'],
            )
        elif scraper_type == 'freelancer':
            from leads.scraper.freelancer import FreelancerScraper
            scraper = FreelancerScraper(
                search_query=options['query'],
                max_results=50,
                headless=headless,
            )
        elif scraper_type == 'agency':
            if not options['url']:
                self.stderr.write(self.style.ERROR(
                    "❌ --url required for agency scraper!"
                ))
                return
            from leads.scraper.agency import AgencyScraper
            scraper = AgencyScraper(
                target_url=options['url'],
                headless=headless,
                max_pages=options['pages'],
            )

        # Run scraper (async)
        leads_data = asyncio.run(scraper.scrape())

        self.stdout.write(f"\n📋 Found {len(leads_data)} leads\n")

        # Save to database
        from leads.tasks import _save_new_leads
        result = _save_new_leads(leads_data)

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Results:\n"
            f"   Total found:  {result['total']}\n"
            f"   New saved:    {result['saved']}\n"
            f"   Duplicates:   {result['duplicates']}\n"
        ))

        # Show saved leads
        if result['saved'] > 0:
            from leads.models import ScrapedLead
            recent = ScrapedLead.objects.filter(
                status=ScrapedLead.Status.UNNOTIFIED
            )[:result['saved']]

            self.stdout.write("\n📋 Newly saved leads:")
            for lead in recent:
                self.stdout.write(
                    f"  • {lead.title[:60]}"
                    f" | {lead.budget or 'No budget'}"
                    f" | {lead.tech_stack_display or 'No tech'}"
                )