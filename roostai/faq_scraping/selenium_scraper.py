import time
from bs4 import BeautifulSoup

# selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import pandas as pd


def get_qa(page_link):
    # Set up headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    driver.get(page_link)

    all_questions = []
    all_answers = []

    while True:
        # Get the current page HTML
        page = driver.page_source

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(page, "html.parser")

        # Get QA table
        table_element = soup.find(id="DataTables_Table_0")
        tbody = table_element.find("tbody")
        rows = tbody.find_all("tr")

        questions = []
        answers = []

        # Loop through each row and extract questions/answers
        for row in rows:
            tds = row.find_all("td")

            # First td will be the question

            questions.append(" ".join(tds[0].text.split()))

            # Second td will contain the answer and URLs
            answer_td = tds[1]
            text = " ".join(answer_td.get_text(separator=" ").split())
            urls = [a["href"] for a in answer_td.find_all("a", href=True)]
            urls = ", ".join(urls)
            answer = f"{text} ({urls})" if urls else text
            answers.append(answer)

        all_questions.extend(questions)
        all_answers.extend(answers)

        button = driver.find_element(By.ID, "DataTables_Table_0_next")

        try:
            # Locate the "Next" button and check if it's enabled
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "DataTables_Table_0_next"))
            )

            # Check if the next button is disabled
            if "disabled" in next_button.get_attribute("class"):
                print("Reached the last page, no more Next button.")
                break

            # Click the "Next" button
            next_button.click()

            # Wait for the next page to load completely before continuing
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[@id='DataTables_Table_0']//tr")
                )
            )
            # Optionally, you can use this to ensure the page has fully transitioned
            time.sleep(1)
        except Exception as e:
            print(f"Error or last page reached: {e}")
            break  # If there is no "Next" button or an error occurs, exit the loop

    driver.quit()
    return all_questions, all_answers


def main():
    page = "https://sc.edu/about/offices_and_divisions/advising/curriculum_services/faq/index.php"
    questions, answers = get_qa(page)

    df = pd.DataFrame({"question": questions, "answer": answers})

    df.to_csv("data/faq_pairs.csv", index=False)


if __name__ == "__main__":
    main()
