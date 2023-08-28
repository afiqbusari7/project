### Naukri Job Listings Scraper ###

import json
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_naukri():
    def extract_job_details_from_template_type1():
        job_title_element = driver.find_element(
            By.CSS_SELECTOR, '.jd-header-title')
        company_name_element = driver.find_element(
            By.CSS_SELECTOR, '.jd-header-comp-name a')
        experience_element = driver.find_element(By.CSS_SELECTOR, '.exp')
        salary_element = driver.find_element(By.CSS_SELECTOR, '.salary')
        location_element = driver.find_element(By.CSS_SELECTOR, '.location')
        job_description_element = driver.find_element(
            By.CSS_SELECTOR, 'section.job-desc')

        return {
            "Job Title": job_title_element.text,
            "Company Name": company_name_element.text,
            "Experience": experience_element.text,
            "Salary": salary_element.text,
            "Location": location_element.text,
            "Job Description": job_description_element.text.replace('"', "'")
        }

    def extract_job_details_from_template_type2():
        job_title_element = driver.find_element(
            By.CSS_SELECTOR, '.av-special-heading-tag')
        company_name_element = driver.find_element(By.CSS_SELECTOR, 'title')
        experience_element = driver.find_element(
            By.CSS_SELECTOR, '.getExperience')
        salary_element = driver.find_element(
            By.CSS_SELECTOR, '.getSalaryRange')
        location_element = driver.find_element(
            By.CSS_SELECTOR, '.getCityLinks')
        job_description_section_elements = driver.find_elements(
            By.CSS_SELECTOR, 'section.JD')

        job_description_text = "\n".join(
            [section.text for section in job_description_section_elements]).replace('"', "'")

        return {
            "Job Title": job_title_element.text,
            "Company Name": company_name_element.text.strip(),
            "Experience": experience_element.text,
            "Salary": salary_element.text,
            "Location": location_element.text,
            "Job Description": job_description_text
        }

    def scrape_job_details():
        # Wait for the new window
        wait.until(EC.number_of_windows_to_be(2))

        # Switch to the new window
        new_window_handle = [
            window for window in driver.window_handles if window != driver.current_window_handle][0]
        driver.switch_to.window(new_window_handle)

        try:
            # Wait condition for Template Type 1
            is_template_type1 = False
            try:
                WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '.jd-header-title')))
                is_template_type1 = True
            except:
                pass

            # Wait condition for Template Type 2
            is_template_type2 = False
            if not is_template_type1:
                try:
                    WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '.av-special-heading-tag')))
                    is_template_type2 = True
                except:
                    pass

            # Scrape job details based on the template type
            if is_template_type1:
                job_data = extract_job_details_from_template_type1()
            elif is_template_type2:
                job_data = extract_job_details_from_template_type2()
            else:
                raise Exception("No matching template found.")

            # Close the new window/tab
            driver.close()

            # Switch back to the original window/tab
            driver.switch_to.window(driver.window_handles[0])

            return job_data

        except Exception:
            print(
                f"Skipped a job listing due to timeout.\nURL: {driver.current_url}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return None

    CHROME_DRIVER_PATH = 'chromedriver'

    options = uc.ChromeOptions()

    # Enabling headless mode
    options.add_argument('--headless')

    # Disable or limit WebDriver logging
    options.add_experimental_option(
        'prefs', {'goog:loggingPrefs': {'performance': 'OFF'}})

    # Disable known automation flags
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(executable_path=CHROME_DRIVER_PATH,
                       options=options, version_main=113)

    # Load the filtered page for tech jobs
    driver.get(
        'https://www.naukri.com/tech-jobs?k=tech&functionAreaIdGid=3&functionAreaIdGid=8')

    # Obtain the total number of jobs from the webpage
    wait = WebDriverWait(driver, 10)
    total_jobs_element = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//div[@class="h1-wrapper"]/span')))
    total_jobs = int(total_jobs_element.text.split()[-1])

    # Calculate the total number of pages and the number of jobs per page
    jobs_per_page = 20
    total_pages = (total_jobs // jobs_per_page) + \
        (1 if total_jobs % jobs_per_page != 0 else 0)

    jobs_data = []

    # Iterate through all pages and job listings
    current_page = 1
    total_scraped_jobs = 0
    while current_page <= total_pages:
        # Wait for the job listings to load and fetch <article> elements within job_listings
        job_listings = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//div[@class="list"]//article')))
        job_listings_count = len(job_listings)

        for job_listing_index in range(job_listings_count):
            # Update the total_scraped_jobs count
            total_scraped_jobs += 1

            # Click on the current job listing
            try:
                job_listings[job_listing_index].click()
            except:
                continue

            # Scrape job details
            job_data = scrape_job_details()

            if job_data is not None:
                # Add job data to the jobs_data list
                jobs_data.append(job_data)

            # Re-fetch job listings (with the <article> elements) after going back to the same page
            job_listings = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@class="list"]//article')))

            # Print progress
            print(f"Scraped {total_scraped_jobs} jobs of {total_jobs}")

        # Proceed to the next page
        current_page += 1
        if current_page <= total_pages:
            next_page_url = f"https://www.naukri.com/tech-jobs-{current_page}?k=tech&functionAreaIdGid=3&functionAreaIdGid=8"
            driver.get(next_page_url)

    # Save all jobs data to a file
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f'jobs_data_naukri_{current_time}.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, ensure_ascii=False, indent=4)

    print(f"Jobs data saved to '{file_name}'")

    # Close the browser
    driver.quit()


if __name__ == '__main__':
    scrape_naukri()
