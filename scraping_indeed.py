### Indeed Job Listings Scraper ###

import json
import time
from datetime import datetime
from random import randint
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_indeed():
    def scrape_job_details():

        # Wait for the job listing to load (with a 5-second timeout)
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '.jobsearch-JobInfoHeader-title > span')))
        except:
            return None

        job_title = driver.find_elements(By.CSS_SELECTOR,
                                         '.jobsearch-RightPane span')[0].text.strip()

        company_name = driver.find_element(By.CSS_SELECTOR,
                                           '.jobsearch-CompanyInfoContainer > div > div > div > div > div:nth-of-type(2) > div').text.strip()

        location = driver.find_element(By.CSS_SELECTOR,
                                       '.jobsearch-CompanyInfoContainer > div > div > div > div:nth-of-type(2) > div').text.strip()

        try:
            salary = driver.find_element(By.CSS_SELECTOR,
                                         '#salaryInfoAndJobType span:nth-of-type(1)').text.strip()
        except:
            salary = 'N/A'

        job_description = driver.find_element(By.CSS_SELECTOR,
                                              '#jobDescriptionText').text.strip().replace('"', "'")

        job_data = {
            "Job Title": job_title,
            "Company": company_name,
            "Location": location,
            "Salary": salary,
            "Job Description": job_description
        }

        # Print Job Listing
        # print(json.dumps(job_data, indent=2))

        return job_data

    CHROME_VERSION = 113

    user_agent_desktop = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.{}.{}.{} Safari/537.36"
        .format(CHROME_VERSION, randint(1000, 9999), randint(100, 999), randint(100, 999)))

    options = uc.ChromeOptions()
    options.add_argument(f"user-agent={user_agent_desktop}")
    options.add_argument('--headless')

    CHROME_DRIVER_PATH = 'chromedriver'
    driver = uc.Chrome(executable_path=CHROME_DRIVER_PATH,
                       options=options, version_main=CHROME_VERSION)

    driver.get('https://sg.indeed.com/jobs?q=tech&l=&from=searchOnHP')
    jobs_data = []

    total_jobs_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, '.jobsearch-JobCountAndSortPane-jobCount span')))
    total_jobs = int(total_jobs_element.text.split()[0].replace(',', ''))

    total_scraped_jobs = 0

    while True:
        job_listings = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'ul.jobsearch-ResultsList > li')))

        job_listings_count = len(job_listings)

        for job_listing_index in range(job_listings_count):
            total_scraped_jobs += 1

            try:
                # Scroll the job_listing into view
                driver.execute_script(
                    'arguments[0].scrollIntoView({block: "center"});', job_listings[job_listing_index])
                time.sleep(1)

                # Click on the current job listing
                job_listings[job_listing_index].click()
            except:
                continue

            job_data = scrape_job_details()
            jobs_data.append(job_data)

            print(f"Scraped {total_scraped_jobs} jobs of {total_jobs}")

        try:
            next_page_button = driver.find_elements(
                By.CSS_SELECTOR, 'nav[role="navigation"] a:last-child')[-1]
            # Check if the next_page_button contains an <svg> element
            svg_element = next_page_button.find_element(By.CSS_SELECTOR, 'svg')
            if svg_element:
                next_page_button.click()

                # Wait for the icl-Modal to load and close it
                try:
                    icl_modal_close_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.icl-Modal .icl-CloseButton')))
                    icl_modal_close_button.click()
                except:
                    pass
            else:
                break
        except Exception as e:
            print(e)
            break

    # Save all jobs data to a file
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f'jobs_data_indeed_sg_{current_time}.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, ensure_ascii=False, indent=4)

    print(f"Jobs data saved to '{file_name}'")

    # Close the browser
    driver.quit()


if __name__ == '__main__':
    scrape_indeed()
