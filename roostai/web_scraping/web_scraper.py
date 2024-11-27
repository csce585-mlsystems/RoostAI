import asyncio
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib
import json
import os
import logging
from playwright.async_api import async_playwright

# Base directory for saving scraped data
abs_data_path = Path("/home/cc/scraped_data")

class WebScraper:
    def __init__(self, start_urls, max_concurrent=2):
        self.start_urls = start_urls
        self.domains = [urlparse(start_url).netloc for start_url in start_urls]
        self.visited = set()
        self.html_hashes = set()
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def is_valid(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc.endswith(tuple(self.domains))

    def get_url_save_path(self, url):
        url = '/'.join(url.split('#'))
        url_path = Path(url.replace('//', '/'))
        return abs_data_path / url_path

    def is_unique(self, html_content):
        content_hash = hashlib.md5(html_content.encode()).hexdigest()
        if content_hash in self.html_hashes:
            return False
        self.html_hashes.add(content_hash)
        return True

    async def save_html(self, url, content):
        save_path = self.get_url_save_path(url)
        os.makedirs(save_path, exist_ok=True)
        with open(save_path / "scraped_data.html", "w", encoding="utf-8") as f:
            f.write(content)
        with open(save_path / "metadata.json", "w") as f:
            metadata = {"source_url": f"https://{url}"}
            json.dump(metadata, f)

    async def scrape_page(self, page, url):
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("domcontentloaded")
        html_content = await page.content()

        if self.is_unique(html_content):
            await self.save_html(url, html_content)

        new_urls = []
        links = await page.evaluate("""
            Array.from(document.querySelectorAll('a'))
                 .map(link => link.href)
        """)
        for href in links:
            full_url = urljoin(url, href)
            if self.is_valid(full_url) and full_url not in self.visited:
                new_urls.append(full_url)
        return new_urls

    async def scrape_url(self, url, browser):
        async with self.semaphore:
            try:
                self.logger.info(f"Scraping: {url}")
                context = await browser.new_context()
                page = await context.new_page()
                new_urls = await self.scrape_page(page, url)
                await context.close()
                return new_urls
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                return []

    async def start(self):
        queue = asyncio.Queue()
        for url in self.start_urls:
            queue.put_nowait(url)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            while not queue.empty():
                url = await queue.get()
                if url not in self.visited:  # Process only if not visited
                    self.visited.add(url)  # Mark visited after dequeuing
                    new_urls = await self.scrape_url(url, browser)
                    for new_url in new_urls:
                        if new_url not in self.visited:
                            queue.put_nowait(new_url)  # Add only unvisited URLs
                self.logger.info(f"Queue size: {queue.qsize()}")
            await browser.close()


if __name__ == "__main__":
    start_urls = ["https://sc.edu"]

    scraper = WebScraper(start_urls, max_concurrent=5)
    asyncio.run(scraper.start())
    print("Finished web scraping scripting")
