"""
Direct Telegram alert test — runs synchronously like Celery does.
Usage: python test_telegram.py
"""
import asyncio
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from leads.models import ScrapedLead
from leads.tasks import _send_single_alert_sync


def main():
    print("=" * 60)
    print("Telegram Alert Test")
    print("=" * 60)

    token   = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    api_base = getattr(settings, 'TELEGRAM_API_BASE_URL', 'https://api.telegram.org')
    proxy    = getattr(settings, 'TELEGRAM_PROXY', '') or 'None'

    print(f"Bot Token : {token[:20]}...")
    print(f"Chat ID   : {chat_id}")
    print(f"API Base  : {api_base}")
    print(f"Proxy     : {proxy}")
    print()

    if not token or not chat_id:
        print("[!] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing in .env!")
        return

    # Get first REAL lead (skip demo source)
    lead = ScrapedLead.objects.filter(
        status=ScrapedLead.Status.UNNOTIFIED
    ).exclude(
        source='demo'
    ).order_by('-scraped_at').first()

    if not lead:
        lead = ScrapedLead.objects.filter(
            status=ScrapedLead.Status.UNNOTIFIED
        ).order_by('-scraped_at').first()

    if not lead:
        print("[!] No unnotified leads in DB. Run test_fiverr.py first.")
        return

    print(f"Sending lead: {lead.title[:60]}")
    print(f"  Source : {lead.source}")
    print(f"  Budget : {lead.budget}")
    print(f"  Seller : {lead.client_name}")
    print(f"  URL    : {lead.url[:70]}")
    print()

    # Direct sync call — no asyncio needed
    success = _send_single_alert_sync(lead)

    if success:
        lead.mark_as_notified()
        print("[OK] Alert sent! Check your Telegram.")
        print("     Lead marked as NOTIFIED in DB.")
    else:
        print("[FAIL] Alert failed.")
        print()
        print("If Telegram is blocked by ISP, do ONE of these:")
        print("  1. Deploy telegram_cf_worker.js to Cloudflare Workers (FREE)")
        print("     Then set in .env: TELEGRAM_API_BASE_URL=https://your-worker.workers.dev")
        print()
        print("  2. Use a VPN/proxy and set in .env:")
        print("     TELEGRAM_PROXY=http://127.0.0.1:7890")


if __name__ == "__main__":
    main()
