import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
INPUT_XLSX = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/Descriptives_Country/PCT_Patents_Country_Summary.xlsx"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/Descriptives_Country/Visuals"

# Sheet names (adjust if your workbook uses different names)
SHEET_GLOBAL_AI_SHARE = "Global_AI_Share"
SHEET_GLOBAL_NON_AI_SHARE = "Global_Non_AI_Share"
SHEET_EU_AI_SHARE = "EU_AI_Share"
SHEET_EU_NON_AI_SHARE = "EU_Non_AI_Share"
SHEET_GLOBAL_INTENSITY = "Global_AI_Intensity"
SHEET_EU_INTENSITY = "EU_AI_Intensity"

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
            ys = []
            for y in years:
                val = row[y] if (y in row and not pd.isna(row[y])) else 0.0
                ys.append(float(val) * 100)  # convert to percentage
            plt.plot(years, ys, label=country)

    plt.xlabel("Year")
    plt.ylabel("Share of patent stock (%)")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


def bar_all_countries_ordered(series_2021, title, outpath):
    """
    series_2021: pd.Series indexed by country in the order you want (already sorted)
    """
    s = normalize_shares_series(series_2021)
    plt.figure(figsize=(12, 6))
    # keep the order of the index as supplied (do not sort)
    x = list(range(len(s)))
    plt.bar(x, s.values)
    plt.xticks(x, s.index, rotation=90)
    plt.xlabel("Country")
    plt.ylabel("AI intensity (fraction)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


def line_trend_all_countries(df_wide, years, title, outpath):
    plt.figure(figsize=(12, 8))
    for country in df_wide.index:
        row = df_wide.loc[country]
        ys = [float(row[y]) if (y in row and not pd.isna(row[y])) else 0.0 for y in years]
        plt.plot(years, ys, label=country)
    plt.xlabel("Year")
    plt.ylabel("AI intensity (fraction)")
    plt.title(title)
    plt.legend(loc="upper left", fontsize="small", ncol=2)
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
    for name in [SHEET_GLOBAL_AI_SHARE, SHEET_GLOBAL_NON_AI_SHARE,
                 SHEET_EU_AI_SHARE, SHEET_EU_NON_AI_SHARE,
                 SHEET_GLOBAL_INTENSITY, SHEET_EU_INTENSITY]:
        if name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=name, index_col=0)
            df = safe_convert_year_cols(df)
            sheets[name] = df
        else:
            print(f"Warning: sheet '{name}' not found in the workbook. Skipping.")
            sheets[name] = None

    # --- Global AI Share: pie (top5) + line trend for top5 ---
    df_global_ai_share = sheets[SHEET_GLOBAL_AI_SHARE]
    if df_global_ai_share is not None:
        # ensure columns as ints, pick 2021 column
        if 2021 not in df_global_ai_share.columns:
            raise ValueError("Global_AI_Share sheet must contain a 2021 column")
        s2021 = df_global_ai_share[2021].astype(float)
        # normalize (detect percentage form inside helper)
        s2021 = normalize_shares_series(s2021)

        # top 5 pie chart: Others includes rows not shown + rest of world missing share
        pie_top_n_with_others(s2021, top_n=5,
                              title="Global AI Patent Stock Share 2021 (Top 5)",
                              outpath=os.path.join(output_dir, "Global_AI_Top5_2021_pie.png"))

        # top 5 countries list for line trend
        top5 = list(s2021.sort_values(ascending=False).index[:5])
        # create wide df for trend (rows = countries, columns = years)
        df_global_ai_wide = df_global_ai_share.copy().astype(float)
        # If sheet columns go back to 2000, we pick 2010-2021
        years_present = [y for y in YEARS if y in df_global_ai_wide.columns]
        line_trend_for_countries(df_global_ai_wide, top5, years_present,
                                 title="Global AI Patent Stock Share Trend 2010-2021 (Top 5)",
                                 outpath=os.path.join(output_dir, "Global_AI_Top5_trend_2010_2021.png"))
    else:
        print("Skipping Global_AI_Share plots because sheet not found.")

    # --- Global Non AI Share: pie (top5) + line trend for top5 ---
    df_global_nonai_share = sheets[SHEET_GLOBAL_NON_AI_SHARE]
    if df_global_nonai_share is not None:
        # ensure columns as ints, pick 2021 column
        if 2021 not in df_global_nonai_share.columns:
            raise ValueError("Global_Non_AI_Share sheet must contain a 2021 column")
        s2021 = df_global_nonai_share[2021].astype(float)
        # normalize (detect percentage form inside helper)
        s2021 = normalize_shares_series(s2021)

        # top 5 pie chart: Others includes rows not shown + rest of world missing share
        pie_top_n_with_others(s2021, top_n=5,
                              title="Global Non AI Patent Stock Share 2021 (Top 5)",
                              outpath=os.path.join(output_dir, "Global_Non_AI_Top5_2021_pie.png"))

        # top 5 countries list for line trend
        top5 = list(s2021.sort_values(ascending=False).index[:5])
        # create wide df for trend (rows = countries, columns = years)
        df_global_nonai_wide = df_global_nonai_share.copy().astype(float)
        # If sheet columns go back to 2000, we pick 2010-2021
        years_present = [y for y in YEARS if y in df_global_nonai_wide.columns]
        line_trend_for_countries(df_global_nonai_wide, top5, years_present,
                                 title="Global Non AI Patent Stock Share Trend 2010-2021 (Top 5)",
                                 outpath=os.path.join(output_dir, "Global_Non_AI_Top5_trend_2010_2021.png"))
    else:
        print("Skipping Global_Non_AI_Share plots because sheet not found.")

    # --- EU AI Share: pie (top6) + line trend for top6 ---
    df_eu_ai_share = sheets[SHEET_EU_AI_SHARE]
    if df_eu_ai_share is not None:
        if 2021 not in df_eu_ai_share.columns:
            raise ValueError("EU_AI_Share sheet must contain a 2021 column")
        s2021_eu = df_eu_ai_share[2021].astype(float)
        s2021_eu = normalize_shares_series(s2021_eu)

        pie_top_n_with_others(s2021_eu, top_n=6,
                              title="EU AI Patent Stock Share 2021 (Top 6)",
                              outpath=os.path.join(output_dir, "EU_AI_Top6_2021_pie.png"))

        top6 = list(s2021_eu.sort_values(ascending=False).index[:6])
        df_eu_ai_wide = df_eu_ai_share.copy().astype(float)
        years_present = [y for y in YEARS if y in df_eu_ai_wide.columns]
        line_trend_for_countries(df_eu_ai_wide, top6, years_present,
                                 title="EU AI Patent Stock Share Trend 2010-2021 (Top 6)",
                                 outpath=os.path.join(output_dir, "EU_AI_Top6_trend_2010_2021.png"))
    else:
        print("Skipping EU_AI_Share plots because sheet not found.")

    # --- EU Non AI Share: pie (top6) + line trend for top6 ---
    df_eu_non_ai_share = sheets[SHEET_EU_NON_AI_SHARE]
    if df_eu_non_ai_share is not None:
        if 2021 not in df_eu_non_ai_share.columns:
            raise ValueError("EU_AI_Share sheet must contain a 2021 column")
        s2021_eu = df_eu_non_ai_share[2021].astype(float)
        s2021_eu = normalize_shares_series(s2021_eu)

        pie_top_n_with_others(s2021_eu, top_n=6,
                              title="EU Non AI Patent Stock Share 2021 (Top 6)",
                              outpath=os.path.join(output_dir, "EU_Non_AI_Top6_2021_pie.png"))

        top6 = list(s2021_eu.sort_values(ascending=False).index[:6])
        df_eu_nonai_wide = df_eu_non_ai_share.copy().astype(float)
        years_present = [y for y in YEARS if y in df_eu_nonai_wide.columns]
        line_trend_for_countries(df_eu_nonai_wide, top6, years_present,
                                 title="EU Non AI Patent Stock Share Trend 2010-2021 (Top 6)",
                                 outpath=os.path.join(output_dir, "EU_Non_AI_Top6_trend_2010_2021.png"))
    else:
        print("Skipping EU_Non_AI_Share plots because sheet not found.")

    # --- Global AI Intensity: bar (2021 all countries in same order as rows), line trends all countries 2010-2021 ---
    df_global_int = sheets[SHEET_GLOBAL_INTENSITY]
    if df_global_int is not None:
        if 2021 not in df_global_int.columns:
            raise ValueError("Global_AI_Intensity sheet must contain a 2021 column")
        s2021_int = df_global_int[2021].astype(float)
        s2021_int = normalize_shares_series(s2021_int)

        # Use the row order as-is (assumed already decreasing). Reindex to keep order.
        bar_all_countries_ordered(s2021_int, title="Global AI Intensity by Country (2021)",
                                  outpath=os.path.join(output_dir, "Global_AI_Intensity_2021_bar.png"))

        # Trend lines for all countries 2010-2021
        df_global_int_wide = df_global_int.copy().astype(float)
        years_present = [y for y in YEARS if y in df_global_int_wide.columns]
        line_trend_all_countries(df_global_int_wide, years_present,
                                 title="Global AI Intensity Trend (All Countries) 2010-2021",
                                 outpath=os.path.join(output_dir, "Global_AI_Intensity_trends_2010_2021.png"))
    else:
        print("Skipping Global_AI_Intensity plots because sheet not found.")

    # --- EU AI Intensity: bar + trends (assumed sheet name EU_AI_Intensity) ---
    df_eu_int = sheets[SHEET_EU_INTENSITY]
    if df_eu_int is not None:
        if 2021 not in df_eu_int.columns:
            raise ValueError("EU_AI_Intensity sheet must contain a 2021 column")
        s2021_eu_int = df_eu_int[2021].astype(float)
        s2021_eu_int = normalize_shares_series(s2021_eu_int)

        bar_all_countries_ordered(s2021_eu_int, title="EU AI Intensity by Country (2021)",
                                  outpath=os.path.join(output_dir, "EU_AI_Intensity_2021_bar.png"))

        df_eu_int_wide = df_eu_int.copy().astype(float)
        years_present = [y for y in YEARS if y in df_eu_int_wide.columns]
        line_trend_all_countries(df_eu_int_wide, years_present,
                                 title="EU AI Intensity Trend (All EU Countries) 2010-2021",
                                 outpath=os.path.join(output_dir, "EU_AI_Intensity_trends_2010_2021.png"))
    else:
        print("Skipping EU_AI_Intensity plots because sheet not found.")

    print("Done. Charts written to:", os.path.abspath(output_dir))


# ---------- Run ----------
if __name__ == "__main__":
    generate_all_charts(INPUT_XLSX, OUTPUT_DIR)
