import os
import pandas as pd
import numpy as np

FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/IOT_v2"  # <- update here
OUT_FILENAME = "FIGARO_GrossOutput_2010_2021.xlsx"
YEARS = list(range(2010, 2022))

N_COUNTRIES = 46
N_INDUSTRIES = 64
N_COLS_PROD = N_COUNTRIES * N_INDUSTRIES  # 2944
N_ROWS_SUM = N_COLS_PROD + 6              # 2950


def compute_gross_output_for_year(file_path):
    # Load CSV as string first
    df_raw = pd.read_csv(file_path, header=None, dtype=str, low_memory=False)

    # Extract industry labels from first row, skipping the first "rowLabels" column
    labels = df_raw.iloc[0, 1:N_COLS_PROD+1].tolist()

    # Convert everything except the first row and first column to numeric
    df_numeric = df_raw.iloc[1:, 1:N_COLS_PROD+1].apply(pd.to_numeric, errors='coerce')

    # Sum the rows (use all available rows, up to N_ROWS_SUM)
    rows_to_use = min(df_numeric.shape[0], N_ROWS_SUM)
    gross_output = df_numeric.iloc[:rows_to_use, :].sum(axis=0)

    gross_output.index = labels
    return gross_output


def main():
    results = {}

    for year in YEARS:
        file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
        if not os.path.exists(file_path):
            print(f"Missing file for year {year}: {file_path}")
            continue

        series = compute_gross_output_for_year(file_path)
        results[year] = series
        print(f"Processed {year}")

    # Combine all into a DataFrame
    df_out = pd.DataFrame(results)
    df_out.index.name = "Country_Industry"

    out_path = os.path.join(FIGARO_DIR, OUT_FILENAME)
    df_out.to_excel(out_path)

    print(f"\n✅ Saved correct Gross Output file to:\n   {out_path}")
    print(f"Shape: {df_out.shape} (should be 2944 rows x 12 years)")


if __name__ == "__main__":
    main()
