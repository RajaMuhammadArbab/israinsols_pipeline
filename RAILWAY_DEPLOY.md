# Railway Deployment Guide - Free 24/7 Hosting

## Overview
Railway provides free hosting with Postgres & Redis, perfect for your lead scraper. The app will run 24/7 without your PC.

## Prerequisites
- GitHub account (for easy deployment)
- Railway account: https://railway.app (free tier available)

## Step 1: Prepare Your Code
Your `config/settings.py` now supports `DATABASE_URL`, so Railway's Postgres will work automatically.

## Step 2: Deploy to Railway

### Option A: GitHub Integration (Recommended)
1. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/israinsols_pipeline.git
   git push -u origin main
   ```

2. Go to [Railway.app](https://railway.app) and sign up/login.

3. Click "New Project" → "Deploy from GitHub repo".

4. Select your `israinsols_pipeline` repo.

5. Railway will auto-detect Django and start building.

### Option B: Manual Deploy
1. Create a new project on Railway.
2. Use the Railway CLI if you prefer manual control.

## Step 3: Add Database & Redis

1. In your Railway project dashboard, click "Add Plugin".

2. Add **PostgreSQL** (free tier available).

3. Add **Redis** (free tier available).

4. Railway will automatically set `DATABASE_URL` and `REDIS_URL` environment variables.

## Step 4: Configure Environment Variables

In Railway project settings → Variables, set:

```
DEBUG=False
SECRET_KEY=your-new-secret-key-here
ALLOWED_HOSTS=your-railway-app-url.railway.app

TELEGRAM_BOT_TOKEN=8493340154:AAEROVGaDtRMpr9ADWBSmFTq_onah-8n1qc
TELEGRAM_CHAT_ID=8619429877
TELEGRAM_API_BASE_URL=https://api.telegram.org

SCRAPER_HEADLESS=true
SCRAPER_DELAY_MIN=2
SCRAPER_DELAY_MAX=7
SCRAPER_INTERVAL_MINUTES=15

# Optional: ScraperAPI for Upwork
SCRAPERAPI_KEY=3d24e31cb8c26e94a65508a3356685ee
```

⚠️ **Security Note**: Your current `TELEGRAM_BOT_TOKEN` is leaked in the code. Generate a new one from [@BotFather](https://t.me/BotFather)!

## Step 5: Database Setup

After deployment, run migrations:

1. In Railway project → "Deployments" tab.

2. Click the latest deployment → "Shell" or run command.

3. Execute:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser  # Optional, for admin access
   ```

## Step 6: Configure Background Tasks (Celery)

Railway supports background services. In your project settings:

1. Go to "Services" → Add a new service.

2. Choose "Worker" or "Cron Job" for Celery.

3. Set the start command:
   ```bash
   celery -A config worker --beat -l info
   ```

This runs both Celery worker and beat scheduler in one process.

## Step 7: Test Your Deployment

1. Visit your Railway app URL.

2. Check logs in Railway dashboard.

3. Test the Telegram bot: `/start` command.

4. Monitor scrapers: They should run every 15 minutes automatically.

## Step 8: Monitor & Scale

- **Free Tier Limits**: Railway free tier has usage limits. Monitor your dashboard.
- **Logs**: View real-time logs in Railway.
- **Alerts**: Set up Railway notifications for errors.

## Troubleshooting

### Common Issues:
- **Database Connection**: Ensure `DATABASE_URL` is set correctly.
- **Redis Connection**: Check `REDIS_URL`.
- **Migrations**: Run `python manage.py migrate` if tables are missing.
- **Celery Not Starting**: Verify the worker command in Railway.

### If Scrapers Fail:
- Check Railway logs for errors.
- Test locally first: `python manage.py run_scraper --type demo`

## Cost
- **Free Forever**: Railway's free tier should handle your usage (light scraping + Telegram bot).
- **Upgrade if Needed**: If you hit limits, paid plans start at ~$5/month.

## Security Notes
- Change your `TELEGRAM_BOT_TOKEN` immediately.
- Use Railway's environment variables for secrets.
- Enable Railway's backup for your Postgres database.

---

Your lead scraper will now run 24/7 on Railway! 🎉