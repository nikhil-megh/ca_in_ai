import pandas as pd

# Static path to the PWT Excel file
INPUT_PATH = "/Users/nikhil/Documents/Thesis/Capital/PWT/pwt110.xlsx"
OUTPUT_PATH = "/Users/nikhil/Documents/Thesis/Capital/PWT/pwt110_current_prices.xlsx"


def pivot_capital_stock(input_path: str, output_path: str):
    # Read Excel file
    df = pd.read_excel(input_path, sheet_name="Data", dtype={"countrycode": str, "year": int, "cn": float})

    # Filter years 2010 to 2023
    df_filtered = df[(df['year'] >= 2010) & (df['year'] <= 2023)]

    # Create a new column for cn * pl_n
    df_filtered['cn_pln'] = df_filtered['cn'] * df_filtered['pl_n']

    # Pivot the data: countrycode as index, years as columns, values from cn
    pivot_df = df_filtered.pivot(index='countrycode', columns='year', values='cn_pln')

    # Save to Excel
    pivot_df.to_excel(output_path)

    print(f"Pivot table saved successfully: {output_path}")


def main():
    pivot_capital_stock(INPUT_PATH, OUTPUT_PATH)


if __name__ == "__main__":
    main()
