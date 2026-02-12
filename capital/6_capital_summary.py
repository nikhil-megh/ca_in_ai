import argparse
from pathlib import Path
import pandas as pd

EU27 = {"BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR",
        "HR", "IT", "CY", "LV", "LT", "LU", "HU", "MT", "NL", "AT",
        "PL", "PT", "RO", "SI", "SK", "FI", "SE"}
YEARS = [str(y) for y in range(2010, 2022)]
INPUT_PATH = "/Users/nikhil/Documents/Thesis/Capital/CAPITAL_v2_figaro2025.xlsx"
COUNTRY_OUTPUT_PATH = "/Users/nikhil/Documents/Thesis/Capital/Capital_Country_Summary.xlsx"
INDUSTRY_OUTPUT_PATH = "/Users/nikhil/Documents/Thesis/Capital/Capital_Industry_Summary.xlsx"


def read_input(path: Path) -> pd.DataFrame:
    # Read first sheet by default
    df = pd.read_excel(path, sheet_name="Final", engine="openpyxl")
    # Ensure factor_key column present and properly named
    if df.columns[0] != "factor_key":
        df = df.rename(columns={df.columns[0]: "factor_key"})
    # Keep only expected year columns plus factor_key (in case sheet has extras)
    df.columns = df.columns.map(str)
    print(df.columns)
    cols = ["factor_key"] + [c for c in YEARS if c in df.columns]
    print(cols)
    df = df[cols].copy()
    # Ensure numeric years
    for y in YEARS:
        if y in df.columns:
            df[y] = pd.to_numeric(df[y], errors="coerce").fillna(0.0)
    return df


def split_factor_key(df: pd.DataFrame) -> pd.DataFrame:
    # Split factor_key at the first underscore only
    def split_once(s: str):
        parts = str(s).split("_", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            raise FileNotFoundError(f"Error splitting: {s}")
    codes = df["factor_key"].apply(split_once)
    df[["country_code", "industry_code"]] = pd.DataFrame(codes.tolist(), index=df.index)
    return df


def make_country_summaries(df: pd.DataFrame):
    # Sum across industries for each country and year
    country_sum = df.groupby("country_code")[YEARS].sum()
    # Global totals per year (all countries)
    global_total = country_sum.sum(axis=0)

    # Global labour share: include EU27 aggregated row, but remove individual EU27 rows
    eu_agg = country_sum.loc[list(EU27 & set(country_sum.index))].sum(axis=0)
    # Build Global DataFrame: non-EU countries + EU27 aggregate row
    non_eu = country_sum.drop(index=[c for c in country_sum.index if c in EU27], errors="ignore")
    global_df = pd.concat([non_eu, pd.DataFrame([eu_agg], index=["EU27"])])
    # Shares: divide by global_total (broadcasting along columns)
    global_share = global_df.divide(global_total, axis=1).fillna(0.0)
    # Order rows by 2021 descending
    global_share = global_share.sort_values(by="2021", ascending=False)

    # EU Labour Share: only EU27 countries, share within EU total
    # Keep only EU countries that actually appear in data
    eu_countries_present = sorted([c for c in country_sum.index if c in EU27])
    eu_country_sum = country_sum.loc[eu_countries_present].copy()
    eu_total = eu_country_sum.sum(axis=0)
    eu_share = eu_country_sum.divide(eu_total, axis=1).fillna(0.0)
    eu_share = eu_share.sort_values(by="2021", ascending=False)

    # Return DataFrames with country_code as index and YEARS columns
    return global_share[YEARS].rename_axis("country_code"), eu_share[YEARS].rename_axis("country_code")


def make_industry_summaries(df: pd.DataFrame):
    # Sum across countries for each industry and year
    industry_sum = df.groupby("industry_code")[YEARS].sum()
    # Global totals per year (all industries)
    global_total = industry_sum.sum(axis=0)

    # Global industry share (industry / global_total)
    global_ind_share = industry_sum.divide(global_total, axis=1).fillna(0.0)
    global_ind_share = global_ind_share.sort_values(by="2021", ascending=False)

    # EU industry share: sum only over EU countries
    eu_df = df[df["country_code"].isin(EU27)].copy()
    industry_sum_eu = eu_df.groupby("industry_code")[YEARS].sum()
    eu_total = industry_sum_eu.sum(axis=0)
    eu_ind_share = industry_sum_eu.divide(eu_total, axis=1).fillna(0.0)
    eu_ind_share = eu_ind_share.sort_values(by="2021", ascending=False)

    return global_ind_share[YEARS].rename_axis("industry_code"), eu_ind_share[YEARS].rename_axis("industry_code")


def write_excel_country(global_share: pd.DataFrame, eu_share: pd.DataFrame, out_path: Path):
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        # Write Global_Labour_Share
        global_share.to_excel(writer, sheet_name="Global_Capital_Share")
        # Write EU_Labour_Share
        eu_share.to_excel(writer, sheet_name="EU_Capital_Share")


def write_excel_industry(global_ind_share: pd.DataFrame, eu_ind_share: pd.DataFrame, out_path: Path):
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        global_ind_share.to_excel(writer, sheet_name="Global_Capital_Industry_Share")
        eu_ind_share.to_excel(writer, sheet_name="EU_Capital_Industry_Share")


def main(input_file: str, country_out: str, industry_out: str):
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = read_input(path)
    df = split_factor_key(df)

    # Country summaries
    global_share, eu_share = make_country_summaries(df)
    write_excel_country(global_share, eu_share, Path(country_out))

    # Industry summaries
    global_ind_share, eu_ind_share = make_industry_summaries(df)
    write_excel_industry(global_ind_share, eu_ind_share, Path(industry_out))

    print(f"Wrote country summaries to: {country_out}")
    print(f"Wrote industry summaries to: {industry_out}")


if __name__ == "__main__":
    main(INPUT_PATH, COUNTRY_OUTPUT_PATH, INDUSTRY_OUTPUT_PATH)
