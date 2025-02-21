import asyncio
from concurrent.futures import ThreadPoolExecutor
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
from urllib.parse import urlparse
from loguru import logger
import sys
import hashlib
from typing import List, Set
import os
from pathlib import Path
import json

abs_data_path = "/home/cc/scraped_data"


class CustomAsyncScraper:
    def __init__(self, max_threads=1):
        # Configure browser with proper settings
        browser_config = BrowserConfig(
            verbose=True,
        )

        crawler_config = CrawlerRunConfig(
            timeout=30000,  # 30 second timeout
        )

        self.crawler = AsyncWebCrawler(config=browser_config, run_config=crawler_config)

        self.visited_paths: Set[str] = set()
        self.queue = asyncio.Queue()
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
        sys.setrecursionlimit(10000)

    async def start(self, initial_urls: List[str]) -> None:
        try:
            await self.crawler.start()

            for url in initial_urls:
                await self.queue.put(url)

            while not self.queue.empty():
                batch_tasks = []
                batch_size = min(5, self.queue.qsize())

                for _ in range(batch_size):
                    if self.queue.empty():
                        break
                    url = await self.queue.get()
                    batch_tasks.append(self._process_url(url))

                if batch_tasks:
                    try:
                        await asyncio.gather(*batch_tasks, return_exceptions=True)
                    except Exception as e:
                        logger.error(f"Batch processing error: {e}")

                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Scraper error: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        try:
            await self.crawler.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _process_url(self, url: str) -> None:
        url_path = self.clean(url)

        if url_path in self.visited_paths or any(
            url_path.endswith(extension) for extension in self.forbidden_extensions
        ):
            return

        self.visited_paths.add(url_path)
        logger.info(f"Processing URL: {url}")

        try:
            for attempt in range(3):
                try:
                    result = await self.crawler.arun(url=url)
                    if result.success:
                        break
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {result.error_message}"
                    )
                    await asyncio.sleep(1 * (attempt + 1))
                except Exception as e:
                    if attempt == 2:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(1 * (attempt + 1))

            if not result.success:
                logger.error(f"Failed to process {url} after 3 attempts")
                return

            if result.markdown and result.metadata and result.links:
                self._save_to_file(url_path, result)

                for link in result.links["internal"]:
                    clean_link = self.clean(link["href"])
                    if clean_link not in self.visited_paths:
                        await self.queue.put(link["href"])
                        await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")

    def clean(self, url: str) -> str:
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

    def _save_to_file(self, url_path, result) -> None:
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

    try:
        await scraper.start(initial_urls)
    except Exception as e:
        logger.error(f"Main execution error: {e}")
    finally:
        logger.info("Finished web scraping")


if __name__ == "__main__":
    asyncio.run(main())
