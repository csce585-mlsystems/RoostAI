import asyncio

# from crawl4ai import RateLimitConfig
from crawl4ai import AsyncWebCrawler, WebCrawler
from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig

from collections import deque
from urllib.parse import urljoin, urlparse
import pprint

# domain = "sc.edu"
# visited = set()


def clean(url):

    url_info = urlparse(url)
    url = url_info.netloc + url_info.path
    if url.startswith("www"):
        url = url[4:]
    return url


url = "https://www.sc.edu/uofsc/posts/2020/05/library_journal_movers_shakers.php/"
url = "https://" + clean(url)

# # TODO, incorporate all previous checking logic for exploring a website
# # TODO, figure out how to incorporate BFS logic and multiple scrapers
# # TODO, multiple scraper method would need to be thread safe


async def main():
    crawler = AsyncWebCrawler()
    await crawler.start()
    # Use the crawler multiple times
    result = await crawler.arun(url=url)
    # markdown = result.markdown
    # with open("usc.md", "w") as f:
    #     f.write(markdown)

    # pprint.pp(result.metadata)
    pprint.pp(result.success)
    print(result.status_code)
    internal = result.links["internal"]
    external = result.links["external"]
    # object with keys
    # {
    #     "href": "https://www.sc.edu/about/south-carolina-at-a-glance/index.php",
    #     "text": "South Carolina at a Glance",
    #     "title": "South Carolina at a Glance",
    #     "base_domain": "sc.edu",
    # }
    # print(internal[50])
    await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
