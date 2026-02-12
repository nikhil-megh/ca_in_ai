import os
import numpy as np
import pandas as pd

FACTORS_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Factor_Vectors"
LEONTIEF_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Leontief_Inverse_Matrix"
TRADE_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Net_Trade_Vectors"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/Measured_FCT"
GO_FILE = "/Users/nikhil/Documents/Thesis/Figaro/FIGARO_GrossOutput_2010_2021.xlsx"

YEARS = list(range(2010, 2022))


def compute_fct(year, go_df):
    print(f"Processing FCT for {year}...")

    # Load factor matrix (6 x 2944)
    E = pd.read_csv(
        os.path.join(FACTORS_DIR, f"factors_{year}.csv"),
        index_col=0
    )
    print("E head")
    print(E.head())

    # Load Leontief inverse (2944 x 2944)
    L = pd.read_csv(
        os.path.join(LEONTIEF_DIR, f"leontief_matrix_{year}.csv"),
        index_col=0
    )

    # Load net trade matrix (2944 x 46)
    T = pd.read_csv(
        os.path.join(TRADE_DIR, f"net_trade_vector_{year}.csv"),
        index_col=0
    )

    # ✅ Align & extract GO column for this year
    year_col = str(year)
    if year_col not in go_df.columns:
        raise KeyError(f"Year {year} missing in GO dataset!")

    GO = go_df[year_col]
    GO_series = GO.replace(0, np.nan)

    # Check alignment of sectors:
    if not (list(E.columns) == list(L.index) == list(T.index)):
        raise ValueError(f"Sector alignment mismatch in year {year}!")

    # ✅ Normalize E by GO → factor per unit gross output
    E_norm = E.div(GO_series)
    E_norm = E_norm.fillna(0)
    print("E_norm head")
    print(E_norm.head())

    # Compute: f = E · L · T  -> (6 x 2944) · (2944 × 2944) · (2944 x 46) = (6 x 46)
    f = E_norm.values @ L.values @ T.values
    f_df = pd.DataFrame(f, index=E.index, columns=T.columns)

    # Save
    outfile = os.path.join(OUTPUT_DIR, f"measured_fct_{year}.csv")
    f_df.to_csv(outfile)

    print(f"✅ saved: {outfile}")


if __name__ == "__main__":
    # ---- Load Gross Output once ----
    go_df = pd.read_excel(GO_FILE, index_col=0)
    go_df.columns = go_df.columns.map(str)

    for yr in YEARS:
        compute_fct(yr, go_df)

    print("\n🎉 Factor content of trade calculated for all years!")
