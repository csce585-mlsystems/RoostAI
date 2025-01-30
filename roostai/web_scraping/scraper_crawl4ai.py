import asyncio
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig
from urllib.parse import urlparse
from loguru import logger
import sys
import hashlib
from typing import List
import os
from pathlib import Path
import json

# logger.add(
#     "scraping.log",
#     format="{time} {level} {message}",
#     filter="web_scraper",
#     level="INFO",
# )

abs_data_path = Path("C:\\Users\\2002v\\Desktop\\RoostAI\\roostai\\web_scraping")


class CustomAsyncScraper:
    def __init__(self, max_threads=2):
        self.config = CrawlerRunConfig(cache_mode=CacheMode.DISABLED)
        self.crawler = AsyncWebCrawler()
        self.visited_paths = set()
        self.queue = Queue()  # To manage URLs to scrape
        self.executor = ThreadPoolExecutor(max_threads)
        self.forbidden_extensions = [
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

    async def start(self, initial_urls: List[str]):
        # Enqueue initial URLs
        for url in initial_urls:
            await self.queue.put(url)

        await self.crawler.start()

        # Create tasks to process the queue with a thread pool
        tasks = [
            asyncio.create_task(self._process_queue())
            for _ in range(self.executor._max_workers)
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        await self.crawler.close()

    def get_url_save_path(self, url_path: str):
        """Convert a URL to a file path"""

        if len(url_path) > 250:
            # Use a hash of the URL for long file names
            hashed_url = hashlib.md5(url_path.encode("utf-8")).hexdigest()
            safe_name = url_path.replace("/", "_")[:50]  # Truncate and sanitize
            # Combine safe name and hash for uniqueness
            file_path = f"{safe_name}_{hashed_url}"
        else:
            url_path = "/".join(url_path.split("#"))
            file_path = Path(url_path.replace("//", "/"))
        return abs_data_path / file_path

    def clean(self, url):
        url_info = urlparse(url)
        url = url_info.netloc + url_info.path
        if url.startswith("www"):
            url = url[4:]
        return url

    @logger.catch
    async def _process_queue(self):
        while not self.queue.empty():
            url = await self.queue.get()
            print(f"Url: {url}")
            url_path = self.clean(url)

            if url_path in self.visited_paths or any(
                url_path.endswith(extension) for extension in self.forbidden_extensions
            ):
                continue

            self.visited_paths.add(url_path)
            try:
                # Process the URL using the crawler
                result = await self.crawler.arun(url=url)

                # Save the scraped content (e.g., markdown and etc.)
                self._save_to_file(url_path, result)

                # Enqueue new internal links
                for link in result.links["internal"]:
                    if self.clean(link["href"]) not in self.visited_paths:
                        await self.queue.put(link["href"])
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")

    def _save_to_file(self, url_path, result):
        save_path = self.get_url_save_path(url_path)
        os.makedirs(save_path, exist_ok=True)

        markdown_file = os.path.join(save_path, "scraped.md")
        metadata_file = os.path.join(save_path, "metadata.json")

        # Write content to a markdown file
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(result.markdown)

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(result.metadata, f)


# Example usage
async def main():
    initial_urls = ["https://sc.edu"]

    scraper = CustomAsyncScraper()
    await scraper.start(initial_urls)


if __name__ == "__main__":
    asyncio.run(main())
    logger.info("Finished web scraping")
