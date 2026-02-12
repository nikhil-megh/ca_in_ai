import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
INPUT_XLSX = "/Users/nikhil/Documents/Thesis/Labour/Descriptives_Country/Labour_Country_Summary.xlsx"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/Labour/Descriptives_Country/Visuals"

# Sheet names (adjust if your workbook uses different names)
SHEET_GLOBAL_LABOUR_SHARE = "Global_Labour_Share"
SHEET_EU_LABOUR_SHARE = "EU_Labour_Share"

# Year range used for trends
TREND_START = 2010
TREND_END = 2021
YEARS = list(range(TREND_START, TREND_END + 1))


# ---------- Helpers ----------
def safe_convert_year_cols(df):
    new_cols = []
    for c in df.columns:
        try:
            # ignore non-string/float conversions raising exceptions
            if isinstance(c, (int, np.integer)):
                new_cols.append(int(c))
            else:
                # try numeric cast then int
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
    Ensure series sums are in fraction form (0-1). If values look like percentages (sum > 1),
    divide by 100.
    """
    s = s.astype(float)
    total = s.sum()
    if total > 1.0001:  # likely percentages (0-100)
        s = s / 100.0
    return s


def add_rest_of_world_to_others(total_rows_sum, sum_of_remaining_rows):
    """
    Calculate the 'rest of world' share that is not included in the rows.
    total_rows_sum = sum of all rows present in sheet for 2021 (e.g. df[2021].sum())
    The missing share = 1 - total_rows_sum (if positive), otherwise 0.
    Others in pie = sum_of_remaining_rows + missing_share
    """
    missing = max(0.0, 1.0 - total_rows_sum)
    return sum_of_remaining_rows + missing


# ---------- Plotting functions ----------
def pie_top_n_with_others(series_2021, top_n, title, outpath):
    """
    series_2021: pd.Series indexed by country, values are shares (fractions 0-1)
    top_n: number of top slices to show
    """
    s = normalize_shares_series(series_2021)
    total_rows_sum = s.sum()  # sum of rows present in sheet
    s_sorted = s.sort_values(ascending=False)
    top = s_sorted.iloc[:top_n]
    remaining = s_sorted.iloc[top_n:]
    others_value = add_rest_of_world_to_others(total_rows_sum, remaining.sum())
    labels = list(top.index) + ["Others"]
    sizes = list(top.values) + [others_value]

    # Avoid tiny negative rounding errors
    sizes = [max(0.0, float(x)) for x in sizes]

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct=lambda p: ('%1.2f%%' % (p)) if p > 0 else '', startangle=90)
    plt.title(title)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


def line_trend_for_countries(df_wide, country_list, years, title, outpath):
    """
    df_wide: DataFrame indexed by country, columns are integer years
    country_list: list of countries to plot (order preserved)
    years: list of years to plot
    """
    plt.figure(figsize=(10, 6))
    for country in country_list:
        if country in df_wide.index:
            row = df_wide.loc[country]
            # Ensure convert and handle possible missing values
            ys = []
            for y in years:
                ys.append(float(row[y]) if (y in row and not pd.isna(row[y])) else 0.0)
            plt.plot(years, ys, label=country)
    plt.xlabel("Year")
    plt.ylabel("Labour share (fraction)")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


# ---------- Main generation ----------
def generate_all_charts(input_xlsx, output_dir):
    # Read sheets into dataframes
    xls = pd.ExcelFile(input_xlsx)
    # Read with index_col=0 to preserve rows as countries
    sheets = {}
    for name in [SHEET_GLOBAL_LABOUR_SHARE, SHEET_EU_LABOUR_SHARE]:
        if name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=name, index_col=0)
            df = safe_convert_year_cols(df)
            sheets[name] = df
        else:
            print(f"Warning: sheet '{name}' not found in the workbook. Skipping.")
            sheets[name] = None

    # --- Global Labour Share: pie (top9) + line trend for top9 ---
    df_global_labour_share = sheets[SHEET_GLOBAL_LABOUR_SHARE]
    if df_global_labour_share is not None:
        # ensure columns as ints, pick 2021 column
        if 2021 not in df_global_labour_share.columns:
            raise ValueError("Global_Labour_Share sheet must contain a 2021 column")
        s2021 = df_global_labour_share[2021].astype(float)
        # normalize (detect percentage form inside helper)
        s2021 = normalize_shares_series(s2021)

        # top 5 pie chart: Others includes rows not shown + rest of world missing share
        pie_top_n_with_others(s2021, top_n=9,
                              title="Global Labour Share 2021 (Top 9)",
                              outpath=os.path.join(output_dir, "Global_Labour_Top9_2021_pie.png"))

        # top 5 countries list for line trend
        top9 = list(s2021.sort_values(ascending=False).index[:9])
        # create wide df for trend (rows = countries, columns = years)
        df_global_labour_wide = df_global_labour_share.copy().astype(float)
        # If sheet columns go back to 2000, we pick 2010-2021
        years_present = [y for y in YEARS if y in df_global_labour_wide.columns]
        line_trend_for_countries(df_global_labour_wide, top9, years_present,
                                 title="Global Labour Share Trend 2010-2021 (Top 9)",
                                 outpath=os.path.join(output_dir, "Global_Labour_Top9_trend_2010_2021.png"))
    else:
        print("Skipping Global_Labour_Share plots because sheet not found.")

    # --- EU Labour Share: pie (top9) + line trend for top9 ---
    df_eu_labour_share = sheets[SHEET_EU_LABOUR_SHARE]
    if df_eu_labour_share is not None:
        if 2021 not in df_eu_labour_share.columns:
            raise ValueError("EU_Labour_Share sheet must contain a 2021 column")
        s2021_eu = df_eu_labour_share[2021].astype(float)
        s2021_eu = normalize_shares_series(s2021_eu)

        pie_top_n_with_others(s2021_eu, top_n=9,
                              title="EU Labour Share 2021 (Top 9)",
                              outpath=os.path.join(output_dir, "EU_Labour_Top9_2021_pie.png"))

        top9 = list(s2021_eu.sort_values(ascending=False).index[:9])
        df_eu_labour_wide = df_eu_labour_share.copy().astype(float)
        years_present = [y for y in YEARS if y in df_eu_labour_wide.columns]
        line_trend_for_countries(df_eu_labour_wide, top9, years_present,
                                 title="EU Labour Share Trend 2010-2021 (Top 9)",
                                 outpath=os.path.join(output_dir, "EU_Labour_Top9_trend_2010_2021.png"))
    else:
        print("Skipping EU_Labour_Share plots because sheet not found.")

    print("Done. Charts written to:", os.path.abspath(output_dir))


# ---------- Run ----------
if __name__ == "__main__":
    generate_all_charts(INPUT_XLSX, OUTPUT_DIR)
