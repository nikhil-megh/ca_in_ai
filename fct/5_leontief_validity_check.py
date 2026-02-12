import os
import numpy as np
import pandas as pd

OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Technical_Coefficient_Matrix"
YEARS = list(range(2010, 2024))


def validate_year(year):
    print(f"\n--- Validating year {year} ---")

    A_path = os.path.join(OUTPUT_DIR, f"technical_coefficients_matrix_{year}.csv")
    L_path = os.path.join(OUTPUT_DIR, f"leontief_matrix_{year}.csv")

    # Load matrices
    A = pd.read_csv(A_path, index_col=0)
    L = pd.read_csv(L_path, index_col=0)

    # Identity matrix (same size)
    n = A.shape[0]
    I = np.identity(n)

    # Compute test matrix (I - A) @ L
    M = (I - A.values) @ L.values

    # Wrap back into DataFrame with same labels
    M_df = pd.DataFrame(M, index=A.index, columns=A.columns)

    # Compute error metrics
    deviation = np.abs(M - I).max()
    avg_error = np.abs(M - I).mean()

    print(f"Max deviation from identity: {deviation:.6e}")
    print(f"Mean error: {avg_error:.6e}")

    # Save result for review
    out_file = os.path.join(OUTPUT_DIR, f"validity_check_identity_{year}.csv")
    M_df.to_csv(out_file)
    print(f"✅ Saved validity test to: {out_file}")


if __name__ == "__main__":
    for yr in YEARS:
        validate_year(yr)

    print("\n🎉 Validity check for all years complete!")
