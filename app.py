from quart import Quart, request, Response, render_template
from scraping_careergov import scrape_careergov
from scraping_indeed import scrape_indeed
from scraping_naukri import scrape_naukri
import pandas as pd
import os
import json
import process_data
from job_title_clustering import cluster_job_titles

app = Quart(__name__)


@app.after_request
async def add_cors_headers(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = ",".join(
        ["Content-Type", "Authorization"])
    response.headers["Access-Control-Allow-Methods"] = ",".join(
        ["GET", "POST", "PATCH", "DELETE", "OPTIONS"])
    return response


def file_exists(file_name_prefix):
    return any(process_data.find_latest_file(file_name_prefix))


@app.route("/")
async def index():
    return await render_template("index.html")


@app.route("/scrape/careergov")
async def careergov_scrape():
    scrape_careergov()
    if file_exists("jobs_data_careergov_"):
        return json.dumps({"success": True, "message": "Careergov data scraped and saved successfully"})
    else:
        return json.dumps({"success": False, "message": "Failed to save Careergov data"})


@app.route("/scrape/indeed")
async def indeed_scrape():
    scrape_indeed()
    if file_exists("jobs_data_indeed_sg_"):
        return json.dumps({"success": True, "message": "Indeed data scraped and saved successfully"})
    else:
        return json.dumps({"success": False, "message": "Failed to save Indeed data"})


@app.route("/scrape/naukri")
async def naukri_scrape():
    scrape_naukri()
    if file_exists("jobs_data_naukri_"):
        return json.dumps({"success": True, "message": "Naukri data scraped and saved successfully"})
    else:
        return json.dumps({"success": False, "message": "Failed to save Naukri data"})


@app.route("/consolidate")
async def consolidate_scrape():
    try:
        process_data.consolidate_data()
        if file_exists("all_jobs_data_"):
            return json.dumps({"success": True, "message": "All data consolidated and saved successfully"})
        else:
            return json.dumps({"success": False, "message": "Failed to save consolidated data"})
    except FileNotFoundError as e:
        return json.dumps({"success": False, "message": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "message": "An unexpected error occurred: " + str(e)})


def display_data(file_name_prefix):
    data_file = process_data.find_latest_file(file_name_prefix)

    if data_file:
        data = process_data.read_json(data_file)
    else:
        data = []

    return json.dumps(data)


@app.route("/display/careergov")
async def display_careergov():
    return display_data("jobs_data_careergov_")


@app.route("/display/indeed")
async def display_indeed():
    return display_data("jobs_data_indeed_sg_")


@app.route("/display/naukri")
async def display_naukri():
    return display_data("jobs_data_naukri_")


@app.route("/display/all")
async def display_all():
    return display_data("all_jobs_data_")


@app.route("/graph/statistics")
async def graph_statistics():
    try:
        all_jobs_file = process_data.find_latest_file("all_jobs_data_")

        if all_jobs_file:
            all_data = process_data.read_json(all_jobs_file)
        else:
            all_data = []

        df = pd.DataFrame(all_data)
        df = cluster_job_titles(df)

        # Job listing volume
        job_listing_volume = df.shape[0]

        # Average salaries
        df["Salary"] = pd.to_numeric(df["Salary"], errors="coerce")
        avg_salary = df["Salary"].mean()

        # Grouped category types for different tech jobs
        job_categories = df.groupby("Job Title")[
            "Job Title"].count().sort_values(ascending=False)

        # Calculating additional statistics for each cluster
        job_categories_stats = df.groupby(
            "Cluster")["Job Title"].count().sort_values(ascending=False)

        cluster_salary_stats = df.groupby("Cluster")["Salary"].agg(
            ["count", "mean", "median", "min", "max"]).reset_index()

        # Calculate the 25th and 75th percentiles
        for percentile in [25, 75]:
            cluster_salary_stats[f"{percentile}_percentile"] = df.groupby(
                "Cluster")["Salary"].apply(lambda x: x.quantile(percentile/100))

        # Calculate Experience Level Mode, Job Type Mode, and Job Titles Example for each cluster
        cluster_stats_extended = []
        for cluster_id in range(len(cluster_salary_stats)):
            cluster_data = df[df["Cluster"] == cluster_id]
            exp_level_mode = cluster_data["Experience Level"].mode(
            ).values[0] if not cluster_data["Experience Level"].mode().empty else None
            job_type_mode = cluster_data["Job Type"].mode(
            ).values[0] if not cluster_data["Job Type"].mode().empty else None
            job_titles_example = cluster_data["Job Title"].sample(
                3).values.tolist() if not cluster_data.empty else []

            top_techs = cluster_data["Top Technologies"].iloc[0]

            cluster_stat = {
                "Experience Level Mode": exp_level_mode,
                "Job Type Mode": job_type_mode,
                "Job Titles Example": job_titles_example,
                "Top Technologies": top_techs
            }
            cluster_stats_extended.append(cluster_stat)

        cluster_salary_stats = cluster_salary_stats.to_dict("records")
        for record in cluster_salary_stats:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        result = {
            "job_listing_volume": job_listing_volume,
            "average_salary": avg_salary if pd.notnull(avg_salary) else None,
            "job_categories_count": job_categories.to_dict(),
            "job_categories_stats": job_categories_stats.to_dict(),
            "cluster_salary_stats": cluster_salary_stats,
            "cluster_stats_extended": cluster_stats_extended
        }

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"success": False, "message": "An unexpected error occurred: " + str(e)})

if __name__ == "__main__":
    app.run(debug=False)
