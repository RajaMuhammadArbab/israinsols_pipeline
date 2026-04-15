"""
Israinsols Pipeline - Telegram Bot Handlers (Phase 4)

Main bot file — aiogram 3.x use karta hai.
Handles:
- /start, /help, /stats, /scrape commands
- Inline button callbacks (Contacted, Rejected, Applied, Undo)
- Lead status updates in database

Usage:
    python manage.py run_bot
"""
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
import asyncio
from datetime import timedelta

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from asgiref.sync import sync_to_async

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import Command, CommandStart

from leads.models import ScrapedLead
from leads.bot.formatters import format_lead_message, format_lead_updated_message, format_stats_message
from leads.bot.keyboards import get_lead_keyboard, get_status_updated_keyboard

logger = logging.getLogger('leads.bot')

router = Router(name='leads_bot')


# ---------- Helper async ORM wrappers ----------
async def get_total_leads():
    return await sync_to_async(ScrapedLead.objects.count)()

async def get_leads_by_status():
    return await sync_to_async(lambda: list(ScrapedLead.objects.values('status').annotate(count=Count('id'))))()

async def get_today_leads_count():
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return await sync_to_async(ScrapedLead.objects.filter(scraped_at__gte=today_start).count)()

async def get_week_leads_count():
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    return await sync_to_async(ScrapedLead.objects.filter(scraped_at__gte=week_start).count)()

async def get_high_value_count():
    leads = await sync_to_async(lambda: list(ScrapedLead.objects.exclude(budget='')))()
    return sum(1 for lead in leads if lead.is_high_value)

async def get_recent_leads(limit=5):
    return await sync_to_async(lambda: list(ScrapedLead.objects.all()[:limit]))()

async def get_unnotified_leads(limit=5):
    return await sync_to_async(lambda: list(ScrapedLead.objects.filter(status=ScrapedLead.Status.UNNOTIFIED)[:limit]))()

async def get_unnotified_count():
    return await sync_to_async(ScrapedLead.objects.filter(status=ScrapedLead.Status.UNNOTIFIED).count)()

async def search_leads(keyword, limit=5):
    q = Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(tech_stack__icontains=keyword)
    return await sync_to_async(lambda: list(ScrapedLead.objects.filter(q)[:limit]))()

async def get_search_total(keyword):
    q = Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(tech_stack__icontains=keyword)
    return await sync_to_async(ScrapedLead.objects.filter(q).count)()

async def get_lead_by_id(lead_id):
    return await sync_to_async(ScrapedLead.objects.get)(id=lead_id)

async def update_lead_status(lead, status_field=None, mark_method=None):
    """Generic async update for lead status using method or direct assignment"""
    if mark_method:
        await sync_to_async(getattr(lead, mark_method))()
    elif status_field:
        lead.status = status_field
        await sync_to_async(lead.save)(update_fields=['status', 'updated_at'])
    else:
        raise ValueError("Provide either status_field or mark_method")


# ---------- COMMAND HANDLERS ----------
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🚀 <b>Israinsols Lead Pipeline Bot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "Main aapko naye leads ka alert deta hoon.\n"
        "Har lead ke sath action buttons honge.\n"
        "\n"
        "<b>Commands:</b>\n"
        "/stats — Pipeline statistics\n"
        "/recent — Last 5 leads dikhao\n"
        "/scrape — Scraper abhi run karo\n"
        "/search &lt;keyword&gt; — Tech se leads search karo\n"
        "/help — Madad\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 Powered by Israinsols",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Help Guide</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "🔹 <b>/stats</b> — Total leads, status breakdown\n"
        "🔹 <b>/recent</b> — Last 5 latest leads with buttons\n"
        "🔹 <b>/search react</b> — 'react' keyword se search\n"
        "🔹 <b>/scrape</b> — Scraper manually trigger karo\n"
        "🔹 <b>/unnotified</b> — Abhi tak na bheje gaye leads\n"
        "\n"
        "<b>Button Actions:</b>\n"
        "🚀 Apply Now → Job URL open hota hai\n"
        "✅ Contacted → Status: Contacted ho jayega\n"
        "❌ Irrelevant → Lead reject ho jayegi\n"
        "🟣 Applied → Applied mark ho jayega\n"
        "↩️ Undo → Wapis unnotified kar do\n",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command('stats'))
async def cmd_stats(message: Message):
    # Gather stats using async wrappers
    total = await get_total_leads()
    status_counts = await get_leads_by_status()
    today_count = await get_today_leads_count()
    week_count = await get_week_leads_count()
    high_value = await get_high_value_count()

    stats = {
        'total': total,
        'unnotified': 0,
        'notified': 0,
        'contacted': 0,
        'applied': 0,
        'rejected': 0,
        'today': today_count,
        'this_week': week_count,
        'high_value': high_value,
    }
    for item in status_counts:
        stats[item['status']] = item['count']

    await message.answer(
        format_stats_message(stats),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command('recent'))
async def cmd_recent(message: Message):
    leads = await get_recent_leads(5)
    if not leads:
        await message.answer("📭 Koi lead abhi tak nahi mili.")
        return

    for lead in leads:
        text = format_lead_message(lead)
        keyboard = get_lead_keyboard(lead.id, lead.url)
        await message.answer(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.to_aiogram_markup(),
        )
        await asyncio.sleep(0.5)


@router.message(Command('unnotified'))
async def cmd_unnotified(message: Message):
    leads = await get_unnotified_leads(5)
    if not leads:
        await message.answer("✅ Sab leads notify ho chuki hain!")
        return

    total_count = await get_unnotified_count()
    await message.answer(
        f"🔵 <b>{total_count} Unnotified Leads</b> (showing first 5):",
        parse_mode=ParseMode.HTML,
    )

    for lead in leads:
        text = format_lead_message(lead)
        keyboard = get_lead_keyboard(lead.id, lead.url)
        await message.answer(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.to_aiogram_markup(),
        )
        await asyncio.sleep(0.5)


@router.message(Command('scrape'))
async def cmd_scrape(message: Message):
    await message.answer(
        "⏳ Scraper start ho raha hai... (Demo mode)\n"
        "Results kuch seconds mein aayenge.",
        parse_mode=ParseMode.HTML,
    )

    try:
        from leads.tasks import run_scraper_task
        result = run_scraper_task.delay('demo')
        await message.answer(
            f"🤖 Scraper task queued!\nTask ID: <code>{result.id}</code>\nNaye leads automatically alert honge.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.warning(f"Celery not available, running directly: {e}")
        await message.answer("⚠️ Celery not running. Running scraper directly...", parse_mode=ParseMode.HTML)
        try:
            from leads.scraper.base import DemoScraper
            from leads.tasks import _save_new_leads
            scraper = DemoScraper(headless=True)
            leads_data = await scraper.scrape()
            result = _save_new_leads(leads_data)  # This is sync, but fine for demo
            await message.answer(
                f"✅ Scraping complete!\n📋 Found: {result['total']}\n💾 New: {result['saved']}\n🔄 Duplicates: {result['duplicates']}",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e2:
            await message.answer(f"❌ Error: {e2}", parse_mode=ParseMode.HTML)


@router.message(Command('search'))
async def cmd_search(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /search <keyword>\nExample: /search react", parse_mode=ParseMode.HTML)
        return

    keyword = parts[1].strip()
    leads = await search_leads(keyword, 5)
    if not leads:
        await message.answer(f"🔍 '{keyword}' ke liye koi lead nahi mili.")
        return

    total = await get_search_total(keyword)
    await message.answer(
        f"🔍 <b>'{keyword}' ke liye {total} leads mili</b> (showing 5):",
        parse_mode=ParseMode.HTML,
    )

    for lead in leads:
        text = format_lead_message(lead)
        keyboard = get_lead_keyboard(lead.id, lead.url)
        await message.answer(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.to_aiogram_markup(),
        )
        await asyncio.sleep(0.5)


# ---------- CALLBACK HANDLERS ----------
@router.callback_query(F.data.startswith('contacted:'))
async def callback_contacted(callback: CallbackQuery):
    lead_id = int(callback.data.split(':')[1])
    try:
        lead = await get_lead_by_id(lead_id)
        await update_lead_status(lead, mark_method='mark_as_contacted')
        updated_text = format_lead_updated_message(lead, 'contacted')
        keyboard = get_status_updated_keyboard(lead.id, lead.url)
        await callback.message.edit_text(
            updated_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.to_aiogram_markup(),
        )
        await callback.answer("✅ Marked as Contacted!")
    except ScrapedLead.DoesNotExist:
        await callback.answer("❌ Lead not found!", show_alert=True)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer(f"Error: {str(e)[:50]}", show_alert=True)


@router.callback_query(F.data.startswith('reject:'))
async def callback_reject(callback: CallbackQuery):
    lead_id = int(callback.data.split(':')[1])
    try:
        lead = await get_lead_by_id(lead_id)
        await update_lead_status(lead, mark_method='mark_as_rejected')
        updated_text = format_lead_updated_message(lead, 'rejected')
        keyboard = get_status_updated_keyboard(lead.id, lead.url)
        await callback.message.edit_text(
            updated_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.to_aiogram_markup(),
        )
        await callback.answer("❌ Marked as Irrelevant!")
    except ScrapedLead.DoesNotExist:
        await callback.answer("❌ Lead not found!", show_alert=True)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer(f"Error: {str(e)[:50]}", show_alert=True)


@router.callback_query(F.data.startswith('applied:'))
async def callback_applied(callback: CallbackQuery):
    lead_id = int(callback.data.split(':')[1])
    try:
        lead = await get_lead_by_id(lead_id)
        await update_lead_status(lead, mark_method='mark_as_applied')
        updated_text = format_lead_updated_message(lead, 'applied')
        keyboard = get_status_updated_keyboard(lead.id, lead.url)
        await callback.message.edit_text(
            updated_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.to_aiogram_markup(),
        )
        await callback.answer("🟣 Marked as Applied!")
    except ScrapedLead.DoesNotExist:
        await callback.answer("❌ Lead not found!", show_alert=True)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer(f"Error: {str(e)[:50]}", show_alert=True)


@router.callback_query(F.data.startswith('undo:'))
async def callback_undo(callback: CallbackQuery):
    lead_id = int(callback.data.split(':')[1])
    try:
        lead = await get_lead_by_id(lead_id)
        await update_lead_status(lead, status_field=ScrapedLead.Status.UNNOTIFIED)
        text = format_lead_message(lead)
        keyboard = get_lead_keyboard(lead.id, lead.url)
        await callback.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.to_aiogram_markup(),
        )
        await callback.answer("↩️ Status reset to Unnotified!")
    except ScrapedLead.DoesNotExist:
        await callback.answer("❌ Lead not found!", show_alert=True)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer(f"Error: {str(e)[:50]}", show_alert=True)


@router.callback_query(F.data.startswith('note:'))
async def callback_note(callback: CallbackQuery):
    await callback.answer(
        "📝 Note feature coming soon!\nAbhi ke liye Django Admin mein notes add karein.",
        show_alert=True,
    )


# ---------- BOT STARTUP ----------
async def start_bot():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == 'your-telegram-bot-token-from-botfather':
        logger.error(
            "❌ TELEGRAM_BOT_TOKEN not configured!\n"
            "   1. Go to @BotFather on Telegram\n"
            "   2. Create a new bot with /newbot\n"
            "   3. Copy the token to your .env file"
        )
        return

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Bot start karo"),
        BotCommand(command="stats", description="📊 Pipeline statistics"),
        BotCommand(command="recent", description="📋 Last 5 leads"),
        BotCommand(command="unnotified", description="🔵 Unnotified leads"),
        BotCommand(command="scrape", description="🤖 Scraper run karo"),
        BotCommand(command="search", description="🔍 Search leads"),
        BotCommand(command="help", description="📖 Help guide"),
    ])

    logger.info("🤖 Israinsols Bot starting...")
    print("=" * 50)
    print("🤖 ISRAINSOLS TELEGRAM BOT IS RUNNING!")
    print("=" * 50)
    print(f"Bot token: {token[:10]}...{token[-5:]}")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:
        await dp.start_polling(bot, allowed_updates=['message', 'callback_query'])
    finally:
        await bot.session.close()


def run_bot():
    asyncio.run(start_bot())


if __name__ == '__main__':
    run_bot()