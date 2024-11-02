# Standard library imports
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import platform

# Third-party imports
from bs4 import BeautifulSoup
from bs4.element import Comment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# increased recursion limit for web scraping
sys.setrecursionlimit(5000)

abs_data_path = Path("/home/cc/scraped_data")

class WebScraper:
    def __init__(self, start_urls, max_concurrent=6):
        self.start_urls = start_urls

        self.domains = [urlparse(start_url).netloc for start_url in self.start_urls]
        self.visited = set()
        self.html_hashes = set()
        self.url_queue = Queue()
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self.lock = threading.Lock()  # For thread-safe operations on sets

        # # Set up Selenium WebDriver
        # self.chrome_options = Options()
        # self.chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        # self.chrome_options.add_argument("--no-sandbox")
        # self.chrome_options.add_argument("--disable-dev-shm-usage")
        # self.chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
        # self.chrome_options.add_argument("--remote-debugging-port=9222")  # Fix DevTools issue
        # self.chrome_options.binary_location = "/usr/bin/chromium-browser"  # Use Chromium instead of Chrome
        
        self.chrome_driver_path = "/usr/lib/chromium-browser/chromedriver"  # Path to chromedriver

        # service = Service(chrome_driver_path)
        # self.driver = webdriver.Chrome(service=service, options=chrome_options)


    def get_url_save_path(self, url):
      """
      Returns the disc save path for a given url path
      """
      url = '/'.join(url.split('#'))
      url = Path(url.replace('//', '/'))
      return abs_data_path / url


    def is_valid(self, url):
        """
        Check if a URL is valid and belongs to the same domain as the start URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc.endswith(tuple(self.domains))


    def save_html(self, url, content: str):
        """
        Save the HTML content to a file, maintaining the URL structure.
        @param url: URL of the page
        @param content: HTML content of the page
        """
        if self.is_unique(content, self.html_hashes):
          if 'https' in url:
            url = url.split('https://')[1]
          elif 'http' in url:
            url = url.split('http://')[1]

          save_path = self.get_url_save_path(url)

          if os.path.exists(os.path.join(save_path, 'scraped_data.html')) and os.path.exists(os.path.join(save_path, 'metadata.json')):

            ...
          print(f'Saving to this path {str(save_path.absolute)}')

          # Create directory structure if it doesn't exist
          os.makedirs(save_path, exist_ok=True)
          # Write content to file
          with open(os.path.join(save_path, 'scraped_data.html'), 'w', encoding='utf-8') as f:
              f.write(content)

          # writing down useful metadata of html file path
          # print(url)
          with open(os.path.join(save_path, 'metadata.json'), 'w') as f:
              metadata = {'source_url': f'https://{str(url)}'}
              json.dump(metadata, f)


    def scrape(self, url):
        """
        Scrape a single URL, save its content, and find links to scrape next.
        """
        if url in self.visited:
            return  # Skip if we've already visited this URL
        self.visited.add(url)

        # Load the page with Selenium
        self.driver.get(url)  

        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Allow some time for JavaScript to execute
        time.sleep(2)  

        # Get the rendered HTML
        html_content = self.driver.page_source

        print(f'Visiting {url}')

        if self.is_unique(html_content, self.html_hashes):
            self.save_html(url, html_content)

        # Parse HTML with beautiful soup to extract all embedded reference links
        # And recursively scrape them
        # Find all links and scrape them if they're valid
        soup = BeautifulSoup(html_content, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)  # Handle relative URLs
                if self.is_valid(full_url):
                    self.scrape(full_url)

    
    def scrape_url(self, url, max_retries=3, retry_delay=5):
        """
        Scrape a single URL with retries and improved error handling
        """
        for attempt in range(max_retries):
            with self.semaphore:  # Limit concurrent browsers
                driver = None
                try:
                    # Enhanced Chrome options
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    chrome_options.add_argument("--disable-gpu")
                    chrome_options.add_argument("--disable-software-rasterizer")
                    chrome_options.add_argument("--disable-extensions")
                    chrome_options.add_argument("--single-process")
                    chrome_options.add_argument("--disable-setuid-sandbox")
                    chrome_options.add_argument("--window-size=1920,1080")
                    chrome_options.add_argument("--disable-infobars")
                    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
                    chrome_options.add_argument("--ignore-certificate-errors")
                    chrome_options.binary_location = "/usr/bin/chromium-browser"

                    service = Service(
                        self.chrome_driver_path,
                        service_args=['--verbose']
                    )
                    
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver.set_page_load_timeout(30)  # Set page load timeout
                    
                    try:
                        driver.get(url)
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        
                        html_content = driver.page_source
                        print(f'Successfully visited {url} on attempt {attempt + 1}')
                        self.save_html(url, html_content)
                        
                        # Extract new URLs
                        soup = BeautifulSoup(html_content, 'html.parser')
                        new_urls = []
                        for link in soup.find_all('a'):
                            href = link.get('href')
                            if href:
                                full_url = urljoin(url, href)
                                with self.lock:
                                    if self.is_valid(full_url) and full_url not in self.visited:
                                        self.visited.add(full_url)
                                        new_urls.append(full_url)
                        
                        return new_urls
                        
                    except Exception as e:
                        print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                        if attempt < max_retries - 1:
                            print(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        continue
                        
                except Exception as e:
                    print(f"Browser creation failed on attempt {attempt + 1} for {url}: {str(e)}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    continue
                    
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass  # Ignore errors during cleanup
                    
        print(f"Failed to scrape {url} after {max_retries} attempts")
        return []  
    
        
    def start(self):
            """
            Start the scraping process using a thread pool
            """
            # Add initial URLs to queue
            for url in self.start_urls:
                self.url_queue.put(url)
                with self.lock:
                    self.visited.add(url)
            
            # spawns threads
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                
                while True:
                    try:
                        # Get all current URLs to process
                        current_urls = []
                        while not self.url_queue.empty():
                            current_urls.append(self.url_queue.get())
                        
                        if not current_urls:
                            break
                        
                        # Process current batch of URLs
                        futures = [executor.submit(self.scrape_url, url) for url in current_urls]
                        
                        # Add new URLs to queue
                        for future in futures:
                            for new_url in future.result():
                                self.url_queue.put(new_url)
                                
                    except Exception as e:
                        print(f"Error in main loop: {e}")
                        break


    def normalize_html(self, html_content):
      # Parse HTML
      soup = BeautifulSoup(html_content, 'html.parser')

      # Remove comments
      for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
          comment.extract()

      # Lowercase all text
      for element in soup(text=True):
          element.string = element.string.lower()

      # Sort attributes
      for tag in soup.find_all():
          if tag.attrs:
              tag.attrs = dict(sorted(tag.attrs.items()))

      # Remove whitespace
      return re.sub(r'\s+', '', str(soup))


    def is_unique(self, html_content, existing_hashes):
        with self.lock:
            content_hash = hashlib.md5(html_content.encode()).hexdigest()
            
            if content_hash in existing_hashes:
                return False
            
            existing_hashes.add(content_hash)
            return True
          
          
    def cleanup_chrome_processes(self):
        """
        Clean up any lingering chrome processes
        """
        try:
            if platform.system() == "Linux":
                os.system("pkill -f chromium")
                os.system("pkill -f chrome")
            elif platform.system() == "Windows":
                os.system("taskkill /f /im chrome.exe")
                os.system("taskkill /f /im chromedriver.exe")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_chrome_processes()

if __name__ == "__main__":
    start_urls = ["https://sc.edu"]
    with WebScraper(start_urls, max_concurrent=2) as scraper:  # Reduced concurrent browsers
        try:
            scraper.start()
        except KeyboardInterrupt:
            print("Scraping interrupted by user")
        except Exception as e:
            print(f"Scraping error: {e}")