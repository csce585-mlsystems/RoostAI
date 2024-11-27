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

# BFS web scraping tool


class WebScraper:
    def __init__(self, start_urls, max_concurrent=2):
        self.start_urls = start_urls
        # scheme://netloc/path/...
        self.domains = [urlparse(start_url).netloc for start_url in start_urls]
        self.visited = set()  # set of visited urls
        self.html_hashes = set()  # set of scraped HTML hashes
        # semaphore defined by max number of threads
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,  # WARNING, ERROR, CRITICAL messages will be logged
            # Timestamp - (Warning/Error/Critical) - STDOUT
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        # sets the name of the logger to be the name of the module
        self.logger = logging.getLogger(__name__)

    def is_valid(self, url):
        """Validate that urls only have the root url's (sc.edu) netloc"""
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc.endswith(tuple(self.domains))

    def get_url_save_path(self, url):
        """Convert a URL to a file path"""
        url = "/".join(url.split("#"))
        url_path = Path(url.replace("//", "/"))
        return abs_data_path / url_path

    def is_unique(self, html_content):
        """Check that the HTML is unique using hashing"""
        content_hash = hashlib.md5(html_content.encode()).hexdigest()
        if content_hash in self.html_hashes:
            return False
        self.html_hashes.add(content_hash)
        return True

    async def save_html(self, url, content):
        """Giving HTML content string, save the HTML content and its metadata to disk"""
        save_path = self.get_url_save_path(url)
        os.makedirs(save_path, exist_ok=True)
        with open(save_path / "scraped_data.html", "w", encoding="utf-8") as f:
            f.write(content)
        with open(save_path / "metadata.json", "w") as f:
            metadata = {"source_url": f"https://{url}"}
            json.dump(metadata, f)

    async def scrape_page(self, page, url):
        """Save the HTML content of the url"""
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("domcontentloaded")
        html_content = await page.content()

        # save HTML if unique file
        if self.is_unique(html_content):
            await self.save_html(url, html_content)

        # get list of links on the HTML page
        new_urls = []
        links = await page.evaluate(
            """
            Array.from(document.querySelectorAll('a'))
                 .map(link => link.href)
        """
        )
        for href in links:
            full_url = urljoin(url, href)  # join a base url and link
            # if valid and not visited, return it
            if self.is_valid(full_url) and full_url not in self.visited:
                new_urls.append(full_url)
        return new_urls

    async def scrape_url(self, url, browser):
        """Scrape given url and return the list of urls on that page"""
        async with self.semaphore:  # cap the maximum number of crawlers
            try:
                self.logger.info(f"Scraping: {url}")
                # create browsing context, think of it as a window
                context = await browser.new_context()
                page = (
                    await context.new_page()
                )  # create new page, think of it as a new tab
                # scrape the HTML and get the list of URLs
                new_urls = await self.scrape_page(page, url)
                await context.close()  # close browsing context
                return new_urls
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                return []

    async def start(self):
        """Run the web scraper"""
        # immediately add starting urls to async queue
        queue = asyncio.Queue()
        for url in self.start_urls:
            queue.put_nowait(url)

        # async playwright session, launching chromium browser
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            # scrape until we have no more URLs left in the queue
            while not queue.empty():
                url = await queue.get()  # retrieve url asynchronously to avoid deadlock
                if url not in self.visited:  # Process only if not visited
                    self.visited.add(url)  # Mark visited after dequeuing
                    # get the set of new urls from the HTML a href tags
                    new_urls = await self.scrape_url(url, browser)
                    # add new urls to queue if not visited previously
                    for new_url in new_urls:
                        if new_url not in self.visited:
                            # Add only unvisited URLs
                            queue.put_nowait(new_url)
                # log the size of the queue
                self.logger.info(f"Queue size: {queue.qsize()}")
            await browser.close()  # close browser after scraping is complete


if __name__ == "__main__":
    # scrape USC web data, with 5 crawling threads
    start_urls = ["https://sc.edu"]
    scraper = WebScraper(start_urls, max_concurrent=5)

    # run asynchronous function
    asyncio.run(scraper.start())
    print("Finished web scraping scripting")
