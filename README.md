# Israinsols B2B Lead & Market Intel Pipeline

🚀 Automated lead generation system that scrapes freelance platforms, stores leads in PostgreSQL, and sends interactive alerts via Telegram.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Scraping | Playwright (stealth mode) |
| Backend | Django 5.x |
| Database | PostgreSQL |
| Task Queue | Celery + Redis |
| Bot | aiogram 3.x (Telegram) |

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker Desktop (for PostgreSQL & Redis)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### 2. Setup

```bash
# Clone and enter project
cd israinsols_pipeline

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment config
copy .env.example .env         # Windows
# cp .env.example .env         # Linux/Mac

# Edit .env with your settings (especially TELEGRAM_BOT_TOKEN)
# For Railway or other cloud hosting, set DATABASE_URL instead of DB_ENGINE/DB_* values.
```

### 3. Start Infrastructure (Docker)

```bash
# Start PostgreSQL & Redis
docker-compose up -d

# Verify they're running
docker-compose ps
```

### 4. Setup Database

```bash
# Create database tables
python manage.py makemigrations leads
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser
```

### 5. Run Components

```bash
# Terminal 1: Django Admin (open http://localhost:8000/admin)
python manage.py runserver

# Terminal 2: Celery Worker (background task processor)
celery -A config worker -l info

# Terminal 3: Celery Beat (task scheduler)
celery -A config beat -l info

# Terminal 4: Telegram Bot
python manage.py run_bot
```

### 6. Test Scraper Manually

```bash
# Run demo scraper (generates fake leads for testing)
python manage.py run_scraper

# Run with specific scraper
python manage.py run_scraper --type upwork --query "react developer"

# Run with visible browser (debugging)
python manage.py run_scraper --type demo --visible
```

## Architecture

```
Target Websites ──→ Playwright Scraper ──→ PostgreSQL DB ──→ Telegram Bot
                    (Stealth Mode)         (Django ORM)      (aiogram)
                         ↑                                        ↓
                    Celery Worker ←── Celery Beat ←── Redis    User Actions
                    (every 15 min)     (scheduler)    (broker)  (buttons)
```

## Project Structure

```
israinsols_pipeline/
├── config/              # Django settings, Celery config
├── leads/
│   ├── scraper/         # Phase 1: Stealth scraping engine
│   │   ├── stealth.py   # Anti-detection utilities
│   │   ├── base.py      # Abstract base scraper
│   │   ├── upwork.py    # Upwork scraper
│   │   └── agency.py    # Generic agency scraper
│   ├── bot/             # Phase 4: Telegram bot
│   │   ├── handlers.py  # Commands & callbacks
│   │   ├── keyboards.py # Inline buttons
│   │   └── formatters.py # Message formatting
│   ├── models.py        # Phase 2: Database models
│   ├── admin.py         # Django admin dashboard
│   └── tasks.py         # Phase 3: Celery tasks
├── docker-compose.yml   # PostgreSQL + Redis
├── requirements.txt
└── .env.example
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot introduction |
| `/stats` | Pipeline statistics |
| `/recent` | Last 5 leads |
| `/unnotified` | Pending leads |
| `/scrape` | Trigger scraper now |
| `/search <keyword>` | Search leads by tech |
| `/help` | Help guide |

## Django Admin

Access at `http://localhost:8000/admin` after creating a superuser.

Features:
- 📊 Lead dashboard with status badges
- 🔍 Filter by status, source, date
- 📥 Export leads as CSV
- ✅ Bulk status updates

## License

Private - Israinsols
