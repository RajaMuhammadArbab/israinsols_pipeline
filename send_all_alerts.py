"""
Send ALL unnotified leads to Telegram in one batch.
Usage: python send_all_alerts.py
"""
import os, django, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from leads.models import ScrapedLead
from leads.tasks import _send_single_alert_sync

leads = ScrapedLead.objects.filter(
    status=ScrapedLead.Status.UNNOTIFIED
).order_by('scraped_at')

total = leads.count()
print(f"Sending {total} unnotified leads to Telegram...\n")

sent = failed = 0
for i, lead in enumerate(leads, 1):
    print(f"[{i}/{total}] {lead.title[:60]}")
    success = _send_single_alert_sync(lead)
    if success:
        lead.mark_as_notified()
        sent += 1
        print(f"  ✅ Sent | Budget: {lead.budget}")
    else:
        failed += 1
        print(f"  ❌ Failed")
    # 1 sec delay between sends to avoid Telegram rate limit (30 msg/sec limit)
    if i < total:
        time.sleep(1)

print(f"\n{'='*50}")
print(f"Done! Sent: {sent} | Failed: {failed} | Total: {total}")
