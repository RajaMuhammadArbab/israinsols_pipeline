"""Show what's in the database — real vs demo leads."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from leads.models import ScrapedLead
from django.db.models import Count

total = ScrapedLead.objects.count()
by_source = ScrapedLead.objects.values('source').annotate(c=Count('id')).order_by('-c')
by_status = ScrapedLead.objects.values('status').annotate(c=Count('id')).order_by('-c')

print("=" * 70)
print(f"TOTAL LEADS IN DATABASE: {total}")
print("=" * 70)

print("\nBy Source:")
for s in by_source:
    label = s["source"] if s["source"] else "(empty)"
    print(f"  {label:15s} : {s['c']} leads")

print("\nBy Status:")
for s in by_status:
    print(f"  {s['status']:15s} : {s['c']} leads")

# Show 10 REAL Fiverr leads
print("\n" + "=" * 70)
print("SAMPLE REAL FIVERR LEADS (latest 10)")
print("=" * 70)
real = ScrapedLead.objects.exclude(source='demo').order_by('-scraped_at')[:10]
for i, lead in enumerate(real, 1):
    seller = lead.client_name if lead.client_name else "(extracted from URL)"
    print(f"\n--- Lead #{lead.id} ---")
    print(f"  Title   : {lead.title[:70]}")
    print(f"  Seller  : {seller}")
    print(f"  Budget  : {lead.budget}")
    print(f"  Source  : {lead.source}")
    print(f"  Status  : {lead.status}")
    print(f"  URL     : {lead.url[:80]}")
    print(f"  Scraped : {lead.scraped_at}")

# Show 3 DEMO leads for comparison
print("\n" + "=" * 70)
print("SAMPLE DEMO (FAKE) LEADS for comparison")
print("=" * 70)
demo = ScrapedLead.objects.filter(source='demo')[:3]
if not demo:
    print("\n  No demo leads found.")
for lead in demo:
    print(f"\n--- Lead #{lead.id} (FAKE) ---")
    print(f"  Title  : {lead.title[:70]}")
    print(f"  Seller : {lead.client_name}")
    print(f"  Budget : {lead.budget}")
    print(f"  URL    : {lead.url[:80]}")
