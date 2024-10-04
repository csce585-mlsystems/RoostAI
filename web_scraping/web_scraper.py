from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
from pathlib import Path

abs_data_path = Path("C:/Users/2002v/Desktop/Fall2024/CSCE585/scraped_data")

class UniversityWebScraper:
    def __init__(self, start_url):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited = set()
        
        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=chrome_options)

    def is_valid(self, url):
        """
        Check if a URL is valid and belongs to the same domain as the start URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc.endswith(self.domain)

    def save_html(self, url, content):
        """
        Save the HTML content to a file, maintaining the URL structure.
        """
        # parsed = urlparse(url)
        url = url.split('https://')[1]
        url = '/'.join(url.split('#'))
        url = Path(url.replace('//', '/'))
        save_path = abs_data_path / url
        # path = parsed.path
        # if not path.endswith('.html'):
        #     # path = os.path.join(path, 'index.html')
        print(save_path.absolute)
        
        # save_path = os.path.join(abs_data_path, path)
        # print(save_path)
        
        # # Create directory structure if it doesn't exist
        # os.makedirs(save_path, exist_ok=True)
        # # Write content to file
        # with open(os.path.join(save_path, 'scraped_data.html'), 'w', encoding='utf-8') as f:
        #     f.write(content)

    def scrape(self, url):
        """
        Scrape a single URL, save its content, and find links to scrape next.
        """
        if url in self.visited:
            return  # Skip if we've already visited this URL
        self.visited.add(url)

        # print(f"Scraping: {url}")
        self.driver.get(url)  # Load the page with Selenium

        # Wait for the page to load (adjust timeout as needed)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Allow some time for JavaScript to execute
        time.sleep(2)  # Adjust this delay as needed

        # Get the rendered HTML
        html_content = self.driver.page_source
        self.save_html(url, html_content)

        # Parse the HTML with BeautifulSoup
        
        # if php, parse as php, else if html, parse as html
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find all links and scrape them if they're valid
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

if __name__ == "__main__":
    start_url = "https://sc.edu"  # Replace with your university's URL
    scraper = UniversityWebScraper(start_url)
    scraper.start()