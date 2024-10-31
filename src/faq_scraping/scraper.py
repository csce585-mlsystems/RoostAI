import requests
from bs4 import BeautifulSoup


faq_url = 'https://sc.edu/about/offices_and_divisions/advising/curriculum_services/faq/index.php'

# Send an HTTP GET request to fetch the website content
response = requests.get(faq_url)

# Check if the request was successful
if response.status_code != 200:
    raise Exception(
        f"Failed to retrieve the website. Status code: {response.status_code}")

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

table_id = "DataTables_Table_0"

# Extract all text from the HTML
elements_with_ids = soup.find_all(attrs={"id": True})

# Step 4: Extract the list of ids
list_of_ids = [element['id'] for element in elements_with_ids]

# Step 5: Print or work with the list of ids
print(list_of_ids)
# table = soup.find(id=table_id)
# print(table.prettify())
print(soup.text)