import os
import pandas as pd
import numpy as np

FACTORS_DIR = "/Users/nikhil/Documents/Thesis/FCT/Factor_Endowments"
SHARES_FILE = "/Users/nikhil/Documents/Thesis/FCT/Consumption_Shares/consumption_shares.xlsx"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/Predicted_FCT"
YEARS = range(2010, 2022)


def compute_fct(vc_dir, sc_path, output_dir):
    # Load Sc once since it contains all years
    sc_df = pd.read_excel(sc_path)
    sc_df.set_index(sc_df.columns[0], inplace=True)

    for year in YEARS:
        print(f"Processing {year}...")

        # ----- Load country factor endowments (Vc) -----
        vc_file = os.path.join(vc_dir, f"factor_endowments_{year}.csv")
        Vc = pd.read_csv(vc_file, index_col=0)

        # Ensure year exists in Sc file
        if str(year) not in sc_df.columns:
            raise KeyError(f"Year {year} not found in shares file!")

        # Extract Sc for this year (vector of 46 shares)
        Sc_year = sc_df[str(year)]
        Sc_year = Sc_year.loc[Vc.columns]  # Align ordering

        # Convert to row-multipliable structure (46 x 6 -> broadcast-safe)
        Sc_matrix = np.tile(Sc_year.values, (Vc.shape[0], 1))

        # ----- Compute world totals for each factor (row sums) -----
        Vw = Vc.sum(axis=1).values.reshape(-1, 1)  # shape: (6, 1)
        Vw_matrix = np.tile(Vw, (1, Vc.shape[1]))  # replicate across countries

        # ----- Factor content of trade -----
        Fc = Vc.values - (Sc_matrix * Vw_matrix)

        # Convert back to DataFrame
        Fc_df = pd.DataFrame(Fc, index=Vc.index, columns=Vc.columns)

        # Save output
        out_file = os.path.join(output_dir, f"predicted_fct_{year}.csv")
        Fc_df.to_csv(out_file)

    print("✅ All done! FCT files saved in:", output_dir)


if __name__ == "__main__":
    compute_fct(FACTORS_DIR, SHARES_FILE, OUTPUT_DIR)
