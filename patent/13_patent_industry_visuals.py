import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
INPUT_XLSX = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/Descriptives_Industry/PCT_Patents_Industry_Summary.xlsx"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/Descriptives_Industry/Visuals"

# Sheet constants
SHEET_GLOBAL_AI = "Global_AI_Industry_Share"
SHEET_GLOBAL_NON_AI = "Global_Non_AI_Industry_Share"
SHEET_EU_AI = "EU_AI_Industry_Share"
SHEET_EU_NON_AI = "EU_Non_AI_Industry_Share"
SHEET_C26 = "C26_Country_AI_Share"
SHEET_J59_60 = "J59_60_Country_AI_Share"
SHEET_Q86 = "Q86_Country_AI_Share"
SHEET_C28 = "C28_Country_AI_Share"
SHEET_C29 = "C29_Country_AI_Share"
# SHEET_G46 = "G46_Country_AI_Share"
# SHEET_C21 = "C21_Country_AI_Share"

# Year range for trends
TREND_START = 2010
TREND_END = 2021
TREND_YEARS = list(range(TREND_START, TREND_END + 1))

# Industry descriptions (used in titles/annotations)
INDUSTRY_DESCRIPTIONS = {
    "C26": "Computer, Electronics and Optical Products",
    "J59_60": "Motion Picture, Video, Television; Programming & Broadcasting Activities",
    "Q86": "Human Health Activities",
    "C28": "Manufacture of machinery and equipment",
    "C29": "Manufacture of motor vehicles"
    # "G46": "Wholesale Trade, except Motor Vehicles",
    # "C21": "Pharmaceutical Products"
}


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
def pie_top_n_with_others(series_2021, top_n, title, outpath):
    """
    series_2021: pd.Series (index=countries or industries), values in fractions 0-1 or percents 0-100
    top_n: number of top slices to show; rest collapsed into 'Others' which includes missing share up to 1.0
    """
    s = normalize_shares_series(series_2021).fillna(0.0)
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


# def line_trend_top_n(df_wide, top_n, years, title, outpath):
#     """
#     df_wide: rows=index (countries or industries), columns=years (int)
#     top_n: pick top_n by the last year available among `years` to display and legend
#     years: list of years to plot (subset of df_wide columns)
#     """
#     # determine last year available from the years list that is present in the df
#     available_years = [y for y in years if y in df_wide.columns]
#     if not available_years:
#         raise ValueError("No requested trend years are present in the dataframe columns.")
#     last_year = max(available_years)
#     # clean numeric conversion
#     df_f = df_wide.copy().astype(float).fillna(0.0)
#     # top_n selection by last year
#     if last_year in df_f.columns:
#         top_countries = list(df_f[last_year].sort_values(ascending=False).head(top_n).index)
#     else:
#         top_countries = list(df_f.sum(axis=1).sort_values(ascending=False).head(top_n).index)
#
#     plt.figure(figsize=(10, 6))
#     for country in top_countries:
#         row = df_f.loc[country]
#         ys = [row[y] if y in row.index else 0.0 for y in available_years]
#         plt.plot(available_years, ys, marker='o', label=country)
#
#     plt.xlabel("Year")
#     plt.ylabel("AI patent share (fraction)")
#     plt.title(title)
#     plt.legend(title=f"Top {top_n}", loc="best", fontsize="small")
#     plt.grid(True)
#     plt.tight_layout()
#     plt.savefig(outpath, dpi=300)
#     plt.close()


def line_trend_top_n(df_wide, top_n, years, title, outpath):
    """
    df_wide: rows=index (countries or industries), columns=years (int)
    top_n: pick top_n by the last year available among `years`
    years: list of years to plot (subset of df_wide columns)
    """

    # determine last year available from the years list that is present in the df
    available_years = [y for y in years if y in df_wide.columns]
    if not available_years:
        raise ValueError("No requested trend years are present in the dataframe columns.")

    last_year = max(available_years)

    # clean numeric conversion
    df_f = df_wide.copy().astype(float)

    # top_n selection by last year
    if last_year in df_f.columns:
        top_entities = (
            df_f[last_year]
            .fillna(0.0)
            .sort_values(ascending=False)
            .head(top_n)
            .index
            .tolist()
        )
    else:
        top_entities = (
            df_f.fillna(0.0)
            .sum(axis=1)
            .sort_values(ascending=False)
            .head(top_n)
            .index
            .tolist()
        )

    plt.figure(figsize=(10, 6))

    for entity in top_entities:
        if entity in df_f.index:
            row = df_f.loc[entity]
            ys = []
            for y in available_years:
                val = row[y] if (y in row and not pd.isna(row[y])) else 0.0
                ys.append(float(val) * 100)  # convert to percentage
            plt.plot(available_years, ys, label=entity)

    plt.xlabel("Year")
    plt.ylabel("Share of patent stock (%)")
    plt.title(title)
    plt.legend(title=f"Top {top_n}")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


# ---------- Generation ----------
def generate_all_industry_charts(input_xlsx, output_dir):
    xls = pd.ExcelFile(input_xlsx)
    # Load required sheets if present
    sheets_to_load = {
        "global_ai": SHEET_GLOBAL_AI,
        "global_nonai": SHEET_GLOBAL_NON_AI,
        "eu_ai": SHEET_EU_AI,
        "eu_nonai": SHEET_EU_NON_AI,
        "C26": SHEET_C26,
        "J59_60": SHEET_J59_60,
        "Q86": SHEET_Q86,
        "C28": SHEET_C28,
        "C29": SHEET_C29
        # "G46": SHEET_G46,
        # "C21": SHEET_C21
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

    # --- Global AI industry pies & trends (top 7) ---
    if data["global_ai"] is not None:
        df_global_ai = data["global_ai"].copy()
        if 2021 not in df_global_ai.columns:
            raise ValueError("Global_AI_Industry_Share must contain a '2021' column.")
        s2021 = df_global_ai[2021].astype(float)
        s2021 = normalize_shares_series(s2021)
        pie_top_n_with_others(s2021, top_n=7,
                              title="Global Industry AI Patent Stock Share 2021 (Top 7)",
                              outpath=os.path.join(output_dir, "Global_AI_Industry_Top7_2021_pie.png"))

        line_trend_top_n(df_global_ai, top_n=7, years=TREND_YEARS,
                         title="Global Industry AI Patent Stock Share Trend 2010-2021 (Top 7)",
                         outpath=os.path.join(output_dir, "Global_AI_Industry_Top7_trend_2010_2021.png"))
    else:
        print("Skipping Global AI industry charts (sheet missing).")

    # --- Global Non AI industry pies & trends (top 7) ---
    if data["global_nonai"] is not None:
        df_global_nonai = data["global_nonai"].copy()
        if 2021 not in df_global_nonai.columns:
            raise ValueError("Global_Non_AI_Industry_Share must contain a '2021' column.")
        s2021 = df_global_nonai[2021].astype(float)
        s2021 = normalize_shares_series(s2021)
        pie_top_n_with_others(s2021, top_n=7,
                              title="Global Industry Non AI Patent Stock Share 2021 (Top 7)",
                              outpath=os.path.join(output_dir, "Global_Non_AI_Industry_Top7_2021_pie.png"))

        line_trend_top_n(df_global_nonai, top_n=7, years=TREND_YEARS,
                         title="Global Industry Non AI Patent Stock Share Trend 2010-2021 (Top 7)",
                         outpath=os.path.join(output_dir, "Global_Non_AI_Industry_Top7_trend_2010_2021.png"))
    else:
        print("Skipping Global Non AI industry charts (sheet missing).")

    # --- EU AI industry pies & trends (top 7) ---
    if data["eu_ai"] is not None:
        df_eu_ai = data["eu_ai"].copy()
        if 2021 not in df_eu_ai.columns:
            raise ValueError("EU_AI_Industry_Share must contain a '2021' column.")
        s2021_eu = df_eu_ai[2021].astype(float)
        s2021_eu = normalize_shares_series(s2021_eu)
        pie_top_n_with_others(s2021_eu, top_n=7,
                              title="EU Industry AI Patent Stock Share 2021 (Top 7)",
                              outpath=os.path.join(output_dir, "EU_AI_Industry_Top7_2021_pie.png"))

        line_trend_top_n(df_eu_ai, top_n=7, years=TREND_YEARS,
                         title="EU Industry AI Patent Stock Share Trend 2010-2021 (Top 7)",
                         outpath=os.path.join(output_dir, "EU_AI_Industry_Top7_trend_2010_2021.png"))
    else:
        print("Skipping EU AI industry charts (sheet missing).")

    # --- EU Non AI industry pies & trends (top 7) ---
    if data["eu_nonai"] is not None:
        df_eu_nonai = data["eu_nonai"].copy()
        if 2021 not in df_eu_nonai.columns:
            raise ValueError("EU_Non_AI_Industry_Share must contain a '2021' column.")
        s2021_eu = df_eu_nonai[2021].astype(float)
        s2021_eu = normalize_shares_series(s2021_eu)
        pie_top_n_with_others(s2021_eu, top_n=7,
                              title="EU Industry Non AI Patent Stock Share 2021 (Top 7)",
                              outpath=os.path.join(output_dir, "EU_Non_AI_Industry_Top7_2021_pie.png"))

        line_trend_top_n(df_eu_nonai, top_n=7, years=TREND_YEARS,
                         title="EU Industry Non AI Patent Stock Share Trend 2010-2021 (Top 7)",
                         outpath=os.path.join(output_dir, "EU_Non_AI_Industry_Top7_trend_2010_2021.png"))
    else:
        print("Skipping EU Non AI industry charts (sheet missing).")

    # --- For each of the 4 industry-country sheets: pie (top7) + trend (top7) ---
    for code in ["C26", "J59_60", "Q86", "C28", "C29"]:
        df_sheet = data.get(code)
        sheet_name = sheets_to_load.get(code)
        desc = INDUSTRY_DESCRIPTIONS.get(code, "")
        if df_sheet is None:
            print(f"Skipping {code} charts (sheet '{sheet_name}' missing).")
            continue

        if 2021 not in df_sheet.columns:
            raise ValueError(f"Sheet {sheet_name} must contain a '2021' column.")

        # 2021 pie
        s2021 = df_sheet[2021].astype(float)
        s2021 = normalize_shares_series(s2021)
        title_pie = f"{code} - {desc}\nTop 5 Countries (2021) + Others"
        out_pie = os.path.join(output_dir, f"{code}_Top5_2021_pie.png")
        pie_top_n_with_others(s2021, top_n=5, title=title_pie, outpath=out_pie)

        # trend for top 7 (2010-2021)
        title_trend = f"{code} - {desc}\nAI Patent Share Trend (Top 5 Countries) 2010-2021"
        out_trend = os.path.join(output_dir, f"{code}_Top5_trend_2010_2021.png")
        line_trend_top_n(df_sheet, top_n=5, years=TREND_YEARS, title=title_trend, outpath=out_trend)

        print(f"Generated charts for {code}: pie -> {out_pie}, trend -> {out_trend}")

    print("All done. Charts written to:", os.path.abspath(output_dir))


# ---------- Run ----------
if __name__ == "__main__":
    generate_all_industry_charts(INPUT_XLSX, OUTPUT_DIR)
