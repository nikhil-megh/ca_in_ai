import pandas as pd
from itertools import product

# -------- CONFIG --------
INPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/PCT_Patents_By_Country.xlsx"
BASE_YEAR = 2000
END_YEAR = 2023
DEPRECIATION_RATE = 0.15
COUNTRIES = [
    "BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT", "CY", "LV", "LT", "LU", "HU",
    "MT", "NL", "AT", "PL", "PT", "RO", "SI", "SK", "FI", "SE", "AR", "AU", "BR", "CA", "CH", "CN", "ID",
    "IN", "JP", "KR", "MX", "NO", "RU", "SA", "TR", "GB", "US", "ZA", "FIGW1"
]


def prepare_dataframe(df):
    # Ensure required columns exist
    required = {
        "Country", "Year", "Total Count", "AI Count", "Non AI Count",
        "Total Weighted Count", "AI Weighted Count", "Non AI Weighted Count"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input file is missing required columns: {missing}")

    # Normalize column names
    df = df.rename(columns=lambda c: c.strip())
    df["Year"] = df["Year"].astype(int)
    df["Country"] = df["Country"].astype(str).str.strip()

    # Convert numeric columns
    for col in required - {"Country", "Year"}:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)

    return df


def create_full_index(df):
    countries = sorted(COUNTRIES)
    years = list(range(BASE_YEAR, END_YEAR + 1))
    idx = pd.MultiIndex.from_product([countries, years], names=["Country", "Year"])
    return idx


def fill_missing_rows(df, full_index):
    df2 = df.set_index(["Country", "Year"])
    df2 = df2.reindex(full_index, fill_value=0).reset_index()
    return df2


def compute_pim_stock(group, flow_col, stock_col):
    dep = DEPRECIATION_RATE
    years = group["Year"].values
    flows = group[flow_col].values.astype(float)

    if len(years) == 0:
        return group

    stocks = []
    stock_prev = flows[0]  # Base year stock
    stocks.append(stock_prev)

    for f in flows[1:]:
        stock_t = (1 - dep) * stock_prev + f
        stocks.append(stock_t)
        stock_prev = stock_t

    group[stock_col] = stocks
    return group


def main(input_path=INPUT_PATH):
    df = pd.read_excel(input_path)
    df = prepare_dataframe(df)

    # Create full index to fill missing years/countries
    full_index = create_full_index(df)
    df_full = fill_missing_rows(df, full_index)
    df_full = df_full.sort_values(["Country", "Year"]).reset_index(drop=True)

    # Compute all six stock columns
    out_parts = []
    group_cols = ["Country"]
    stock_pairs = [
        ("Total Count", "Total Stock"),
        ("AI Count", "AI Stock"),
        ("Non AI Count", "Non AI Stock"),
        ("Total Weighted Count", "Total Weighted Stock"),
        ("AI Weighted Count", "AI Weighted Stock"),
        ("Non AI Weighted Count", "Non AI Weighted Stock")
    ]

    for _, g in df_full.groupby(group_cols, sort=True):
        g = g.sort_values("Year")
        for flow_col, stock_col in stock_pairs:
            g = compute_pim_stock(g, flow_col, stock_col)
        out_parts.append(g)

    result = pd.concat(out_parts, axis=0).sort_values(["Country", "Year"]).reset_index(drop=True)

    # Ensure all 6 stock columns exist
    for _, stock_col in stock_pairs:
        if stock_col not in result.columns:
            result[stock_col] = 0.0

    # reorder columns
    result = result[[
        "Country", "Year",
        "Total Count", "AI Count", "Non AI Count",
        "Total Stock", "AI Stock", "Non AI Stock",
        "Total Weighted Count", "AI Weighted Count", "Non AI Weighted Count",
        "Total Weighted Stock", "AI Weighted Stock", "Non AI Weighted Stock"
    ]]

    # ✅ Save back to the same input file
    with pd.ExcelWriter(input_path, mode="w", engine="openpyxl") as writer:
        result.to_excel(writer, index=False)

    print(f"✅ Stock columns added and saved to the same file: {input_path}")


if __name__ == "__main__":
    main()
