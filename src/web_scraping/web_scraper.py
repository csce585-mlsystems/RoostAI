# Standard library imports
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse


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
    def __init__(self, start_urls):
        self.start_urls = start_urls
        
        self.domains = [urlparse(start_url).netloc for start_url in self.start_urls]
        self.visited = set()
        self.html_hashes = set()
        
        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
        chrome_options.add_argument("--remote-debugging-port=9222")  # Fix DevTools issue

        # Use Chromium instead of Chrome
        chrome_options.binary_location = "/usr/bin/chromium-browser"  # Adjust if necessary

        # Path to chromedriver
        chrome_driver_path = "/usr/lib/chromium-browser/chromedriver"  # Adjust this path

        service = Service(chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)


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


    def start(self):
        """
        Start the scraping process from the initial URL.
        """
        try:
            for url in self.start_urls:
              self.scrape(url)
        finally:
            self.driver.quit()  # Ensure the browser is closed when we're done


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
        normalized_html = self.normalize_html(html_content)
        content_hash = hashlib.md5(html_content.encode()).hexdigest()
        
        if content_hash in existing_hashes:
            return False
        
        existing_hashes.add(content_hash)
        return True


if __name__ == "__main__":
    start_urls = ["https://sc.edu"]  # Replace with your university's URL
    scraper = WebScraper(start_urls)
    scraper.start()