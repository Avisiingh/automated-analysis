import pandas as pd
import sys
import os
import seaborn as sns
import matplotlib.pyplot as plt
import json
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the script accepts a file path as an argument
if len(sys.argv) != 2:
    print("Usage: python autolysis.py <path_to_csv>")
    sys.exit(1)

# Get the file path from the command-line arguments
csv_file = sys.argv[1]

# Try loading the CSV file with a fallback for encoding issues
try:
    data = pd.read_csv(csv_file, encoding='utf-8')  # Default encoding
    print(f"Successfully loaded {csv_file} with UTF-8 encoding!")
except UnicodeDecodeError:
    try:
        # Retry with a common alternative encoding
        data = pd.read_csv(csv_file, encoding='ISO-8859-1')  
        print(f"Successfully loaded {csv_file} with ISO-8859-1 encoding!")
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        sys.exit(1)

# Display the first 5 rows
print("Here are the first 5 rows of the dataset:")
print(data.head())

# Step 4: Explore and Prepare the Dataset
print("\n--- Data Exploration ---")

# 1. Basic Information
print(f"Dataset Shape: {data.shape}")
print("\nColumn Names and Data Types:")
print(data.dtypes)

print("\nSummary Statistics:")
print(data.describe(include='all'))  # Include non-numeric columns too

# 2. Check for Missing Values
missing_values = data.isnull().sum()
missing_percentage = (missing_values / len(data)) * 100
print("\nMissing Values (per column):")
print(pd.DataFrame({"Missing Values": missing_values, "Percentage": missing_percentage}))

# 3. Display Sample Data
print("\nSample Data (First 5 Rows):")
print(data.head())

# 4. Save Findings for LLM
summary = {
    "shape": data.shape,
    "columns": list(data.columns),
    "missing_values": missing_values.to_dict(),
    "sample_data": data.head().to_dict(),
    "summary_statistics": data.describe(include="all").to_dict(),
}

# Optional: Save summary to a file for debugging or later use
with open("data_summary.json", "w") as file:
    json.dump(summary, file, indent=4)

# Step 5.1: Correlation Analysis
print("\n--- Correlation Analysis ---")

# Select only numerical columns for correlation
numeric_data = data.select_dtypes(include=["float64", "int64"])

if not numeric_data.empty:
    correlation_matrix = numeric_data.corr()

    print("\nCorrelation Matrix:")
    print(correlation_matrix)

    # Save the correlation matrix to a CSV file
    output_dir = os.path.join(os.getcwd(), os.path.splitext(os.path.basename(csv_file))[0])
    os.makedirs(output_dir, exist_ok=True)
    correlation_matrix_path = os.path.join(output_dir, "correlation_matrix.csv")
    correlation_matrix.to_csv(correlation_matrix_path)

    print(f"Correlation matrix saved as: {correlation_matrix_path}")

    # Generate a heatmap for correlations
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True)
    plt.title("Correlation Heatmap")
    plt.tight_layout()

    heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
    plt.savefig(heatmap_path)
    print(f"Correlation heatmap saved as: {heatmap_path}")
    plt.close()
else:
    print("No numerical columns found for correlation analysis.")

# Step 5.2: Outlier Detection
print("\n--- Outlier Detection ---")

# Function to calculate z-scores manually
def calculate_z_scores(df):
    z_scores = (df - df.mean()) / df.std()
    return z_scores

if not numeric_data.empty:
    # Calculate z-scores manually
    z_scores = calculate_z_scores(numeric_data)
    
    # Identify outliers (z-score > 3 or < -3)
    outliers = (z_scores.abs() > 3).sum()

    print("\nOutliers detected in each column:")
    print(outliers)

    # Add outliers information to summary
    summary['outliers'] = outliers.to_dict()

    # Save outlier information for debugging
    outlier_info = outliers.to_dict()
    with open("outliers.json", "w") as file:
        json.dump(outlier_info, file, indent=4)
    print("Outlier information saved as 'outliers.json'.")
else:
    print("No numerical columns found for outlier detection.")

# Step 6: Data Visualization
print("\n--- Data Visualization ---")

# 6.1: Box Plot for Outliers
if not numeric_data.empty:
    plt.figure(figsize=(8, 6))
    sns.boxplot(data=numeric_data, orient="h", palette="coolwarm")
    plt.title("Box Plot of Numerical Features (Outliers Highlighted)")
    plt.tight_layout()

    boxplot_path = os.path.join(output_dir, "boxplot.png")
    plt.savefig(boxplot_path)
    print(f"Box plot saved as: {boxplot_path}")
    plt.close()
else:
    print("No numerical data available for box plot.")

# Prepare the prompt for LLM
with open(correlation_matrix_path, 'r') as f:
    correlation_matrix_content = f.read()

prompt = f"""
### Dataset Overview
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

# Get API token from environment variables
aiproxy_token = os.getenv('AIPROXY_TOKEN')

if not aiproxy_token:
    print("Error: AIPROXY_TOKEN not found in environment variables.")
    sys.exit(1)

# Set the base URL for AI Proxy
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"  # Corrected path

# Set the API key to the AIPROXY_TOKEN
openai.api_key = aiproxy_token

# Attempt to send the prompt to LLM and get a narrative
try:
    response = openai.ChatCompletion.create(
      model="gpt-4o-mini",  # Use the 'gpt-4o-mini' model
      messages=[{"role": "user", "content": prompt}],
      max_tokens=1000,
      temperature=0.7
    )

    # Extract the response (narrative)
    narrative = response['choices'][0]['message']['content'].strip()

    # Debug: Print the generated narrative to check if it's empty or malformed
    print("\n--- Generated Narrative ---")
    print(narrative)

    # Check if the narrative is empty
    if not narrative:
        print("Warning: The generated narrative is empty.")
    else:
        # Save the narrative to README.md
        with open("README.md", "w") as readme_file:
            readme_file.write(narrative)
        
        print("Narrative saved to 'README.md'.")
except openai.error.OpenAIError as e:
    print(f"Error generating narrative: {e}")
    sys.exit(1)
