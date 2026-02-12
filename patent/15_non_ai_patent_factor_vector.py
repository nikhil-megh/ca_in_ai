import pandas as pd
import os

# -------- CONFIGURATION --------
INPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/PCT_Patents_By_Industry.xlsx"
OUTPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/NON_AI_PATENTS_figaro2025.xlsx"
SHEET_NAME = "Sheet1"
START_YEAR = 2010
END_YEAR = 2021


def main():
    # -------- LOAD DATA --------
    df = pd.read_excel(INPUT_PATH, sheet_name=SHEET_NAME)

    # Ensure required columns exist
    required_cols = [
        "Country", "Industry Code", "Year",
        "Total Count", "AI Count", "Non AI Count",
        "Total Stock", "AI Stock", "Non AI Stock"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in input file: {missing}")

    # Filter for years 2010–2023
    df = df[(df["Year"] >= START_YEAR) & (df["Year"] <= END_YEAR)]

    # Create combined key: Country_IndustryCode
    df["Country_Industry"] = df["Country"].astype(str) + "_" + df["Industry Code"].astype(str)

    # -------- CREATE PIVOT TABLE --------
    pivot = df.pivot_table(
        index="Country_Industry",
        columns="Year",
        values="Non AI Stock",
        aggfunc="mean"  # in case multiple rows exist per combination
    )

    # Sort columns and rows for neatness
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    pivot = pivot.sort_index()

    # -------- EXPORT --------
    pivot.to_excel(OUTPUT_PATH, sheet_name="Final")

    print(f"✅ Pivot table created successfully and saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
