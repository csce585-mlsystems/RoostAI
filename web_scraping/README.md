To procure dataset, execute the following scripts in this order

1. `python web_scraper.py` (Beautiful Soup and Selenium to scrape HTML from sc.edu domain)
2. `python collect_html.py` (Moves all scraped html into one top level directory)
3. `python extract.py` (Extracts main text from html files)
4. `python chunker.py` (Chunks main text and saves as json)