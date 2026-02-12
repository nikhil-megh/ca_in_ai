import pandas as pd
from itertools import product

# -------- CONFIG --------
INPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/PCT_Patents_By_Industry.xlsx"
BASE_YEAR = 2000
END_YEAR = 2021
DEPRECIATION_RATE = 0.15
COUNTRIES = ["BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT", "CY", "LV", "LT", "LU", "HU",
             "MT", "NL", "AT", "PL", "PT", "RO", "SI", "SK", "FI", "SE", "AR", "AU", "BR", "CA", "CH", "CN", "ID",
             "IN", "JP", "KR", "MX", "NO", "RU", "SA", "TR", "GB", "US", "ZA", "FIGW1"]
INDUSTRIES = ["A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23",
              "C24", "C25", "C26", "C27", "C28", "C29", "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45",
              "G46", "G47", "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63", "K64", "K65",
              "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77", "N78", "N79", "N80T82", "O84", "P85", "Q86",
              "Q87_88", "R90T92", "R93", "S94", "S95", "S96", "T", "U"]


def prepare_dataframe(df):
    # ensure required columns exist
    required = {"Country", "Industry Code", "Year", "Total Count", "AI Count", "Non AI Count"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input file is missing required columns: {missing}")

    # normalize column names (strip)
    df = df.rename(columns=lambda c: c.strip())
    df["Year"] = df["Year"].astype(int)
    df["Country"] = df["Country"].astype(str).str.strip()
    df["Industry Code"] = df["Industry Code"].astype(str).str.strip()

    # convert counts to numeric, treating missing as 0
    for col in ["Total Count", "AI Count", "Non AI Count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)

    return df


def create_full_index(df):
    # all combinations of Country x Industry Code x Year (BASE_YEAR..END_YEAR)
    countries = sorted(COUNTRIES)
    industry_codes = sorted(INDUSTRIES)
    years = list(range(BASE_YEAR, END_YEAR + 1))
    idx = pd.MultiIndex.from_product([countries, industry_codes, years],
                                     names=["Country", "Industry Code", "Year"])
    return idx


def fill_missing_rows(df, full_index):
    # pivot to MultiIndex and reindex so missing rows become present with zeros
    df2 = df.set_index(["Country", "Industry Code", "Year"])
    # keep original columns (counts). Reindex to full_index and fill zeros for counts
    df2 = df2.reindex(full_index, fill_value=0).reset_index()
    # keep only necessary columns (if extra cols were present, they remain)
    return df2


def compute_pim_stock(group, flow_col, stock_col):
    dep = DEPRECIATION_RATE
    years = group["Year"].values
    flows = group[flow_col].values.astype(float)

    stocks = []
    if len(years) == 0:
        return group

    # base year stock = flow at base year (conventional simple PIM)
    stock_prev = flows[0]  # for BASE_YEAR
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

    # create full index making missing rows explicit (with zero flows)
    full_index = create_full_index(df)
    df_full = fill_missing_rows(df, full_index)

    # sort so groups are processed in chronological order
    df_full = df_full.sort_values(["Country", "Industry Code", "Year"]).reset_index(drop=True)

    # compute AI Stock and Non AI Stock per Country + Industry Code
    out_parts = []
    group_cols = ["Country", "Industry Code"]
    for _, g in df_full.groupby(group_cols, sort=True):
        g = g.sort_values("Year")
        g = compute_pim_stock(g, flow_col="Total Count", stock_col="Total Stock")
        g = compute_pim_stock(g, flow_col="AI Count", stock_col="AI Stock")
        g = compute_pim_stock(g, flow_col="Non AI Count", stock_col="Non AI Stock")
        out_parts.append(g)

    result = pd.concat(out_parts, axis=0).sort_values(["Country", "Industry Code", "Year"]).reset_index(drop=True)

    # If some older/newer columns are missing (unlikely), ensure stock cols exist
    for col in ["AI Stock", "Non AI Stock"]:
        if col not in result.columns:
            result[col] = 0.0

    # reorder columns
    result = result[[
        "Country", "Industry Code", "Year",
        "Total Count", "AI Count", "Non AI Count",
        "Total Stock", "AI Stock", "Non AI Stock"
    ]]

    # ✅ Save back to the same input file
    with pd.ExcelWriter(input_path, mode="w", engine="openpyxl") as writer:
        result.to_excel(writer, index=False)
    print(f"✅ Stock columns added and saved to the same file: {input_path}")


if __name__ == "__main__":
    main()
