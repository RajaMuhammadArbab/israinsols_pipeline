"""
Upwork RSS Feed Scraper (No browser, no blocking)
"""
import logging
import feedparser
from urllib.parse import quote_plus
from typing import List, Dict, Any
import aiohttp

logger = logging.getLogger('leads.scraper')


class UpworkRSSScraper:
    """
    Scrapes Upwork jobs using their official RSS feed.
    Uses proper browser headers to avoid blocking.
    """

    def __init__(self, search_query: str = "web development", headless: bool = True, max_pages: int = 2):
        self.search_query = search_query
        self.headless = headless
        self.max_pages = max_pages
        self.source_name = 'upwork_rss'

    async def scrape(self) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed asynchronously"""
        query = quote_plus(self.search_query)
        url = f"https://www.upwork.com/ab/feed/jobs/rss?q={query}&sort=recency"
        
        logger.info(f"Fetching RSS feed for: {self.search_query}")
        
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.upwork.com/',
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"RSS feed returned status {response.status}")
                        return []
                    
                    text = await response.text()
                    # Some RSS feeds come with BOM or encoding issues
                    if text.startswith('\ufeff'):
                        text = text[1:]
                    
                    # Parse the XML
                    feed = feedparser.parse(text)
                    
                    if feed.bozo:
                        logger.warning(f"Feed parsing warning: {feed.bozo_exception}")
                        # Still try to extract entries even if malformed
                    
                    leads = []
                    for entry in feed.entries[:20]:
                        title = entry.get('title', 'No title')
                        link = entry.get('link', '')
                        description = entry.get('description', '')
                        budget = entry.get('upwork_job_budget', 'Not specified')
                        skills = entry.get('upwork_job_skills', '')
                        client_country = entry.get('upwork_client_country', '')
                        posted_date = entry.get('published', '')
                        
                        lead = {
                            'title': title,
                            'url': link,
                            'budget': budget,
                            'description': description[:1000],
                            'tech_stack': skills,
                            'source': 'upwork_rss',
                            'client_country': client_country,
                            'posted_date': posted_date,
                            'client_name': '',
                        }
                        leads.append(lead)
                    
                    logger.info(f"Found {len(leads)} jobs from RSS feed")
                    return leads
                    
            except Exception as e:
                logger.error(f"Failed to fetch RSS feed: {e}")
                return []