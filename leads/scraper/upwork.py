"""
Israinsols Pipeline - Upwork Playwright Scraper
════════════════════════════════════════════════
Scrapes Upwork's PUBLIC job search page using Playwright + stealth.
No login required — public jobs are visible without an account.

Target: https://www.upwork.com/nx/search/jobs/?q=python+django&sort=recency
"""
import re
import logging
from typing import List, Dict, Any

from .base import BaseScraper
from .stealth import create_stealth_browser, safe_goto

logger = logging.getLogger('leads.scraper')


class UpworkScraper(BaseScraper):
    """
    Scrapes Upwork job listings via Playwright (public search, no login).
    Uses our existing stealth infrastructure.
    """

    SEARCH_BASE = "https://www.upwork.com/nx/search/jobs/"

    def __init__(
        self,
        search_query: str = "python django web development",
        min_budget: int = 0,
        max_pages: int = 2,
        headless: bool = True,
        **kwargs,
    ):
        super().__init__(headless=headless, max_pages=max_pages, **kwargs)
        self.search_query = search_query
        self.min_budget = min_budget
        self.source_name = 'upwork'

    def get_target_url(self, page_num: int = 1) -> str:
        from urllib.parse import urlencode
        params = {'q': self.search_query, 'sort': 'recency'}
        if page_num > 1:
            params['page'] = page_num
        if self.min_budget:
            params['amount'] = f"{self.min_budget}-"
        return f"{self.SEARCH_BASE}?{urlencode(params)}"

    async def parse_page(self, page) -> List[Dict[str, Any]]:
        """Required by ABC — main logic is in scrape()."""
        return []

    # ─────────────────────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────────────────────
    async def scrape(self) -> List[Dict[str, Any]]:
        import asyncio, random

        # First try browser scraping. If Upwork blocks the browser path, fallback to RSS.
        browser_leads = await self._scrape_with_browser()
        if browser_leads:
            return browser_leads

        logger.info("Falling back to Upwork RSS feed scraper")
        rss_leads = await self._scrape_with_rss()
        logger.info(f"Total Upwork leads scraped via RSS: {len(rss_leads)}")
        return rss_leads

    async def _scrape_with_browser(self) -> List[Dict[str, Any]]:
        import asyncio, random

        all_leads = []

        async with create_stealth_browser(headless=self.headless, proxy=self.proxy) as (browser, context, page):

            # Warmup — visit Upwork homepage first
            logger.info("Warming up session — visiting Upwork homepage...")
            try:
                await page.goto("https://www.upwork.com/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(3, 5))
            except Exception:
                pass
            logger.info("Session warmup complete.")

            for page_num in range(1, self.max_pages + 1):
                url = self.get_target_url(page_num)
                logger.info(f"Scraping Upwork page {page_num}: {url}")

                try:
                    success = await safe_goto(page, url, timeout=45000)
                    if not success:
                        blocked_html = await page.content()
                        if 'Just a moment...' in blocked_html or 'Challenge - Upwork' in blocked_html or 'cdn-cgi/challenge-platform' in blocked_html:
                            logger.warning('Upwork browser access blocked by Cloudflare challenge.')
                        logger.warning(f"Failed to load Upwork page {page_num}; skipping Upwork browser scraping.")
                        return []
                    await asyncio.sleep(random.uniform(3, 5))

                    # Wait for job cards
                    try:
                        await page.wait_for_selector(
                            'article[data-test="JobTile"], [data-test="job-tile"], .up-card-section, .job-tile',
                            timeout=15000
                        )
                        logger.info(f"Job cards detected on page {page_num}")
                    except Exception:
                        logger.warning(f"Job cards not found on page {page_num} — saving debug HTML")
                        html = await page.content()
                        with open(f"debug_upwork_page{page_num}.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        return []

                    # Human scroll
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    await asyncio.sleep(random.uniform(1, 2))
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(random.uniform(2, 3))

                    # Extract jobs via JS
                    jobs = await page.evaluate("""
                    () => {
                        const results = [];

                        // Try multiple card selectors
                        let cards = document.querySelectorAll('article[data-test="JobTile"]');
                        if (!cards.length) cards = document.querySelectorAll('[data-test="job-tile"]');
                        if (!cards.length) cards = document.querySelectorAll('section.up-card-section');
                        if (!cards.length) cards = document.querySelectorAll('[class*="JobTile"]');
                        if (!cards.length) cards = document.querySelectorAll('[class*="js-search-result"]');

                        cards.forEach(card => {
                            try {
                                // Title + URL
                                const titleLink = card.querySelector('a[data-test="job-tile-title-link"], h2 a, h3 a, [class*="title"] a, a[href*="/jobs/"]');
                                if (!titleLink) return;
                                const title = titleLink.innerText.trim();
                                let url = titleLink.href || titleLink.getAttribute('href') || '';
                                if (url && !url.startsWith('http')) url = 'https://www.upwork.com' + url;

                                // Budget
                                const budgetEl = card.querySelector('[data-test="budget"], [class*="budget"], strong[data-test="budget"], .job-type, .job-budget');
                                const budget = budgetEl ? budgetEl.innerText.trim() : '';

                                // Description
                                const descEl = card.querySelector('[data-test="job-description-text"], [class*="description"], .up-card-section__description');
                                const description = descEl ? descEl.innerText.trim().slice(0, 500) : '';

                                // Skills
                                const skillEls = card.querySelectorAll('[data-test="attr-item"], .up-skill-badge, [class*="Skill"] span, [class*="skill"] span, .chips-list span');
                                const skills = Array.from(skillEls).map(s => s.innerText.trim()).filter(Boolean).slice(0, 10);

                                // Posted date
                                const dateEl = card.querySelector('[data-test="posted-on"], time, [class*="posted"]');
                                const posted = dateEl ? (dateEl.getAttribute('datetime') || dateEl.innerText.trim()) : '';

                                // Job type
                                const typeEl = card.querySelector('[data-test="job-type"], [class*="jobType"], .job-type');
                                const jobType = typeEl ? typeEl.innerText.trim() : '';

                                // Client country
                                const countryEl = card.querySelector('[data-test="client-country"], [class*="country"], .client-location');
                                const country = countryEl ? countryEl.innerText.trim() : '';

                                if (title && url) {
                                    results.push({ title, url, budget, description, skills, posted, jobType, country });
                                }
                            } catch(e) {}
                        });

                        return results;
                    }
                    """)

                    logger.info(f"Found {len(jobs)} jobs on page {page_num}")

                    for job in jobs:
                        budget = job.get('budget', '')
                        job_type = job.get('jobType', '')
                        if job_type and budget:
                            budget = f"{job_type}: {budget}"
                        elif job_type:
                            budget = job_type

                        all_leads.append({
                            'title':          job.get('title', ''),
                            'url':            job.get('url', ''),
                            'description':    job.get('description', ''),
                            'budget':         budget,
                            'tech_stack':     job.get('skills', []),
                            'source':         'upwork',
                            'client_country': job.get('country', ''),
                            'posted_date':    job.get('posted', ''),
                            'client_name':    '',
                        })

                    if page_num < self.max_pages:
                        await asyncio.sleep(random.uniform(5, 8))

                except Exception as e:
                    logger.error(f"Error on Upwork page {page_num}: {e}")
                    break

        logger.info(f"Total Upwork leads scraped: {len(all_leads)}")
        return all_leads

    async def _scrape_with_rss(self) -> List[Dict[str, Any]]:
        from .upwork_rss import UpworkRSSScraper

        rss_scraper = UpworkRSSScraper(search_query=self.search_query, max_pages=self.max_pages)
        results = await rss_scraper.scrape()
        leads = []
        for item in results:
            leads.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'description': item.get('description', ''),
                'budget': item.get('budget', ''),
                'tech_stack': item.get('tech_stack', []),
                'source': 'upwork',
                'client_country': item.get('client_country', ''),
                'posted_date': item.get('posted_date', ''),
                'client_name': '',
            })
        return leads

    def transform_lead(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        lead = super().transform_lead(raw)
        lead['source'] = 'upwork'
        if lead.get('budget'):
            lead['budget'] = re.sub(r'\s+', ' ', lead['budget']).strip()
        if isinstance(lead.get('tech_stack'), list):
            lead['tech_stack'] = ', '.join(lead['tech_stack'])
        return lead