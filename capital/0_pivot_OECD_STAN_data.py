import pandas as pd
import os

# -------- CONFIGURATION --------
INPUT_PATH = "/Users/nikhil/Downloads/OECD_STAN/OECD_NetCapitalStock_CurrentPrices.csv"
OUTPUT_PATH = "/Users/nikhil/Downloads/OECD_STAN/OECD_Industry_NetCapitalStock_CurrentPrices_DomesticCurrency_Millions.xlsx"

START_YEAR = 2010
END_YEAR = 2023


def create_pivot_excel(input_path: str, output_path: str):
    # Read data
    df = pd.read_csv(input_path, dtype={"REF_AREA": str, "ACTIVITY": str, "TIME_PERIOD": int, "OBS_VALUE": float})

    # Filter only years within 2010–2023
    df = df[(df["TIME_PERIOD"] >= START_YEAR) & (df["TIME_PERIOD"] <= END_YEAR)]

    # Create Excel writer
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for area, group in df.groupby("REF_AREA"):
            pivot = group.pivot_table(
                index="ACTIVITY",
                columns="TIME_PERIOD",
                values="OBS_VALUE",
                aggfunc="first"  # assuming one value per activity-year; use "sum" if multiple
            )

            # Sort columns (years) in ascending order
            pivot = pivot.reindex(sorted(pivot.columns), axis=1)

            # Write each pivot to its own sheet
            pivot.to_excel(writer, sheet_name=area)

    print(f"✅ Done. Pivot tables written to: {output_path}")


if __name__ == "__main__":
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Error: Input file not found at {INPUT_PATH}")
    else:
        create_pivot_excel(INPUT_PATH, OUTPUT_PATH)
