import asyncio
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib
import json
import os
import logging
from playwright.async_api import async_playwright, Error as PlaywrightError

# Base directory for saving scraped data
abs_data_path = Path("/home/cc/scraped_data")

# BFS web scraping tool
MAX_RETRIES = 3


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

    def is_valid(self, url: str):
        """Validate that urls only have the root url's (sc.edu) netloc"""
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc.endswith(tuple(self.domains))

    def get_url_save_path(self, url: str):
        """Convert a URL to a file path"""
        colon_index = url.index(":")
        url = url[colon_index + 3 :]  # remove https://

        if len(url) > 250:
            # Use a hash of the URL for long file names
            hashed_url = hashlib.md5(url.encode("utf-8")).hexdigest()

            # Optional: Extract a readable part of the URL (e.g., path or query) for better context
            parsed_url = urlparse(url)
            safe_name = parsed_url.path.replace("/", "_")[:50]  # Truncate and sanitize

            # Combine safe name and hash for uniqueness
            url_path = f"{safe_name}_{hashed_url}"
        else:
            url = "/".join(url.split("#"))
            url_path = Path(url.replace("//", "/"))
        return abs_data_path / url_path

    def remove_http_protocol(self, url: str):
        parsed_url = urlparse(url)
        # Get everything after 'https://' or 'http://'
        return parsed_url.netloc + parsed_url.path

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
        await page.goto(url, timeout=90000)
        await page.wait_for_load_state("load", timeout=60000)
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

        # checks if any element of l is in s
        file_extensions = [
            ".pdf",
            ".docx",
            ".doc",
            ".xlsx",
            ".xls",
            ".zip",
            ".pptx",
            ".jpg",
            ".jpeg",
            ".png",
            ".mov",
        ]

        def ends_with(l, s):
            return any(s.endswith(x) for x in l)

        for href in links:
            full_url: str = urljoin(url, href)  # join a base url and link
            # if valid and not visited, return it
            if (
                self.is_valid(full_url)
                and self.remove_http_protocol(full_url) not in self.visited
                and not full_url.endswith("pdf")
                and not ends_with(file_extensions, full_url)
            ):
                new_urls.append(full_url)
        return new_urls

    async def scrape_url_with_retries(self, url, browser, context):
        for attempt in range(MAX_RETRIES):
            try:
                page = await context.new_page()
                result = await self.scrape_page(page, url)
                await page.close()
                return result
            except PlaywrightError as e:
                self.logger.error(f"Playwright Error for {url} : {e}")
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
                await asyncio.sleep(2**attempt)  # Exponential backoff

        self.logger.error(f"Failed to scrape {url} after {MAX_RETRIES} attempts.")
        return []

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
            except PlaywrightError as e:
                self.logger.error(f"Playwright Error for {url} : {e}")
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                return []

    async def start(self):
        """Run the web scraper"""
        async with async_playwright() as playwright:
            # Launch the browser ONCE at the start
            # browser = await playwright.chromium.launch(headless=True)

            # # Create a single browser context to reuse
            # context = await browser.new_context()
            browser = await playwright.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            )

            queue = asyncio.Queue()
            for url in self.start_urls:
                queue.put_nowait(url)

            try:
                while not queue.empty():
                    url = await queue.get()
                    if self.remove_http_protocol(url) not in self.visited:
                        self.visited.add(self.remove_http_protocol(url))
                        try:
                            # Use the same context for all pages
                            page = await context.new_page()
                            new_urls = await self.scrape_page(page, url)
                            await page.close()  # Close the page, but keep the context open

                            for new_url in new_urls:
                                if (
                                    self.remove_http_protocol(new_url)
                                    not in self.visited
                                ):
                                    queue.put_nowait(new_url)
                        except PlaywrightError as e:
                            self.logger.error(f"Playwright Error for {url} : {e}")
                        except Exception as e:
                            self.logger.error(f"Error scraping {url}: {e}")

                    self.logger.info(f"Queue size: {queue.qsize()}")
            except PlaywrightError as e:
                self.logger.error(f"Playwright Error: {e}")
            except Exception as e:
                self.logger.error(f"Critical error: {e}")
            finally:
                await context.close()
                await browser.close()
                self.logger.info("Browser closed successfully.")


if __name__ == "__main__":
    # scrape USC web data, with 5 crawling threads
    start_urls = ["https://sc.edu"]
    scraper = WebScraper(start_urls, max_concurrent=5)

    # run asynchronous function
    asyncio.run(scraper.start())
    print("Finished web scraping scripting")
