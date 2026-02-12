import pandas as pd


def transform_csv_to_excel(input_csv: str, output_excel: str):
    # Read CSV
    df = pd.read_csv(input_csv)
    df.columns = df.columns.str.strip()

    # --- Clean and normalize ---
    # Convert TIME_PERIOD to numeric year (ignore non-numeric)
    df["TIME_PERIOD"] = pd.to_numeric(df["TIME_PERIOD"], errors="coerce").astype("Int64")

    # Convert OBS_VALUE to numeric
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")

    # Drop rows with missing values in critical columns
    df = df.dropna(subset=["TIME_PERIOD", "OBS_VALUE", "REF_AREA", "Reference area", "ACTIVITY", "Economic activity"])

    # Create descriptive columns
    df["Country"] = df["REF_AREA"].astype(str) + ": " + df["Reference area"].astype(str)
    df["Industry Code"] = df["ACTIVITY"]
    df["Industry"] = df["Economic activity"]

    # Keep only relevant years (2010–2020)
    df = df[df["TIME_PERIOD"].between(2010, 2020)]

    # --- Pivot ---
    pivot_df = df.pivot_table(
        index=["Country", "Industry Code", "Industry"],
        columns="TIME_PERIOD",
        values="OBS_VALUE",
        aggfunc="mean"  # In case of duplicates, take average
    ).reset_index()

    # Convert TIME_PERIOD columns to strings
    pivot_df.columns = pivot_df.columns.map(lambda x: str(x) if isinstance(x, (int, float)) else x)

    # Ensure all years 2010–2020 exist
    for year in range(2010, 2021):
        year_str = str(year)
        if year_str not in pivot_df.columns:
            pivot_df[year_str] = None

    # Reorder columns
    fixed_columns = ["Country", "Industry Code", "Industry"] + [str(year) for year in range(2010, 2021)]
    pivot_df = pivot_df[fixed_columns]

    # --- Write to Excel ---
    pivot_df.to_excel(output_excel, index=False)
    print(f"✅ Transformation complete. Saved to '{output_excel}'")


if __name__ == "__main__":
    # Example usage
    input_csv = "/Users/nikhil/Downloads/Tim_2010-2020.csv"
    output_excel = "/Users/nikhil/Downloads/Tim_2010-2020_UPDATED.xlsx"
    transform_csv_to_excel(input_csv, output_excel)
