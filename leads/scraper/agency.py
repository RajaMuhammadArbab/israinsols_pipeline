"""
Israinsols Pipeline - Agency Website Scraper (Phase 1)

Generic scraper for competitor agency websites.
Pricing pages, portfolio pages, ya service pages ko scrape karta hai.

Usage:
    scraper = AgencyScraper(
        target_url="https://competitor-agency.com/services",
        source_name="competitor_xyz"
    )
    leads = await scraper.scrape()
"""
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin

from .base import BaseScraper
from .stealth import random_delay

logger = logging.getLogger('leads.scraper')


class AgencyScraper(BaseScraper):
    """
    Generic Agency Website Scraper.
    
    Yeh scraper kisi bhi website ke service/portfolio/pricing pages se
    data extract karta hai. CSS selectors configurable hain.

    Args:
        target_url: Base URL to scrape
        source_name: Name for this source (stored in DB)
        selectors: Dict of CSS selectors for extracting data
    """

    DEFAULT_SELECTORS = {
        'card': 'article, .service-card, .portfolio-item, .project-card, .card',
        'title': 'h2, h3, h4, .title, .card-title',
        'description': 'p, .description, .card-text, .excerpt',
        'price': '.price, .cost, .budget, .rate, .pricing',
        'tech': '.tag, .tech, .skill, .badge, .label',
        'link': 'a[href]',
    }

    def __init__(
        self,
        target_url: str,
        source_name: str = 'agency',
        selectors: Dict[str, str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.target_url = target_url
        self.source_name = source_name
        self.selectors = selectors or self.DEFAULT_SELECTORS

    def get_target_url(self, page_num: int = 1) -> str:
        """Return the target URL (pagination handled via query param)"""
        if page_num > 1:
            separator = '&' if '?' in self.target_url else '?'
            return f"{self.target_url}{separator}page={page_num}"
        return self.target_url

    async def parse_page(self, page) -> List[Dict[str, Any]]:
        """
        Parse agency website page using configurable CSS selectors.
        Flexible enough to handle most website structures.
        """
        leads = []

        # Wait for content to load
        try:
            await page.wait_for_selector(
                self.selectors['card'],
                timeout=10000
            )
        except Exception:
            logger.warning(f"Content cards not found with selector: {self.selectors['card']}")
            return []

        await random_delay(1, 3)

        # Extract data using JavaScript
        selectors = self.selectors
        base_url = self.target_url

        raw_leads = await page.evaluate("""
            (config) => {
                const leads = [];
                const cards = document.querySelectorAll(config.selectors.card);
                
                cards.forEach(card => {
                    try {
                        // Title
                        const titleEl = card.querySelector(config.selectors.title);
                        const title = titleEl ? titleEl.textContent.trim() : '';
                        
                        // Description
                        const descEl = card.querySelector(config.selectors.description);
                        const description = descEl ? descEl.textContent.trim() : '';
                        
                        // Price/Budget
                        const priceEl = card.querySelector(config.selectors.price);
                        const price = priceEl ? priceEl.textContent.trim() : '';
                        
                        // Tech tags
                        const techEls = card.querySelectorAll(config.selectors.tech);
                        const tech_stack = Array.from(techEls)
                            .map(el => el.textContent.trim())
                            .filter(s => s.length > 0 && s.length < 50);
                        
                        // Link
                        const linkEl = card.querySelector(config.selectors.link);
                        let url = linkEl ? linkEl.href : '';
                        
                        // If no direct link, use current page URL with title as anchor
                        if (!url) {
                            url = window.location.href + '#' + 
                                  title.toLowerCase().replace(/\\s+/g, '-').substring(0, 50);
                        }
                        
                        if (title) {
                            leads.push({
                                title,
                                description: description.substring(0, 1000),
                                budget: price,
                                tech_stack,
                                url,
                                client_name: '',
                                client_country: '',
                                posted_date: '',
                            });
                        }
                    } catch (e) {
                        // Skip card on error
                    }
                });
                
                return leads;
            }
        """, {'selectors': selectors, 'base_url': base_url})

        # Make URLs absolute
        for lead in raw_leads:
            if lead['url'] and not lead['url'].startswith('http'):
                lead['url'] = urljoin(base_url, lead['url'])

        logger.info(f"Parsed {len(raw_leads)} items from agency page")
        return raw_leads
