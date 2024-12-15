# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "matplotlib",
#   "seaborn",
#   "openai",
#   "numpy",
#   "ipykernel",
# ]
# ///

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import openai

# Configure OpenAI API to use the AI Proxy
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"
openai.api_key = os.getenv("AIPROXY_TOKEN")  # Fetch the token from the environment variable


# Test API Proxy Connectivity
def test_openai_connection():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test connection to the AI Proxy"}]
        )
        print("API Proxy Test Successful: ", response.choices[0].message["content"])
    except Exception as e:
        print(f"API Proxy Test Failed: {e}")


def main(filename):
    try:
        # Load the dataset with proper encoding handling
        print(f"Loading dataset: {filename}")
        try:
            data = pd.read_csv(filename, encoding="utf-8")  # Default to UTF-8
        except UnicodeDecodeError:
            print(f"UTF-8 decoding failed for {filename}. Trying ISO-8859-1...")
            data = pd.read_csv(filename, encoding="ISO-8859-1")  # Fallback to ISO-8859-1

        # Create output directory based on dataset name
        dataset_name = os.path.splitext(os.path.basename(filename))[0]
        output_dir = f"./{dataset_name}"
        os.makedirs(output_dir, exist_ok=True)

        # Perform analysis
        analyze_data(data, dataset_name, output_dir)
    except Exception as e:
        print(f"Error processing {filename}: {e}")


def analyze_data(data, dataset_name, output_dir):
    # Step 1: Basic Analysis
    print("Performing basic data analysis...")
    summary = data.describe(include="all").transpose()
    missing_values = data.isnull().sum()

    # Save basic analysis results
    summary.to_csv(f"{output_dir}/summary.csv")
    missing_values.to_csv(f"{output_dir}/missing_values.csv")

    # Step 2: Correlation Matrix
    correlations = data.corr(numeric_only=True)
    save_correlation_heatmap(correlations, output_dir)

    # Step 3: Missing Values Visualization
    save_missing_values_chart(missing_values, output_dir)

    # Step 4: Outlier Detection
    outliers = detect_outliers(data)

    # Step 5: Generate Insights with LLM
    insights = generate_llm_insights(data, summary, missing_values, outliers)

    # Step 6: Write README.md
    write_readme(output_dir, dataset_name, insights)


def save_correlation_heatmap(correlations, output_dir):
    """Saves a heatmap of the correlation matrix."""
    if correlations.empty:
        print("No numeric data for correlation heatmap.")
        return
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlations, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Matrix")
    plt.savefig(f"{output_dir}/correlation_matrix.png")
    plt.close()


def save_missing_values_chart(missing_values, output_dir):
    """Saves a bar chart of missing values."""
    if missing_values.sum() == 0:
        print("No missing values to plot.")
        return
    plt.figure(figsize=(8, 6))
    missing_values.plot(kind="bar", color="skyblue")
    plt.title("Missing Values by Column")
    plt.ylabel("Number of Missing Values")
    plt.savefig(f"{output_dir}/missing_values_chart.png")
    plt.close()


def detect_outliers(data):
    """Detects outliers in numerical columns using the IQR method."""
    outliers = {}
    for column in data.select_dtypes(include=np.number).columns:
        Q1 = data[column].quantile(0.25)
        Q3 = data[column].quantile(0.75)
        IQR = Q3 - Q1
        condition = (data[column] < Q1 - 1.5 * IQR) | (data[column] > Q3 + 1.5 * IQR)
        outliers[column] = data[column][condition].tolist()
    return outliers


def generate_llm_insights(data, summary, missing_values, outliers):
    """Generates insights using GPT-4o-Mini."""
    try:
        # Prepare column information
        columns_info = [{"name": col, "dtype": str(data[col].dtype)} for col in data.columns]
        
        # Create the prompt
        prompt = (
            f"The dataset has {len(data)} rows and {len(data.columns)} columns.\n"
            f"Column Details: {columns_info}\n"
            f"Summary Statistics: {summary.to_dict()}\n"
            f"Missing Values: {missing_values.to_dict()}\n"
            f"Outliers Detected: {outliers}\n"
            "Provide insights, highlight significant findings, and suggest additional analyses."
        )

        # Configure OpenAI API
        openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"  # Use the proxy endpoint

        # Make the ChatCompletion API call
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data scientist."},
                {"role": "user", "content": prompt},
            ]
        )
        # Return the content of the response
        return response.choices[0].message["content"]

    except Exception as e:
        print(f"Error generating LLM insights: {str(e)}")
        return "Could not generate insights due to an unexpected error."


def write_readme(output_dir, dataset_name, insights):
    """Creates a README.md file summarizing the analysis."""
    with open(f"{output_dir}/README.md", "w") as readme:
        readme.write(f"# Analysis of {dataset_name}\n")
        readme.write("## Dataset Overview\n")
        readme.write(f"This analysis is based on the `{dataset_name}` dataset.\n\n")
        readme.write("## Insights\n")
        readme.write(insights)
        readme.write("\n\n## Visualizations\n")
        readme.write("### Correlation Matrix\n")
        readme.write(f"![Correlation Matrix](./correlation_matrix.png)\n\n")
        readme.write("### Missing Values Chart\n")
        readme.write(f"![Missing Values Chart](./missing_values_chart.png)\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <filename.csv>")
    else:
        main(sys.argv[1])
