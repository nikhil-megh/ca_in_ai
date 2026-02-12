import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
INPUT_XLSX = "/Users/nikhil/Documents/Thesis/Labour/Labour_Industry_Summary.xlsx"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/Labour"

# Sheet constants
SHEET_GLOBAL_LABOUR = "Global_Labour_Industry_Share"
SHEET_EU_LABOUR = "EU_Labour_Industry_Share"

# Year range for trends
TREND_START = 2010
TREND_END = 2023
TREND_YEARS = list(range(TREND_START, TREND_END + 1))


# ---------- Helpers ----------
def safe_convert_year_cols(df):
    """
    Convert columns that look like years (e.g. "2000", 2000, '2000.0') to ints.
    Keeps the index (row labels) as-is.
    """
    new_cols = []
    for c in df.columns:
        try:
            # try numeric conversion
            cn = float(str(c).strip())
            if cn.is_integer():
                new_cols.append(int(cn))
            else:
                new_cols.append(c)
        except Exception:
            new_cols.append(c)
    df.columns = new_cols
    return df


def normalize_shares_series(s):
    """
    Convert to float and if series sums >>1 assume percentages (0-100) and divide by 100.
    Returns series of fractions (0-1).
    """
    s = s.astype(float).copy()
    total = s.sum()
    if total > 1.0001:
        s = s / 100.0
    return s


def add_missing_share(total_rows_sum, remaining_sum):
    """
    Missing share (rest of world/industries) = max(0, 1 - total_rows_sum).
    Others = remaining_sum (rows not in top N) + missing_share.
    """
    missing = max(0.0, 1.0 - total_rows_sum)
    return remaining_sum + missing


# ---------- Plotting ----------
def pie_top_n_with_others(series_2023, top_n, title, outpath):
    """
    series_2023: pd.Series (index=countries or industries), values in fractions 0-1 or percents 0-100
    top_n: number of top slices to show; rest collapsed into 'Others' which includes missing share up to 1.0
    """
    s = normalize_shares_series(series_2023).fillna(0.0)
    total_rows_sum = s.sum()
    s_sorted = s.sort_values(ascending=False)
    top = s_sorted.iloc[:top_n]
    remaining = s_sorted.iloc[top_n:]
    others_value = add_missing_share(total_rows_sum, remaining.sum())
    labels = list(top.index) + ["Others"]
    sizes = list(top.values) + [others_value]
    sizes = [max(0.0, float(x)) for x in sizes]  # clip tiny negatives

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct=lambda p: ('%1.2f%%' % (p)) if p > 0 else '', startangle=90)
    plt.title(title)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


def line_trend_top_n(df_wide, top_n, years, title, outpath):
    """
    df_wide: rows=index (countries or industries), columns=years (int)
    top_n: pick top_n by the last year available among `years` to display and legend
    years: list of years to plot (subset of df_wide columns)
    """
    # determine last year available from the years list that is present in the df
    available_years = [y for y in years if y in df_wide.columns]
    if not available_years:
        raise ValueError("No requested trend years are present in the dataframe columns.")
    last_year = max(available_years)
    # clean numeric conversion
    df_f = df_wide.copy().astype(float).fillna(0.0)
    # top_n selection by last year
    if last_year in df_f.columns:
        top_countries = list(df_f[last_year].sort_values(ascending=False).head(top_n).index)
    else:
        top_countries = list(df_f.sum(axis=1).sort_values(ascending=False).head(top_n).index)

    plt.figure(figsize=(10, 6))
    for country in top_countries:
        row = df_f.loc[country]
        ys = [row[y] if y in row.index else 0.0 for y in available_years]
        plt.plot(available_years, ys, marker='o', label=country)

    plt.xlabel("Year")
    plt.ylabel("Labour share (fraction)")
    plt.title(title)
    plt.legend(title=f"Top {top_n}", loc="best", fontsize="small")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


# ---------- Generation ----------
def generate_all_industry_charts(input_xlsx, output_dir):
    xls = pd.ExcelFile(input_xlsx)
    # Load required sheets if present
    sheets_to_load = {
        "global_labour": SHEET_GLOBAL_LABOUR,
        "eu_labour": SHEET_EU_LABOUR
    }
    data = {}
    for key, sheet in sheets_to_load.items():
        if sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, index_col=0)
            df = safe_convert_year_cols(df)
            data[key] = df
            print(f"Loaded sheet '{sheet}' with shape {df.shape}")
        else:
            data[key] = None
            print(f"Warning: sheet '{sheet}' not found — skipping related charts.")

    # --- Global Labour industry pies & trends (top 12) ---
    if data["global_labour"] is not None:
        df_global_labour = data["global_labour"].copy()
        if 2023 not in df_global_labour.columns:
            raise ValueError("Global_Labour_Industry_Share must contain a '2023' column.")
        s2023 = df_global_labour[2023].astype(float)
        s2023 = normalize_shares_series(s2023)
        pie_top_n_with_others(s2023, top_n=12,
                              title="Global Industry Labour Share 2023 (Top 12)",
                              outpath=os.path.join(output_dir, "Global_Labour_Industry_Top12_2023_pie.png"))

        line_trend_top_n(df_global_labour, top_n=12, years=TREND_YEARS,
                         title="Global Industry Labour Share Trend 2010-2023 (Top 12)",
                         outpath=os.path.join(output_dir, "Global_Labour_Industry_Top12_trend_2010_2023.png"))
    else:
        print("Skipping Global Labour industry charts (sheet missing).")

    # --- EU Labour industry pies & trends (top 12) ---
    if data["eu_labour"] is not None:
        df_eu_labour = data["eu_labour"].copy()
        if 2023 not in df_eu_labour.columns:
            raise ValueError("EU_Labour_Industry_Share must contain a '2023' column.")
        s2023_eu = df_eu_labour[2023].astype(float)
        s2023_eu = normalize_shares_series(s2023_eu)
        pie_top_n_with_others(s2023_eu, top_n=12,
                              title="EU Industry Labour Share 2023 (Top 12)",
                              outpath=os.path.join(output_dir, "EU_Labour_Industry_Top12_2023_pie.png"))

        line_trend_top_n(df_eu_labour, top_n=12, years=TREND_YEARS,
                         title="EU Industry Labour Share Trend 2010-2023 (Top 12)",
                         outpath=os.path.join(output_dir, "EU_Labour_Industry_Top12_trend_2010_2023.png"))
    else:
        print("Skipping EU Labour industry charts (sheet missing).")

    print("All done. Charts written to:", os.path.abspath(output_dir))


# ---------- Run ----------
if __name__ == "__main__":
    generate_all_industry_charts(INPUT_XLSX, OUTPUT_DIR)
