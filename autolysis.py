import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# List of dataset names
datasets = ["goodreads", "happiness", "media"]

# Function to process dataset
def process_dataset(csv_file, dataset_name):
    # Load the dataset
    try:
        data = pd.read_csv(csv_file, encoding='utf-8')
        print(f"Successfully loaded {csv_file} with UTF-8 encoding!")
    except UnicodeDecodeError:
        data = pd.read_csv(csv_file, encoding='ISO-8859-1')
        print(f"Successfully loaded {csv_file} with ISO-8859-1 encoding!")

    # Data Exploration
    print(f"\nExploring dataset: {dataset_name}")
    missing_values = data.isnull().sum()
    missing_percentage = (missing_values / len(data)) * 100
    summary = {
        "shape": data.shape,
        "columns": list(data.columns),
        "missing_values": missing_values.to_dict(),
        "summary_statistics": data.describe(include="all").to_dict(),
    }

    # Create directory for the dataset if not exists
    output_dir = os.path.join(os.getcwd(), dataset_name)
    os.makedirs(output_dir, exist_ok=True)

    # Save Summary to JSON
    with open(os.path.join(output_dir, "data_summary.json"), "w") as file:
        json.dump(summary, file, indent=4)
    
    # Generate Correlation Heatmap and Boxplot
    numeric_data = data.select_dtypes(include=["float64", "int64"])
    if not numeric_data.empty:
        correlation_matrix = numeric_data.corr()

        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True)
        plt.title(f"{dataset_name.capitalize()} Correlation Heatmap")
        plt.tight_layout()
        heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.savefig(heatmap_path)
        plt.close()

        plt.figure(figsize=(8, 6))
        sns.boxplot(data=numeric_data, orient="h", palette="coolwarm")
        plt.title(f"{dataset_name.capitalize()} Box Plot of Numerical Features")
        plt.tight_layout()
        boxplot_path = os.path.join(output_dir, "boxplot.png")
        plt.savefig(boxplot_path)
        plt.close()

    # Create README.md
    readme_content = f"""
# {dataset_name.capitalize()} Data Analysis

## Data Overview
Summary of the {dataset_name} dataset contents.

## Key Insights
- Insight 1: Description
- Insight 2: Description

## Visualizations
![Boxplot](boxplot.png)
![Heatmap](correlation_heatmap.png)
    """

    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, 'w') as readme_file:
        readme_file.write(readme_content)
    
    print(f"Generated files for {dataset_name}: README.md, boxplot.png, correlation_heatmap.png")

# Loop through each dataset and process
for dataset in datasets:
    csv_file = f"{dataset}.csv"
    process_dataset(csv_file, dataset)

# Send the output for AI narrative generation (Optional)
# Load environment variables and OpenAI API token
aiproxy_token = os.getenv('AIPROXY_TOKEN')

if not aiproxy_token:
    print("Error: AIPROXY_TOKEN not found in environment variables.")
else:
    openai.api_key = aiproxy_token
    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"  # Corrected path

    # Construct prompt based on dataset summary
    prompt = """
### Dataset Analysis Summary
- Shape: {summary['shape']}
- Columns: {', '.join(summary['columns'])}

### Summary Statistics
{json.dumps(summary['summary_statistics'], indent=4)}

### Missing Data
{json.dumps(summary['missing_values'], indent=4)}

### Correlation Matrix
{correlation_matrix_content}

### Outlier Detection
{json.dumps(summary['outliers'], indent=4)}

### Task:
Please generate a detailed narrative summarizing the analysis, findings, and implications. This should include:
1. An overview of the dataset.
2. A description of the analysis performed (summary statistics, correlation matrix, outlier detection).
3. Insights derived from the data (e.g., patterns, trends, key observations).
4. Any recommendations or actions that can be taken based on these insights.
    """
    # Send to OpenAI model for narrative generation
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Use the 'gpt-4o-mini' model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )

        narrative = response['choices'][0]['message']['content'].strip()
        if narrative:
            with open("README.md", "w") as readme_file:
                readme_file.write(narrative)
            print("Narrative saved to 'README.md'.")
        else:
            print("Warning: The generated narrative is empty.")

    except openai.error.OpenAIError as e:
        print(f"Error generating narrative: {e}")
# Function to create README.md for each dataset
def create_readme(dataset_name, summary):
    readme_content = f"""
# {dataset_name.capitalize()} Data Analysis

## Data Overview
Summary of the {dataset_name} dataset contents.

## Key Insights
- Insight 1: Description
- Insight 2: Description

## Visualizations
![Boxplot](boxplot.png)
![Heatmap](correlation_heatmap.png)
    """
    
    # Create the README.md file for each dataset in their respective folder
    readme_path = os.path.join(dataset_name, "README.md")
    with open(readme_path, 'w') as readme_file:
        readme_file.write(readme_content)
    
    print(f"Generated {dataset_name}/README.md")

# Now call the create_readme function for each dataset
for dataset in datasets:
    create_readme(dataset, summary)
