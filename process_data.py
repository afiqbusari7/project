import json
import os
import glob
import re
from datetime import datetime
from technologies_extraction import extract_technologies


def parse_salary(salary):
    if not salary:
        return None

    # If salary is already a float, return its value
    if isinstance(salary, float):
        return salary

    salary = salary.lower().strip()
    salary = re.sub('[^0-9a-z$, -]+', '', salary)

    # Parse monthly salary
    if "a month" in salary:
        salary = re.sub("[^0-9-,]", "", salary)
        salary_range = [int(val.replace(',', '')) for val in salary.split('-')]
        return sum(salary_range) / len(salary_range)

    # Parse hourly salary
    if "an hour" in salary:
        salary = re.sub("[^0-9-,]", "", salary)
        salary_range = [int(val.replace(',', '')) for val in salary.split('-')]
        hourly_rate = sum(salary_range) / len(salary_range)

        # Assuming 8 working hours per day, 20 working days per month
        monthly_rate = hourly_rate * 8 * 20
        return monthly_rate

    # Parse weekly salary
    if "a week" in salary:
        salary = re.sub("[^0-9-,]", "", salary)
        salary_range = [int(val.replace(',', '')) for val in salary.split('-')]
        weekly_rate = sum(salary_range) / len(salary_range)

        # Assuming 4 weeks per month
        monthly_rate = weekly_rate * 4
        return monthly_rate

    return None


def process_careergov_data(data):
    processed_data = []
    for item in data:
        if item is None:
            continue
        processed_item = {
            "Job Title": item["Job Title"],
            "Company": item["Agency"],
            "Experience Level": item["Level"],
            "Job Type": item["Job Type"],
            "Location": None,
            "Job Description": item["Request Div Text"].replace("\n", " ").strip(),
            "Technologies": extract_technologies(item["Request Div Text"]),
            "Salary": None
        }
        processed_data.append(processed_item)
    return processed_data


def process_indeed_sg_data(data):
    processed_data = []
    for item in data:
        if item is None:
            continue
        job_title = item["Job Title"]
        if "- job post" in job_title:
            job_title = job_title.replace("- job post", "").strip()
        processed_item = {
            "Job Title": job_title,
            "Company": item["Company"],
            "Experience Level": None,
            "Job Type": None,
            "Location": item["Location"],
            "Job Description": item["Job Description"].replace("\n", " "),
            "Technologies": extract_technologies(item["Job Description"]),
            "Salary": parse_salary(item["Salary"])
        }
        processed_data.append(processed_item)
    return processed_data


def process_naukri_data(data):
    processed_data = []
    for item in data:
        if item is None:
            continue
        processed_item = {
            "Job Title": item["Job Title"],
            "Company": item["Company Name"],
            "Experience Level": item["Experience"],
            "Job Type": None,
            "Location": item["Location"],
            "Job Description": item["Job Description"].replace("\n", " "),
            "Technologies": extract_technologies(item["Job Description"]),
            "Salary": parse_salary(item["Salary"])
        }
        processed_data.append(processed_item)
    return processed_data


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_data_to_json(data, filename):
    with open(filename, "w") as outfile:
        json.dump(data, outfile, indent=2)


def find_latest_file(file_prefix):
    search_pattern = f"{file_prefix}*.json"
    files = glob.glob(search_pattern)

    latest_file = None
    latest_date = None

    for file in files:
        try:
            date_str = file.replace(file_prefix, "").replace(".json", "")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")

            if not latest_date or date_obj > latest_date:
                latest_date = date_obj
                latest_file = file
        except ValueError:
            continue

    return latest_file


def consolidate_data():
    careergov_file = find_latest_file("jobs_data_careergov_")
    indeed_sg_file = find_latest_file("jobs_data_indeed_sg_")
    naukri_file = find_latest_file("jobs_data_naukri_")

    if not careergov_file or not indeed_sg_file or not naukri_file:
        raise FileNotFoundError("One or more required files not found")

    careergov_data = process_careergov_data(read_json(careergov_file))
    indeed_sg_data = process_indeed_sg_data(read_json(indeed_sg_file))
    naukri_data = process_naukri_data(read_json(naukri_file))

    all_data = careergov_data + indeed_sg_data + naukri_data

    # Process salary data during consolidation
    for item in all_data:
        item["Salary"] = parse_salary(item["Salary"])

    # Create a timestamp for the consolidated filename
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    consolidated_filename = f"all_jobs_data_{timestamp}.json"

    save_data_to_json(all_data, consolidated_filename)
    return all_data
