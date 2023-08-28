from technologies_list import technologies


def extract_technologies(job_description: str):
    techs_present = []

    for tech in technologies:
        if tech.lower() in job_description.lower():
            techs_present.append(tech)

    return techs_present
