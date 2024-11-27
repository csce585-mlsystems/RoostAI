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
        """
        Check if a URL is valid and belongs to the same domain as the start URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc.endswith(tuple(self.domains))

    def get_url_save_path(self, url):
        """
        Returns the file save path for a given URL.
        """
        url = '/'.join(url.split('#'))  # Remove fragments
        url_path = Path(url.replace('//', '/'))
        return abs_data_path / url_path

    def is_unique(self, html_content):
        """
        Check if HTML content is unique by comparing its hash.
        """
        content_hash = hashlib.md5(html_content.encode()).hexdigest()
        if content_hash in self.html_hashes:
            return False
        self.html_hashes.add(content_hash)
        return True

    async def save_html(self, url, content):
        """
        Save the HTML content and metadata to the disk.
        """
        save_path = self.get_url_save_path(url)

        # Create directory structure if it doesn't exist
        os.makedirs(save_path, exist_ok=True)

        # Save HTML content
        with open(save_path / "scraped_data.html", "w", encoding="utf-8") as f:
            f.write(content)

        # Save metadata
        with open(save_path / "metadata.json", "w") as f:
            metadata = {"source_url": f"https://{url}"}
            json.dump(metadata, f)

    async def scrape_page(self, page, url):
        """
        Scrape a single page, extract links, and save content.
        """
        await page.goto(url, timeout=30000)  # 30-second timeout
        await page.wait_for_load_state("domcontentloaded")

        # Extract page content
        html_content = await page.content()

        # Save unique content
        if self.is_unique(html_content):
            await self.save_html(url, html_content)

        # Extract and filter new URLs
        new_urls = []
        links = await page.evaluate("""
            Array.from(document.querySelectorAll('a'))
                 .map(link => link.href)
        """)
        for href in links:
            full_url = urljoin(url, href)
            if self.is_valid(full_url) and full_url not in self.visited:
                new_urls.append(full_url)
                self.visited.add(full_url)

        return new_urls

    async def scrape_url(self, url, browser):
        """
        Scrape a URL using a shared Playwright browser instance.
        """
        async with self.semaphore:  # Limit concurrency
            try:
                self.logger.info(f"Scraping: {url}")
                context = await browser.new_context()
                page = await context.new_page()
                new_urls = await self.scrape_page(page, url)
                await context.close()
                print(f'New urls: {new_urls}')
                return new_urls
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                return []

    async def start(self):
        """
        Start scraping all URLs asynchronously.
        """
        queue = asyncio.Queue()
        for url in self.start_urls:
            queue.put_nowait(url)
            self.visited.add(url)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            while not queue.empty():
                url = await queue.get()
                new_urls = await self.scrape_url(url, browser)
                for new_url in new_urls:
                    if new_url not in self.visited:
                        queue.put_nowait(new_url)
            await browser.close()

if __name__ == "__main__":
    start_urls = ["https://sc.edu"]

    scraper = WebScraper(start_urls, max_concurrent=2)
    asyncio.run(scraper.start())
    print("Finished web scraping scripting")

    
# # Standard library imports
# import hashlib
# import json
# import os
# import re
# import sys
# import time
# from pathlib import Path
# from urllib.parse import urljoin, urlparse
# import threading
# from queue import Queue
# from concurrent.futures import ThreadPoolExecutor, TimeoutError
# import platform
# import logging
# from contextlib import contextmanager

# # Third-party imports
# from bs4 import BeautifulSoup
# from bs4.element import Comment
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.common.exceptions import WebDriverException, TimeoutException

# # increased recursion limit for web scraping
# sys.setrecursionlimit(5000)

# abs_data_path = Path("/home/cc/scraped_data")


# class WebScraper:
#     def __init__(self, start_urls, max_concurrent=2):  # Reduced default concurrency
#       self.start_urls = start_urls
#       self.domains = [urlparse(start_url).netloc for start_url in start_urls]
#       self.visited = set()
#       self.html_hashes = set()
#       self.url_queue = Queue()
#       self.max_concurrent = max_concurrent
#       self.semaphore = threading.Semaphore(max_concurrent)
#       self.lock = threading.Lock()

#       # Configure logging
#       logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s'
#       )
#       self.logger = logging.getLogger(__name__)

#       self.chrome_driver_path = "/usr/lib/chromium-browser/chromedriver"   


#     @contextmanager
#     def create_driver(self):
#         """Context manager for creating and cleaning up Chrome driver instances"""
#         chrome_options = Options()
#         chrome_options.add_argument("--headless=new")  # Use new headless mode
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--disable-software-rasterizer")
#         chrome_options.add_argument("--disable-extensions")
#         chrome_options.add_argument("--window-size=1920,1080")
#         chrome_options.add_argument("--ignore-certificate-errors")
#         chrome_options.add_argument("--log-level=3")  # Reduce logging
#         chrome_options.add_argument("--silent")
#         chrome_options.binary_location = "/usr/bin/chromium-browser"
#         chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
#         chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])   
        
#         service = Service(
#             self.chrome_driver_path,
#             log_path=os.devnull  # Suppress service logs
#         )
        
#         driver = None
#         try:
#             driver = webdriver.Chrome(service=service, options=chrome_options)
#             yield driver
#         finally:
#             if driver:
#                 try:
#                     driver.quit()
#                 except Exception as e:
#                     self.logger.warning(f"Error closing driver: {e}")
#                     self.force_quit_driver(driver)


#     def get_url_save_path(self, url):
#       """
#       Returns the disc save path for a given url path
#       """
#       url = '/'.join(url.split('#'))
#       url = Path(url.replace('//', '/'))
#       return abs_data_path / url


#     def is_valid(self, url):
#         """
#         Check if a URL is valid and belongs to the same domain as the start URL.
#         """
#         parsed = urlparse(url)
#         return bool(parsed.netloc) and parsed.netloc.endswith(tuple(self.domains))


#     def save_html(self, url, content: str):
#         """
#         Save the HTML content to a file, maintaining the URL structure.
#         @param url: URL of the page
#         @param content: HTML content of the page
#         """
#         if self.is_unique(content, self.html_hashes):
#           if 'https' in url:
#             url = url.split('https://')[1]
#           elif 'http' in url:
#             url = url.split('http://')[1]

#           save_path = self.get_url_save_path(url)

#           if os.path.exists(os.path.join(save_path, 'scraped_data.html')) and os.path.exists(os.path.join(save_path, 'metadata.json')):

#             ...
#           print(f'Saving to this path {str(save_path.absolute)}')

#           # Create directory structure if it doesn't exist
#           os.makedirs(save_path, exist_ok=True)
#           # Write content to file
#           with open(os.path.join(save_path, 'scraped_data.html'), 'w', encoding='utf-8') as f:
#               f.write(content)

#           # writing down useful metadata of html file path
#           # print(url)
#           with open(os.path.join(save_path, 'metadata.json'), 'w') as f:
#               metadata = {'source_url': f'https://{str(url)}'}
#               json.dump(metadata, f)


#     def scrape(self, url):
#         """
#         Scrape a single URL, save its content, and find links to scrape next.
#         """
#         if url in self.visited:
#             return  # Skip if we've already visited this URL
#         self.visited.add(url)

#         # Load the page with Selenium
#         self.driver.get(url)  

#         # Wait for the page to load
#         WebDriverWait(self.driver, 10).until(
#             EC.presence_of_element_located((By.TAG_NAME, "body"))
#         )

 
#         # Get the rendered HTML
#         html_content = self.driver.page_source

#         print(f'Visiting {url}')

#         if self.is_unique(html_content, self.html_hashes):
#             self.save_html(url, html_content)

#         # Parse HTML with beautiful soup to extract all embedded reference links
#         # And recursively scrape them
#         # Find all links and scrape them if they're valid
#         soup = BeautifulSoup(html_content, 'html.parser')
#         for link in soup.find_all('a'):
#             href = link.get('href')
#             if href:
#                 full_url = urljoin(url, href)  # Handle relative URLs
#                 if self.is_valid(full_url):
#                     self.scrape(full_url)


#     def force_quit_driver(self, driver):
#         """Force quit a potentially hanging driver"""
#         try:
#             if platform.system() == "Linux":
#                 os.system(f"kill -9 {driver.service.process.pid}")
#             elif platform.system() == "Windows":
#                 os.system(f"taskkill /F /PID {driver.service.process.pid}")
#         except Exception as e:
#             self.logger.error(f"Error force quitting driver: {e}")


#     def scrape_url(self, url, max_retries=2, retry_delay=5):
#         """Improved URL scraping with better error handling"""
#         # only try a certain number of times
#         for attempt in range(max_retries):
#             # only a certain number of threads will be able to scrape at a time to prevent too many chromedrivers to be running
#             with self.semaphore:
#                 try:
#                     # create selenium web driver 
#                     with self.create_driver() as driver:
#                         try:
#                             # Set timeout and wait for specific elements
#                             driver.set_page_load_timeout(20)
#                             driver.get(url)
                            
#                             # Wait for either body or specific content indicators
#                             wait = WebDriverWait(driver, 10)
#                             wait.until(lambda d: d.execute_script(
#                                 "return document.readyState") == "complete")
                            
#                             # Additional wait for dynamic content
#                             try:
#                                 wait.until(EC.presence_of_element_located(
#                                     (By.TAG_NAME, "body")))
#                             except TimeoutException:
#                                 if "body" not in driver.page_source.lower():
#                                     raise
                            
#                             html_content = driver.page_source
#                             self.logger.info(f'Successfully scraped {url} on attempt {attempt + 1}')
                            
#                             # Process the content
#                             with self.lock:
#                                 if self.is_unique(html_content, self.html_hashes):
#                                     self.save_html(url, html_content)
                            
#                             # Extract and return new URLs
#                             return self.extract_new_urls(url, html_content)
                            
#                         except Exception as e:
#                             self.logger.warning(
#                                 f"Attempt {attempt + 1} failed for {url}: {str(e)}")
#                             if attempt < max_retries - 1:
#                                 time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
#                             continue
                            
#                 except Exception as e:
#                     self.logger.error(f"Browser error on attempt {attempt + 1} for {url}: {str(e)}")
#                     if attempt < max_retries - 1:
#                         time.sleep(retry_delay * (attempt + 1))
#                     continue
                    
#         self.logger.error(f"Failed to scrape {url} after {max_retries} attempts")
#         return []


#     def extract_new_urls(self, base_url, html_content):
#         """Extract and filter new URLs from HTML content"""
#         soup = BeautifulSoup(html_content, 'html.parser')
#         new_urls = []
        
#         for link in soup.find_all('a'):
#             href = link.get('href')
#             if href:
#                 full_url = urljoin(base_url, href)
#                 with self.lock:
#                     if self.is_valid(full_url) and full_url not in self.visited:
#                         self.visited.add(full_url)
#                         new_urls.append(full_url)
        
#         return new_urls


#     def normalize_html(self, html_content):
#       # Parse HTML
#       soup = BeautifulSoup(html_content, 'html.parser')

#       # Remove comments
#       for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
#           comment.extract()

#       # Lowercase all text
#       for element in soup(text=True):
#           element.string = element.string.lower()

#       # Sort attributes
#       for tag in soup.find_all():
#           if tag.attrs:
#               tag.attrs = dict(sorted(tag.attrs.items()))

#       # Remove whitespace
#       return re.sub(r'\s+', '', str(soup))


#     def is_unique(self, html_content, existing_hashes):
#         with self.lock:
#             content_hash = hashlib.md5(html_content.encode()).hexdigest()
            
#             if content_hash in existing_hashes:
#                 return False
            
#             existing_hashes.add(content_hash)
#             return True
          
    
#     def start(self):
#         """
#         Enhanced start method with comprehensive error handling and detailed logging.
        
#         Provides more granular error tracking and recovery mechanisms for web scraping.
#         """
#         for url in self.start_urls:
#             self.url_queue.put(url)
#             with self.lock:
#                 self.visited.add(url)
        
#         # Track overall scraping statistics
#         total_processed_urls = 0
#         failed_urls = []
        
#         # spawn the threads
#         with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
#             while True:
#                 try:
#                     # append all urls in the queue to current urls
#                     current_urls = []
#                     while not self.url_queue.empty():
#                         current_urls.append(self.url_queue.get())
                    
#                     # no more to scrape
#                     if not current_urls:
#                         break
                    
#                     # Process URLs in batches
#                     futures = []
#                     for url in current_urls:
#                         future = executor.submit(self.scrape_url, url)
#                         futures.append((url, future))
                    
#                     # Handle results and queue new URLs
#                     for url, future in futures:
#                         try:
#                             new_urls = future.result(timeout=90)  # Increased timeout
#                             total_processed_urls += 1
                            
#                             if new_urls:
#                                 for new_url in new_urls:
#                                     self.url_queue.put(new_url)
                            
#                         except TimeoutError:
#                             self.logger.warning(f"Timeout occurred while processing {url}")
#                             failed_urls.append((url, "Timeout"))
                        
#                         except Exception as e:
#                             self.logger.error(f"Failed to process {url}: {e}")
#                             failed_urls.append((url, str(e)))
                
#                 except Exception as e:
#                     self.logger.critical(f"Catastrophic error in scraping loop: {e}")
#                     break
        
#         # Log final scraping statistics
#         self.logger.info(f"Total URLs Processed: {total_processed_urls}")
#         if failed_urls:
#             self.logger.warning(f"Failed URLs ({len(failed_urls)}):")
#             for url, error in failed_urls:
#                 self.logger.warning(f"- {url}: {error}")
                  
#     def cleanup_chrome_processes(self):
#         """
#         Clean up any lingering chrome processes
#         """
#         try:
#             if platform.system() == "Linux":
#                 os.system("pkill -f chromium")
#                 os.system("pkill -f chrome")
#             elif platform.system() == "Windows":
#                 os.system("taskkill /f /im chrome.exe")
#                 os.system("taskkill /f /im chromedriver.exe")
#         except Exception as e:
#             print(f"Error during cleanup: {e}")


#     def __enter__(self):
#         return self


#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.cleanup_chrome_processes()


# if __name__ == "__main__":
#     start_urls = ["https://sc.edu"]
#     with WebScraper(start_urls, max_concurrent=2) as scraper:
#         try:
#             scraper.start()
#         except KeyboardInterrupt:
#             print("\nScraping interrupted by user")
#         except Exception as e:
#             print(f"Scraping error: {e}")
#     print("Finished web scraping scripting")
    
