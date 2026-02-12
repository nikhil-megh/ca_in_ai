import os
import pandas as pd
from pathlib import Path

# ======================== CONFIGURATION ========================
BASE_SENSITIVITY_DIR = "/Users/nikhil/Documents/Thesis/FCT/Sensitivity"

INDUSTRY_CODES = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]

EU27 = [
    "BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT",
    "CY", "LV", "LT", "LU", "HU", "MT", "NL", "AT", "PL", "PT", "RO", "SI",
    "SK", "FI", "SE"
]

YEARS = list(range(2010, 2022))


# ======================== HELPER FUNCTIONS ========================
def aggregate_eu27_columns(df: pd.DataFrame, eu_list=EU27, new_col="EU27"):
    """
    Sum the values across all EU27 columns, drop them, insert aggregated EU27 column.
    """
    eu_cols = [c for c in df.columns if c in eu_list]

    if not eu_cols:
        print(f"    ⚠️ Warning: No EU27 columns found in dataframe")
        return df

    df[new_col] = df[eu_cols].sum(axis=1)
    df = df.drop(columns=eu_cols)
    return df


def process_factor_endowments_eu_agg(industry_code):
    """
    Aggregates EU27 columns in factor endowments for a given omitted industry.
    """
    industry_dir = Path(BASE_SENSITIVITY_DIR) / industry_code
    input_dir = industry_dir / "Factor_Endowments"
    output_dir = industry_dir / "Factor_Endowments_EU_Agg"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Processing Factor Endowments EU aggregation for {industry_code}...")

    for year in YEARS:
        file_path = input_dir / f"factor_endowments_{year}.csv"

        if not file_path.exists():
            print(f"    ⚠️ Warning: {file_path} not found, skipping...")
            continue

        df = pd.read_csv(file_path, index_col=0)

        # Aggregate EU27 columns
        df_agg = aggregate_eu27_columns(df)

        # Save output
        out_path = output_dir / f"factor_endowments_{year}.csv"
        df_agg.to_csv(out_path)

    print(f"    ✅ Completed Factor Endowments EU aggregation for {industry_code}")


def process_measured_fct_eu_agg(industry_code):
    """
    Aggregates EU27 columns in measured FCT for a given omitted industry.
    """
    industry_dir = Path(BASE_SENSITIVITY_DIR) / industry_code
    input_dir = industry_dir / "Measured_FCT"
    output_dir = industry_dir / "Measured_FCT_EU_Agg"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Processing Measured FCT EU aggregation for {industry_code}...")

    for year in YEARS:
        file_path = input_dir / f"measured_fct_{year}.csv"

        if not file_path.exists():
            print(f"    ⚠️ Warning: {file_path} not found, skipping...")
            continue

        df = pd.read_csv(file_path, index_col=0)

        # Aggregate EU27 columns
        df_agg = aggregate_eu27_columns(df)

        # Save output
        out_path = output_dir / f"measured_fct_{year}.csv"
        df_agg.to_csv(out_path)

    print(f"    ✅ Completed Measured FCT EU aggregation for {industry_code}")


# ======================== MAIN EXECUTION ========================
if __name__ == "__main__":
    print("🚀 Starting EU27 aggregation for all industry sensitivity analyses...\n")

    for industry_code in INDUSTRY_CODES:
        print(f"\n{'=' * 60}")
        print(f"PROCESSING EU AGGREGATION FOR: {industry_code}")
        print(f"{'=' * 60}")

        # Process Factor Endowments
        try:
            process_factor_endowments_eu_agg(industry_code)
        except Exception as e:
            print(f"  ❌ Error processing Factor Endowments for {industry_code}: {e}")

        # Process Measured FCT
        try:
            process_measured_fct_eu_agg(industry_code)
        except Exception as e:
            print(f"  ❌ Error processing Measured FCT for {industry_code}: {e}")

        print(f"✅ COMPLETED EU AGGREGATION: {industry_code}\n")

    print("\n" + "=" * 60)
    print("🎉 EU27 AGGREGATION COMPLETE FOR ALL INDUSTRIES!")
    print("=" * 60)
