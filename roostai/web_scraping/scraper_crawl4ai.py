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


abs_data_path = Path("/home/cc/scraped_data")


class CustomAsyncScraper:
    def __init__(self, max_threads=2):
        self.config = CrawlerRunConfig(cache_mode=CacheMode.DISABLED)
        self.crawler = AsyncWebCrawler()
        self.visited_paths = set()
        self.queue = Queue()
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
        # Increase recursion limit
        sys.setrecursionlimit(10000)

    async def start(self, initial_urls: List[str]):
        # Enqueue initial URLs
        for url in initial_urls:
            await self.queue.put(url)

        await self.crawler.start()

        # Process URLs in batches to prevent deep callback chains
        while not self.queue.empty():
            batch_tasks = []
            # Process up to 10 URLs at a time
            for _ in range(min(10, self.queue.qsize())):
                if self.queue.empty():
                    continue
                url = await self.queue.get()
                batch_tasks.append(self._process_url(url))

            if batch_tasks:
                await asyncio.gather(*batch_tasks)

            # Add a small delay to prevent CPU overload
            await asyncio.sleep(0.1)

        await self.crawler.close()

    async def _process_url(self, url: str):
        url_path = self.clean(url)

        if url_path in self.visited_paths or any(
            url_path.endswith(extension) for extension in self.forbidden_extensions
        ):
            return

        self.visited_paths.add(url_path)
        logger.info(f"Processing URL: {url}")

        try:
            result = await self.crawler.arun(url=url)
            if not result.metadata or not result.markdown or not result.links:
                return

            self._save_to_file(url_path, result)

            # Add new URLs to queue
            for link in result.links["internal"]:
                clean_link = self.clean(link["href"])
                if clean_link not in self.visited_paths:
                    await self.queue.put(link["href"])
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")

    def clean(self, url):
        url_info = urlparse(url)
        url = url_info.netloc + url_info.path
        if url.startswith("www"):
            url = url[4:]
        return url

    def get_url_save_path(self, url_path: str):
        if len(url_path) > 250:
            hashed_url = hashlib.md5(url_path.encode("utf-8")).hexdigest()
            safe_name = url_path.replace("/", "_")[:50]
            file_path = f"{safe_name}_{hashed_url}"
        else:
            url_path = "/".join(url_path.split("#"))
            file_path = Path(url_path.replace("//", "/"))
        return abs_data_path / file_path

    def _save_to_file(self, url_path, result):
        save_path = self.get_url_save_path(url_path)
        os.makedirs(save_path, exist_ok=True)

        markdown = result.markdown
        metadata = result.metadata
        if not markdown or not metadata:
            return

        markdown_file = os.path.join(save_path, "scraped.md")
        metadata_file = os.path.join(save_path, "metadata.json")

        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(result.markdown)

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(result.metadata, f)


async def main():
    initial_urls = ["https://sc.edu"]
    scraper = CustomAsyncScraper()
    await scraper.start(initial_urls)


if __name__ == "__main__":
    asyncio.run(main())
    logger.info("Finished web scraping")
