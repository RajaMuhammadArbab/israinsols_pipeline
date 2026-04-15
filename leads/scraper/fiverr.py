"""
Israinsols Pipeline - Fiverr Gig Scraper (PerimeterX Bypass Edition)

Anti-detection layers:
1. Full stealth JS patches (webdriver, plugins, chrome runtime, etc.)
2. Session warmup  — visit homepage first, then search (like a real user)
3. Human mouse movement simulation across the page
4. Up-to-date Chrome 124 User-Agents (no headless string leakage)
5. No resource blocking (PX checks what a real browser loads)
6. Cookie persistence across page navigations
7. Realistic HTTP accept-language & sec-ch-ua headers
"""
import re
import os
import json
import logging
import asyncio
import random
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import quote_plus
from playwright.async_api import async_playwright

from .base import BaseScraper
from .stealth import apply_stealth_scripts

logger = logging.getLogger('leads.scraper')

# ── Cookies cache path (keeps session alive between runs) ──────────────────────
_COOKIES_PATH = Path(__file__).parent / "fiverr_cookies.json"


# ── Updated, realistic Chrome 124 User-Agents ─────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

_VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1366, 'height': 768},
]


class FiverrScraper(BaseScraper):
    def __init__(
        self,
        search_query: str = "web development",
        headless: bool = True,
        max_pages: int = 2,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.search_query = search_query
        self.headless = headless
        self.max_pages = max_pages
        self.source_name = 'fiverr'

    # ── Required by BaseScraper interface ────────────────────────────────────
    async def parse_page(self, page):
        return []

    def get_target_url(self, page_num: int = 1) -> str:
        base_url = "https://www.fiverr.com/search/gigs"
        query = quote_plus(self.search_query)
        return f"{base_url}?query={query}" if page_num == 1 else f"{base_url}?query={query}&page={page_num}"

    # ── Human-like helpers ────────────────────────────────────────────────────
    async def _random_delay(self, min_sec=1.5, max_sec=4.0):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _simulate_mouse_movement(self, page):
        """Move mouse in natural arcs across the page — PX tracks mouse entropy."""
        vw = page.viewport_size.get('width', 1366) if page.viewport_size else 1366
        vh = page.viewport_size.get('height', 768) if page.viewport_size else 768
        points = [
            (random.randint(100, vw - 100), random.randint(100, vh - 100))
            for _ in range(random.randint(4, 8))
        ]
        for x, y in points:
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.08, 0.25))

    async def _human_scroll(self, page):
        """Scroll in small increments, pause, scroll back a bit — like a real reader."""
        total_height = await page.evaluate("document.body.scrollHeight")
        vh = page.viewport_size.get('height', 768) if page.viewport_size else 768
        current = 0
        while current < total_height:
            step = random.randint(250, vh)
            current = min(current + step, total_height)
            await page.evaluate(f"window.scrollTo({{top: {current}, behavior: 'smooth'}})")
            await asyncio.sleep(random.uniform(0.4, 1.1))
        # Scroll back up slightly (humans do this)
        await page.evaluate(f"window.scrollTo({{top: {random.randint(0, 400)}, behavior: 'smooth'}})")
        await asyncio.sleep(random.uniform(0.5, 1.2))

    # ── Cookie persistence ────────────────────────────────────────────────────
    async def _load_cookies(self, context):
        if _COOKIES_PATH.exists():
            try:
                cookies = json.loads(_COOKIES_PATH.read_text(encoding='utf-8'))
                await context.add_cookies(cookies)
                logger.info("Loaded saved Fiverr cookies.")
            except Exception as e:
                logger.warning(f"Could not load cookies: {e}")

    async def _save_cookies(self, context):
        try:
            cookies = await context.cookies()
            _COOKIES_PATH.write_text(json.dumps(cookies, indent=2), encoding='utf-8')
            logger.info("Saved Fiverr cookies for next session.")
        except Exception as e:
            logger.warning(f"Could not save cookies: {e}")

    # ── Session warmup ────────────────────────────────────────────────────────
    async def _warmup_session(self, page):
        """
        Visit Fiverr homepage first so PX builds a legitimate session history.
        PX grants higher trust to sessions that browsed before searching.
        """
        logger.info("Warming up session — visiting Fiverr homepage...")
        try:
            await page.goto("https://www.fiverr.com/", wait_until='domcontentloaded', timeout=45000)
            await self._random_delay(3, 6)
            await self._simulate_mouse_movement(page)
            await self._human_scroll(page)
            await self._random_delay(2, 4)
            logger.info("Session warmup complete.")
        except Exception as e:
            logger.warning(f"Warmup failed (non-fatal): {e}")

    # ── Extra stealth init script (PX-specific patches) ──────────────────────
    async def _apply_px_stealth(self, page):
        await page.add_init_script("""
            // Remove webdriver flag
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            // Realistic plugins (Chrome has 3 by default)
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
                ]
            });

            // Realistic languages
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

            // Hardware fingerprints (consistent with a mid-range PC)
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });

            // Chrome runtime object (headless Chrome lacks this)
            if (!window.chrome) {
                window.chrome = {
                    runtime: {
                        id: undefined,
                        onMessage: { addListener: () => {} },
                        sendMessage: () => {}
                    },
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: { isInstalled: false }
                };
            }

            // Permissions API — PX tests this
            const _origQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (params) => {
                if (params.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return _origQuery(params);
            };

            // WebGL vendor — headless has "Google SwiftShader"
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';    // UNMASKED_VENDOR_WEBGL
                if (parameter === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
                return getParameter.call(this, parameter);
            };

            // Connection type (headless may report none)
            Object.defineProperty(navigator, 'connection', {
                get: () => ({ effectiveType: '4g', rtt: 50, downlink: 10, saveData: false })
            });
        """)

    # ── Gig data extraction ───────────────────────────────────────────────────
    async def _extract_gigs(self, page) -> List[Dict]:
        return await page.evaluate("""
            () => {
                const gigs = [];

                // Primary: Fiverr's stable class name discovered via DOM analysis
                // Fallback chain for future Fiverr updates
                const containerSelectors = [
                    '.gig-wrapper-impressions',   // outer wrapper (most reliable)
                    '.basic-gig-card',             // inner card
                    '.gig-card-layout',
                    '[class*="gig-wrapper"]',
                    '[class*="gig-card"]',
                    'article',
                ];

                let cards = [];
                for (const sel of containerSelectors) {
                    cards = document.querySelectorAll(sel);
                    // Filter out nested duplicates — only top-level cards
                    if (cards.length > 0) {
                        cards = Array.from(cards).filter(el =>
                            !el.closest(sel.trim()) || el === el.closest(sel.trim())
                        );
                        break;
                    }
                }

                cards.forEach(card => {
                    try {
                        // ── Title & URL ──────────────────────────────────────
                        // p.gig-header > a._6528e8 (confirmed from DOM)
                        let titleEl = card.querySelector('p.gig-header');
                        if (!titleEl) titleEl = card.querySelector('[class*="gig-header"]');
                        const title = titleEl ? titleEl.innerText.trim() : '';

                        // Gig link — the anchor wrapping the gig header
                        let linkEl = card.querySelector('a._6528e8') ||
                                     card.querySelector('a[href*="/gig/"]') ||
                                     (titleEl ? titleEl.closest('a') : null) ||
                                     (titleEl ? titleEl.querySelector('a') : null);
                        let url = linkEl ? linkEl.href : '';

                        // ── Price ────────────────────────────────────────────
                        // a._0ed0fc contains "From PKR 35,144" or "From $X"
                        const priceEl = card.querySelector('a._0ed0fc') ||
                                        card.querySelector('[class*="price"]') ||
                                        card.querySelector('[class*="starting-at"]');
                        const price = priceEl ? priceEl.innerText.trim() : '';

                        // ── Seller name ──────────────────────────────────────
                        // figure[title] holds the seller name as an attribute.
                        // Multiple fallbacks since React lazy-renders the avatar.
                        let seller = '';
                        // 1. figure[title] — avatar element (set in SSR)
                        const avatar = card.querySelector('figure[title]');
                        if (avatar) seller = avatar.getAttribute('title').trim();
                        // 2. img[alt] on avatar image
                        if (!seller) {
                            const avatarImg = card.querySelector('figure img[alt]');
                            if (avatarImg) seller = avatarImg.getAttribute('alt').trim();
                        }
                        // 3. Seller profile anchor text (text-bold class = seller link)
                        if (!seller) {
                            const boldAnchor = card.querySelector('a.text-bold');
                            if (boldAnchor) seller = boldAnchor.innerText.trim();
                        }
                        // 4. Extract username from gig URL — always present
                        // Gig URLs are like: /username/gig-slug
                        if (!seller && url) {
                            const parts = (new URL(url)).pathname.split('/').filter(Boolean);
                            if (parts.length >= 2) seller = parts[0];  // username segment
                        }

                        // ── Rating ───────────────────────────────────────────
                        const scoreEl  = card.querySelector('strong.rating-score') ||
                                         card.querySelector('[class*="rating-score"]');
                        const countEl  = card.querySelector('span.ratings-count') ||
                                         card.querySelector('[class*="ratings-count"]');
                        const rating = scoreEl
                            ? `${scoreEl.innerText.trim()} ${countEl ? countEl.innerText.trim() : ''}`.trim()
                            : '';

                        // ── Delivery / extras ────────────────────────────────
                        const deliveryEl = card.querySelector('[class*="delivery"]');
                        const delivery = deliveryEl ? deliveryEl.innerText.trim() : '';

                        // ── Tags / skills ────────────────────────────────────
                        const tags = Array.from(
                            card.querySelectorAll('[class*="tag"], [class*="skill"]')
                        ).map(el => el.innerText.trim())
                         .filter(t => t.length > 0 && t.length < 50);

                        if (title) {
                            gigs.push({ title, url, budget: price, seller, rating, delivery, tags });
                        }
                    } catch(e) {}
                });
                return gigs;
            }
        """)

    # ── Main scrape method ────────────────────────────────────────────────────
    async def scrape(self) -> List[Dict[str, Any]]:
        all_leads = []

        async with async_playwright() as p:
            ua = random.choice(_USER_AGENTS)
            viewport = random.choice(_VIEWPORTS)

            # sec-ch-ua headers must match the UA version (PX cross-checks these)
            ch_ua_version = re.search(r'Chrome/(\d+)', ua)
            ch_ua_ver = ch_ua_version.group(1) if ch_ua_version else "124"
            brand_header = f'"Chromium";v="{ch_ua_ver}", "Google Chrome";v="{ch_ua_ver}", "Not-A.Brand";v="99"'

            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    f'--window-size={viewport["width"]},{viewport["height"]}',
                ]
            )

            context = await browser.new_context(
                user_agent=ua,
                viewport=viewport,
                locale='en-US',
                timezone_id='America/New_York',
                color_scheme='light',
                java_script_enabled=True,
                has_touch=False,
                is_mobile=False,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'sec-ch-ua': brand_header,
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'Upgrade-Insecure-Requests': '1',
                    'DNT': '1',
                }
            )

            # Restore cookies from previous session
            await self._load_cookies(context)

            page = await context.new_page()

            # Apply all stealth patches before any navigation
            await self._apply_px_stealth(page)

            # Warm up the session with a homepage visit
            await self._warmup_session(page)

            # Save cookies after warmup (PX sets trust cookies here)
            await self._save_cookies(context)

            for page_num in range(1, self.max_pages + 1):
                url = self.get_target_url(page_num)
                logger.info(f"Scraping Fiverr page {page_num}: {url}")

                try:
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                    if response and response.status == 403:
                        logger.error("Fiverr returned 403 — still blocked. Try rotating IP/proxy.")
                        break

                    await self._random_delay(3, 6)
                    await self._simulate_mouse_movement(page)

                    # Check for PX challenge page
                    page_title = await page.title()
                    page_url = page.url
                    if 'px' in page_url.lower() or 'human' in page_title.lower() or 'challenge' in page_title.lower():
                        logger.error(f"PX challenge detected on page {page_num}. Saving debug HTML.")
                        html = await page.content()
                        with open(f"debug_fiverr_px_page{page_num}.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        break

                    # Wait for confirmed gig card class (discovered from DOM analysis)
                    try:
                        await page.wait_for_selector(
                            '.gig-wrapper-impressions, .basic-gig-card, .gig-card-layout',
                            timeout=25000
                        )
                        logger.info(f"Gig cards detected on page {page_num}")
                    except Exception:
                        logger.warning(f"Gig selector not found on page {page_num} — trying anyway")

                    # Extra wait for React to fully hydrate lazy-loaded cards
                    await self._random_delay(3, 5)
                    await self._human_scroll(page)
                    await self._random_delay(2, 3)

                    # Extract gigs
                    gigs_data = await self._extract_gigs(page)

                    # Fix relative URLs
                    for gig in gigs_data:
                        if gig.get('url') and not gig['url'].startswith('http'):
                            gig['url'] = f"https://www.fiverr.com{gig['url']}"

                    logger.info(f"Found {len(gigs_data)} gigs on page {page_num}")
                    all_leads.extend(gigs_data)

                    # Save debug if nothing found
                    if page_num == 1 and len(gigs_data) == 0:
                        html = await page.content()
                        with open("debug_fiverr_no_results.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        logger.warning("No gigs found — saved debug_fiverr_no_results.html")

                except Exception as e:
                    logger.error(f"Error on page {page_num}: {e}")
                    break

                # Save cookies after every page (PX refreshes trust tokens)
                await self._save_cookies(context)

                # Longer human-like delay between pages
                if page_num < self.max_pages:
                    await self._random_delay(6, 12)

            await browser.close()

        logger.info(f"Total Fiverr leads scraped: {len(all_leads)}")
        return all_leads

    # ── Lead transformer ──────────────────────────────────────────────────────
    def transform_lead(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        lead = super().transform_lead(raw)
        lead['source'] = 'fiverr'
        if lead.get('budget'):
            lead['budget'] = re.sub(r'\s+', ' ', lead['budget']).strip()
        if isinstance(lead.get('tech_stack'), list):
            lead['tech_stack'] = ', '.join(lead['tech_stack'])
        # Map gig-specific fields
        if not lead.get('description') and raw.get('seller'):
            rating = raw.get('rating', '')
            delivery = raw.get('delivery', '')
            lead['description'] = f"Seller: {raw['seller']} | Rating: {rating} | Delivery: {delivery}"
        if not lead.get('client_name') and raw.get('seller'):
            lead['client_name'] = raw['seller']
        if not lead.get('tech_stack') and raw.get('tags'):
            lead['tech_stack'] = ', '.join(raw['tags']) if isinstance(raw['tags'], list) else raw['tags']
        return lead