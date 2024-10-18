from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from bs4.element import Comment
from urllib.parse import urljoin, urlparse
import os
import time
from pathlib import Path
import hashlib
import re

abs_data_path = Path("/home/cc/scraped_data")

class WebScraper:
    def __init__(self, start_url):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited = set()
        self.html_hashes = set()
        
        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Use Chromium instead of Chrome
        chrome_options.binary_location = "/usr/bin/chromium-browser"  # Adjust if necessary

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        


    def is_valid(self, url):
        """
        Check if a URL is valid and belongs to the same domain as the start URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc.endswith(self.domain)


    def save_html(self, url, content: str):
        """
        Save the HTML content to a file, maintaining the URL structure.
        @param url: URL of the page
        @param content: HTML content of the page
        """
        if self.is_unique(content, self.html_hashes):
          # parsed = urlparse(url)
          url = url.split('https://')[1]
          url = '/'.join(url.split('#'))
          url = Path(url.replace('//', '/'))
          save_path = abs_data_path / url

          print(f'Saving to this path {str(save_path.absolute)}')
          
          # # Create directory structure if it doesn't exist
          os.makedirs(save_path, exist_ok=True)
          # # Write content to file
          with open(os.path.join(save_path, 'scraped_data.html'), 'w', encoding='utf-8') as f:
              f.write(content)


    def scrape(self, url):
        """
        Scrape a single URL, save its content, and find links to scrape next.
        """
        if url in self.visited:
            return  # Skip if we've already visited this URL
        self.visited.add(url)

        self.driver.get(url)  # Load the page with Selenium

        # Wait for the page to load (adjust timeout as needed)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Allow some time for JavaScript to execute
        time.sleep(2)  # Adjust this delay as needed

        # Get the rendered HTML
        html_content = self.driver.page_source
        print(f'Visiting {url}')
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
            self.scrape(self.start_url)
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
    start_url = "https://sc.edu"  # Replace with your university's URL
    scraper = WebScraper(start_url)
    scraper.start()