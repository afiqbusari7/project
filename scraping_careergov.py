### Careers@Gov Job Listings Scraper ###

import time
from datetime import datetime
import json
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_careergov():
    # Path to your chromedriver
    CHROME_DRIVER_PATH = 'chromedriver'

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver = webdriver.Chrome(
        executable_path=CHROME_DRIVER_PATH, options=options)

    # Load the careers.gov.sg website
    driver.get(
        'https://www.careers.hrp.gov.sg/sap/bc/ui5_ui5/sap/ZGERCFA004/index.html')

    wait = WebDriverWait(driver, 10)

    # Find and click the link with text 'FIELD'
    field_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, '//a[contains(text(), "FIELD")]')))
    field_link.click()

    # Wait for the modal to appear after clicking 'FIELD'
    modal = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, '__dialog0-dialog')))

    # Wait for the modal content to be visible
    wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, 'div.sapMDialogScrollCont')))

    # Find the li element for 'InfoComm, Technology, New Media Communications'
    target_li = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//li[.//div[contains(text(), "InfoComm, Technology, New Media Communications")]]')))

    # Find the div element with the specified classes inside the li element
    checkbox_div = target_li.find_element(
        By.XPATH, './/div[contains(@class, "sapMCbBg sapMCbHoverable sapMCbActiveStateOff sapMCbMark")]')

    # Click the div to toggle the checkbox
    checkbox_div.click()

    # Find the bdi element containing the text 'APPLY'
    apply_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, '//bdi[contains(text(), "APPLY")]')))

    # Click the APPLY button
    apply_button.click()

    # Function to scroll and load more jobs

    def scroll_to_load_more_jobs():
        previous_jobs_count = len(driver.find_elements(
            By.XPATH, '//a[contains(@class, "sapMLnk")]'))
        driver.switch_to.active_element.send_keys(Keys.END)

        def new_jobs_loaded(driver):
            current_jobs_count = len(driver.find_elements(
                By.XPATH, '//a[contains(@class, "sapMLnk")]'))
            return current_jobs_count > previous_jobs_count

        try:
            WebDriverWait(driver, 2).until(new_jobs_loaded)
        except TimeoutException:
            pass

    FILTER_LINKS = 6
    END_LINKS = 10

    # Keep scrolling until no new jobs are loaded
    previous_jobs_count = 0
    while True:
        scroll_to_load_more_jobs()
        job_links = driver.find_elements(
            By.XPATH, '//a[contains(@class, "sapMLnk")]')
        current_jobs_count = len(job_links) - FILTER_LINKS

        if current_jobs_count == previous_jobs_count:
            break
        else:
            previous_jobs_count = current_jobs_count

    # Update jobs_count with the fully loaded jobs list
    jobs_count = len(job_links) - FILTER_LINKS - END_LINKS
    i = FILTER_LINKS
    jobs_data = []

    while i - FILTER_LINKS < jobs_count:
        try:
            # Click on the job link
            job_links[i].click()
        except Exception:
            break

        # Wait for the "APPLY NOW" button to load
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//bdi[contains(text(), "APPLY NOW")]')))

        time.sleep(1)

        # Scrape key job details
        job_title = driver.find_element(
            By.ID, '__xmlview1--titleJD-inner').text
        agency = driver.find_element(
            By.CSS_SELECTOR, '.agencyLabelJD bdi').text
        level = driver.find_element(
            By.CSS_SELECTOR, '.midLevelTextJD bdi').text
        job_type = driver.find_elements(
            By.CSS_SELECTOR, '.midLevelTextJD bdi')[1].text
        # Handle optional closing_date
        try:
            closing_date = driver.find_element(
                By.CSS_SELECTOR, '.midLevelTextJD.colorJobRed bdi').text
        except:
            closing_date = ''
        applicants = driver.find_elements(
            By.CSS_SELECTOR, '.midLevelTextJD bdi')[-1].text

        # Scrape data from the specified div
        request_div = driver.find_element(
            By.CSS_SELECTOR, '.sapUiRespGrid.sapUiRespGridMedia-Std-Tablet.sapUiRespGridHSpace1.sapUiRespGridVSpace1.sapUiMediumMarginTop.blockLayoutJobDescription')
        request_div_text = request_div.text

        job_data = {
            "Job Title": job_title,
            "Agency": agency,
            "Level": level,
            "Job Type": job_type,
            "Closing Date": closing_date,
            "Applicants": applicants,
            "Request Div Text": request_div_text.replace('"', "'")
        }

        jobs_data.append(job_data)

        # Go back to the job listings
        driver.execute_script("window.history.go(-1)")

        # Update jobs list
        job_links = driver.find_elements(
            By.XPATH, '//a[contains(@class, "sapMLnk")]')
        jobs_count = len(job_links) - FILTER_LINKS - END_LINKS
        i += 1

        # Print progress
        print(f"Scraped {i - FILTER_LINKS} jobs of {jobs_count} jobs")

    # Save all jobs data to a file
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f'jobs_data_careergov_{current_time}.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, ensure_ascii=False, indent=4)

    print(f"Jobs data saved to '{file_name}'")

    # Close the browser
    driver.quit()


if __name__ == '__main__':
    scrape_careergov()
