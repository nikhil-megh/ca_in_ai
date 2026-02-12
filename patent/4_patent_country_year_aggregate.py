import pandas as pd
import os

# -------- CONFIGURATION --------
#INPUT_FILE = "/Users/nikhil/Documents/Patents/Extended_Triadic_AI_Patents/Extended_Triadic_AI_Patents.xlsx"
INPUT_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_Patents/PCT_AI_Patents.csv"
OUTPUT_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_Patents/PCT_AI_Patents_By_Country_Year.xlsx"


def aggregate_country_year(input_path, output_path):
    # Read Excel file
    # df = pd.read_excel(input_path)
    df = pd.read_csv(input_path, dtype=str)

    # Ensure column names are clean (remove extra spaces)
    df.columns = df.columns.str.strip()

    # Check required columns exist
    required_cols = ["Applicant Residence Country", "Application Year", "Patent Weight"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Convert Patent Weight to numeric (non-numeric become NaN → replaced with 0)
    df["Patent Weight"] = pd.to_numeric(df["Patent Weight"], errors="coerce").fillna(0)

    # Group by Country and Year
    agg_df = (
        df.groupby(["Applicant Residence Country", "Application Year"])
        .agg(
            Count=("Application Id", "count"),  # number of applications
            Weighted_Count=("Patent Weight", "sum")  # sum of Patent Weights
        )
        .reset_index()
    )

    # Rename columns for clarity
    agg_df.rename(columns={
        "Applicant Residence Country": "Country",
        "Application Year": "Year"
    }, inplace=True)

    # Sort the data for better readability
    agg_df.sort_values(by=["Country", "Year"], inplace=True)

    # Export to Excel
    agg_df.to_excel(output_path, index=False)

    print(f"✅ Aggregated file saved to: {output_path}")
    print(agg_df.head())


if __name__ == "__main__":
    aggregate_country_year(INPUT_FILE, OUTPUT_FILE)
