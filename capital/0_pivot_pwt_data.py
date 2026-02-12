import pandas as pd
import os

# -------- CONFIGURATION --------
INPUT_PATH = "/Users/nikhil/Downloads/pwt_filtered.csv"
OUTPUT_PATH = "/Users/nikhil/Downloads/FIGARO_Country_NetCapitalStock_CurrentPPP_USD_2021.xlsx"

START_YEAR = 2010
END_YEAR = 2023


def create_capital_price_pivots(input_path: str, output_path: str):
    # Read CSV
    df = pd.read_csv(input_path, dtype={"countrycode": str, "year": int, "cn": float, "pl_n": float})

    # Filter year range
    df = df[(df["year"] >= START_YEAR) & (df["year"] <= END_YEAR)]

    # Create Excel writer
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for country, group in df.groupby("countrycode"):
            # --- Pivot for capital (cn) ---
            pivot_cn = group.pivot_table(
                index=None,
                columns="year",
                values="cn",
                aggfunc="first"
            )
            pivot_cn = pivot_cn.reindex(sorted(pivot_cn.columns), axis=1)
            pivot_cn.to_excel(writer, sheet_name=f"{country}_capital", index=False)

            # --- Pivot for price (pl_n) ---
            pivot_pln = group.pivot_table(
                index=None,
                columns="year",
                values="pl_n",
                aggfunc="first"
            )
            pivot_pln = pivot_pln.reindex(sorted(pivot_pln.columns), axis=1)
            pivot_pln.to_excel(writer, sheet_name=f"{country}_price", index=False)

    print(f"✅ Done. Created capital and price pivot sheets for each country in: {output_path}")


if __name__ == "__main__":
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Error: Input file not found at {INPUT_PATH}")
    else:
        create_capital_price_pivots(INPUT_PATH, OUTPUT_PATH)
