import os
import pandas as pd
from pathlib import Path

# ---- USER INPUT ----
NET_TRADE_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Net_Trade_Vectors"
GDP_FILE = "/Users/nikhil/Documents/Thesis/Figaro/FIGARO_ValueAdded_2010_2021.xlsx"
OUTPUT_FILE = "/Users/nikhil/Documents/Thesis/FCT/Consumption_Shares/consumption_shares_2010_2021.xlsx"

YEARS = range(2010, 2022)
FINAL_COUNTRY_ORDER = [
    "AR","AT","AU","BE","BG","BR","CA","CH","CN","CY","CZ","DE","DK","EE",
    "ES","FI","FIGW1","FR","GB","GR","HR","HU","ID","IE","IN","IT","JP","KR",
    "LT","LU","LV","MT","MX","NL","NO","PL","PT","RO","RU","SA","SE","SI",
    "SK","TR","US","ZA"
]


def extract_country_code(idx):
    """Extracts the country code from an index like AR_A01 → AR"""
    return idx.split("_")[0]


if __name__ == "__main__":
    # ---- Load GDP ----
    gdp_df = pd.read_excel(GDP_FILE, index_col=0)
    year_cols = [col for col in gdp_df.columns if isinstance(col, int) or str(col).isdigit()]
    gdp_df.rename(columns={col: str(col) for col in year_cols}, inplace=True)
    gdp_df['country'] = gdp_df.index.map(extract_country_code)
    GDP_country = gdp_df.groupby('country')[list(map(str, YEARS))].sum()

    # ---- Load TB (Trade Balance) ----
    TB_country = pd.DataFrame(index=FINAL_COUNTRY_ORDER, columns=list(map(str, YEARS)))

    for year in YEARS:
        fn = Path(NET_TRADE_DIR) / f"net_trade_vector_{year}.csv"
        T = pd.read_csv(fn, index_col=0)

        tb_vec = T.sum(axis=0)  # sum across industries → 46 countries
        TB_country[str(year)] = tb_vec

    # ---- Reindex GDP to match final order ----
    GDP_country = GDP_country.reindex(FINAL_COUNTRY_ORDER)

    # ---- Compute global totals ----
    GDP_world = GDP_country.sum()
    TB_world = TB_country.sum()

    # ---- Compute consumption share ----
    consumption_shares = (GDP_country - TB_country) \
        .div((GDP_world - TB_world), axis=1)

    # Formatting
    consumption_shares.index.name = "country"
    consumption_shares.columns = [str(y) for y in YEARS]

    # ---- Save ----
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    consumption_shares.to_excel(OUTPUT_FILE)

    print("✅ Consumption shares saved successfully!")
    print("📄 File:", OUTPUT_FILE)
