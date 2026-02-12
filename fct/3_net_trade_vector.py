import pandas as pd
import numpy as np
import os

FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/IOT_v2"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Net_Trade_Vectors/"

COUNTRIES = [
    "AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CN", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FIGW1", "FR",
    "GB", "GR", "HR", "HU", "ID", "IE", "IN", "IT", "JP", "KR", "LT", "LU", "LV", "MT", "MX", "NL", "NO", "PL",
    "PT", "RO", "RU", "SA", "SE", "SI", "SK", "TR", "US", "ZA"
]
INDUSTRY_CODES = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]


def load_figaro_data():
    """Loads all FIGARO matrices (2010–2021) as numeric NumPy arrays."""
    W = []
    years = list(range(2010, 2022))
    for year in years:
        file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
        df = pd.read_csv(file_path, header=None)

        # Convert to numeric and drop all-empty rows/cols
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        df_numeric = df_numeric.dropna(how='all', axis=0).dropna(how='all', axis=1)

        W.append(df_numeric.to_numpy())
        print(f"Loaded FIGARO {year} matrix with shape {df_numeric.shape}")
    return W, years


def compute_net_trade_vector(W, years):
    """Computes net trade vectors for each year."""
    for idx, year in enumerate(years):
        M = W[idx].copy()

        # 1. Drop last 6 rows (value added)
        M = M[:-6, :]

        # Dimensions check: 46 countries * 64 industries = 2944 rows
        n_countries = 46
        n_industries = 64
        n_final_demand = 5

        # 2. Split into intermediate-use and final demand sections
        inter_start, inter_end = 0, n_countries * n_industries
        fd_start, fd_end = inter_end, inter_end + n_countries * n_final_demand

        inter_matrix = M[:, inter_start:inter_end]  # 2944 x 2944
        fd_matrix = M[:, fd_start:fd_end]           # 2944 x 230

        # 3. Aggregate (sum) at country level across industries
        # For intermediate use: sum every 64 columns per country
        inter_country = np.hstack([
            inter_matrix[:, i * n_industries:(i + 1) * n_industries].sum(axis=1, keepdims=True)
            for i in range(n_countries)
        ])

        # For final demand: sum every 5 columns per country
        fd_country = np.hstack([
            fd_matrix[:, i * n_final_demand:(i + 1) * n_final_demand].sum(axis=1, keepdims=True)
            for i in range(n_countries)
        ])

        # 4. Add intermediate-use and final demand per country
        total_use = inter_country + fd_country  # 2944 x 46

        # 5. Zero out intra-country flows (diagonal)
        for i in range(n_countries):
            row_start = i * n_industries
            row_end = (i + 1) * n_industries
            total_use[row_start:row_end, i] = 0

        # 6. Add export column (row sums)
        export_col = total_use.sum(axis=1, keepdims=True)

        # 7. Multiply all country columns by -1
        total_use_neg = -1 * total_use

        # 8. Replace the 0 diagonal blocks with export_col
        for i in range(n_countries):
            row_start = i * n_industries
            row_end = (i + 1) * n_industries
            total_use_neg[row_start:row_end, i] = export_col[row_start:row_end, 0]

        # 9. Convert to DataFrame and save
        col_names = COUNTRIES
        row_names = [f"{COUNTRIES[i // n_industries]}_{INDUSTRY_CODES[i % n_industries]}"
                     for i in range(total_use_neg.shape[0])]
        df_out = pd.DataFrame(total_use_neg, columns=col_names, index=row_names)

        out_path = os.path.join(OUTPUT_DIR, f"net_trade_vector_{year}.csv")
        df_out.to_csv(out_path)
        print(f"Saved net trade vector for {year} → {out_path}")


if __name__ == "__main__":
    W, years = load_figaro_data()
    compute_net_trade_vector(W, years)
    print("✅ Net trade vector computation completed for all years.")
