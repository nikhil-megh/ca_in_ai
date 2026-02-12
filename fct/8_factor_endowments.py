import os
import pandas as pd

FACTORS_DIR = "/Users/nikhil/Documents/Thesis/FCT/Matrices/Factor_Vectors"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/Factor_Endowments"

YEARS = list(range(2010, 2022))

# Given valid country ordering list (46)
COUNTRIES = [
    "AR","AT","AU","BE","BG","BR","CA","CH","CN","CY","CZ","DE","DK","EE",
    "ES","FI","FIGW1","FR","GB","GR","HR","HU","ID","IE","IN","IT","JP","KR",
    "LT","LU","LV","MT","MX","NL","NO","PL","PT","RO","RU","SA","SE","SI",
    "SK","TR","US","ZA"
]


def aggregate_country_factors(year):
    print(f"Processing factor endowments for {year}...")

    # Load factor matrix (6 x 2944)
    E = pd.read_csv(os.path.join(FACTORS_DIR, f"factors_{year}.csv"),
                    index_col=0)

    # Extract country code from each sector column
    country_map = E.columns.str.split("_").str[0]

    # Group by country prefix & sum
    E_country = E.groupby(country_map, axis=1).sum()

    # Reorder columns to desired fixed ordering
    E_country = E_country[COUNTRIES]

    # Save output
    outfile = os.path.join(OUTPUT_DIR,
                           f"factor_endowments_{year}.csv")
    E_country.to_csv(outfile)

    print(f"✅ Saved: {outfile}")


if __name__ == "__main__":
    for yr in YEARS:
        aggregate_country_factors(yr)

    print("\n🎉 All country-level factor endowments created!")
