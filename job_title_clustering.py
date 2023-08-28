import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import process_data
import matplotlib.pyplot as plt


def preprocess_text(text):
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()

    tokens = word_tokenize(text.lower())
    filtered_tokens = [lemmatizer.lemmatize(
        token) for token in tokens if token not in stop_words and token.isalnum()]

    return " ".join(filtered_tokens)


def find_best_k(tfidf_matrix, max_k=10):
    sil_scores = []
    K_values = range(2, max_k+1)

    for k in K_values:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(tfidf_matrix)
        sil_scores.append(silhouette_score(tfidf_matrix, kmeans.labels_))

    best_k = K_values[sil_scores.index(max(sil_scores))]

    return best_k


def cluster_job_titles(df, k=None):
    job_titles = df["Job Title"]
    job_titles_preprocessed = job_titles.apply(preprocess_text)

    vectorizer = TfidfVectorizer()
    job_titles_tfidf = vectorizer.fit_transform(job_titles_preprocessed)

    if k is None:
        k = find_best_k(job_titles_tfidf)

    kmeans = KMeans(n_clusters=k, random_state=42)
    job_titles_clusters = kmeans.fit_predict(job_titles_tfidf)

    df["Cluster"] = job_titles_clusters

    # Calculate the top 3 technologies for each cluster
    all_tech_counts = top_technologies_by_cluster(df)

    # Map each row to its corresponding cluster's top 3 technologies
    df["Top Technologies"] = df["Cluster"].apply(lambda x: all_tech_counts[x])
    
    # # Download required nltk resources
    # nltk.download("punkt", quiet=True)
    # nltk.download("stopwords", quiet=True)
    # nltk.download("wordnet", quiet=True)

    return df


def top_technologies_by_cluster(df, n=3):
    all_tech_counts = []

    k = len(df["Cluster"].unique())
    for i in range(k):
        cluster_df = df[df["Cluster"] == i]

        all_techs = []
        for tech_list in cluster_df["Technologies"]:
            all_techs += tech_list

        tech_counts = {}
        for tech in all_techs:
            if tech not in tech_counts:
                tech_counts[tech] = 0
            tech_counts[tech] += 1

        top_techs = sorted(tech_counts, key=tech_counts.get, reverse=True)[:n]
        all_tech_counts.append(', '.join(top_techs))

    return all_tech_counts


if __name__ == '__main__':
    all_jobs_file = process_data.find_latest_file("all_jobs_data_")
    all_data = process_data.read_json(all_jobs_file)
    df = pd.DataFrame(all_data)

    clustered_df = cluster_job_titles(df)

    # Show cluster stats and job title examples in each cluster
    k = len(clustered_df["Cluster"].unique())
    for i in range(k):
        cluster_df = clustered_df[clustered_df["Cluster"] == i]
        n_samples = 3
        job_titles_example = cluster_df["Job Title"].head(n_samples).tolist()

        cluster_size = len(cluster_df)
        avg_salary = cluster_df["Salary"].mean()
        salary_count = cluster_df["Salary"].count()
        exp_mode = cluster_df["Experience Level"].mode().get(0)
        job_type_mode = cluster_df["Job Type"].mode().get(0)

        print(f"Cluster {i}:")
        print(f"  Size: {cluster_size}")
        print(f"  Average Salary: {avg_salary}")
        print(f"  Salary Count: {salary_count}")
        print(f"  Experience Level Mode: {exp_mode}")
        print(f"  Job Type Mode: {job_type_mode}")
        print(f"  Job Titles Example: {', '.join(job_titles_example)}\n")
