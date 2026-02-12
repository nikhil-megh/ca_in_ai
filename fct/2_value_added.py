import os
import pandas as pd
import numpy as np

FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/IOT_v2"  # <- update here
OUT_FILENAME = "FIGARO_ValueAdded_2010_2021.xlsx"
YEARS = list(range(2010, 2022))

N_COUNTRIES = 46
N_INDUSTRIES = 64
N_COLS_PROD = N_COUNTRIES * N_INDUSTRIES  # 2944


def compute_value_added_for_year(file_path):
    # Load CSV as string first
    df_raw = pd.read_csv(file_path, header=None, dtype=str, low_memory=False)

    # Extract industry labels from first row, skipping first "rowLabels" column
    labels = df_raw.iloc[0, 1:N_COLS_PROD+1].tolist()

    # Convert everything except first row & first column to numeric
    df_numeric = df_raw.iloc[1:, 1:N_COLS_PROD+1].apply(pd.to_numeric, errors='coerce')

    # We only want the **last 6 rows** (usually value added rows)
    last_6_rows = df_numeric.tail(6)

    # Sum across the last 6 rows
    value_added = last_6_rows.sum(axis=0)
    value_added.index = labels

    return value_added


def main():
    results = {}

    for year in YEARS:
        file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
        if not os.path.exists(file_path):
            print(f"Missing file for year {year}: {file_path}")
            continue

        series = compute_value_added_for_year(file_path)
        results[year] = series
        print(f"Processed {year}")

    # Combine into DataFrame
    df_out = pd.DataFrame(results)
    df_out.index.name = "Country_Industry"

    out_path = os.path.join(FIGARO_DIR, OUT_FILENAME)
    df_out.to_excel(out_path)

    print("\n✅ Saved Value Added file:")
    print("   ", out_path)
    print(f"Shape: {df_out.shape} (should be 2944 rows x 12 years)")


if __name__ == "__main__":
    main()
