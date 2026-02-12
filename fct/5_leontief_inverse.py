import os
import numpy as np
import pandas as pd

FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/IOT_v2"
GO_FILE = "/Users/nikhil/Documents/Thesis/Figaro/FIGARO_GrossOutput_2010_2021.xlsx"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Technical_Coefficient_Matrix"
N_SECTORS = 2944  # 46 countries x 64 industries
YEARS = list(range(2010, 2022))


def load_IIO_matrix(year):
    file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
    df = pd.read_csv(file_path, header=None)

    # Row labels are in column 0
    row_labels = df.iloc[1:N_SECTORS+1, 0].values

    # Column labels are in row 0, starting from col 1
    col_labels = df.iloc[0, 1:N_SECTORS+1].values

    # Extract numeric block (skip row 0 label row + col 0)
    iio_numeric = df.iloc[1:N_SECTORS+1, 1:N_SECTORS+1].apply(pd.to_numeric, errors='coerce')

    # Reassign proper names
    iio_numeric.index = row_labels
    iio_numeric.columns = col_labels

    print(f"✅ Loaded IIO for {year} → {iio_numeric.shape}")
    print(iio_numeric.head())
    return iio_numeric


def load_GO_vector(year):
    df_go = pd.read_excel(GO_FILE, index_col=0)
    df_go.columns = df_go.columns.map(str)
    return df_go[str(year)].values  # returns numpy vector


def compute_A_matrix(IIO, GO):
    eps_vec = np.full_like(GO, 1e-8)
    GOnz = GO + eps_vec
    A = IIO.values @ np.linalg.inv(np.diag(GOnz))
    return pd.DataFrame(A, index=IIO.index, columns=IIO.index)


def compute_leontief_inverse(A):
    I = np.identity(A.shape[0])
    L = np.linalg.inv(I - A.values)
    return pd.DataFrame(L, index=A.index, columns=A.columns)


def process_year(year):
    print(f"Processing {year}...")

    IIO = load_IIO_matrix(year)
    GO = load_GO_vector(year)

    A = compute_A_matrix(IIO, GO)
    L = compute_leontief_inverse(A)

    # Save results
    A.to_csv(os.path.join(OUTPUT_DIR, f"technical_coefficients_matrix_{year}.csv"))
    L.to_csv(os.path.join(OUTPUT_DIR, f"leontief_matrix_{year}.csv"))

    print(f"✅ Year {year} complete: A and L saved")


if __name__ == "__main__":
    for yr in YEARS:
        process_year(yr)

    print("🎉 All years processed successfully!")
