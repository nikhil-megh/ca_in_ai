import os
import pandas as pd
import numpy as np
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

TARGET = ["US", "CN", "EU27", "JP", "KR"]
YEARS = list(range(2010, 2022))


# ======================== HELPER FUNCTIONS ========================
def safe_divide(numerator, denominator):
    """Safely divide two arrays or scalars (element-wise); return 0 where denominator == 0."""
    if np.isscalar(numerator) and np.isscalar(denominator):
        if denominator == 0 or not np.isfinite(denominator) or not np.isfinite(numerator):
            return 0.0
        else:
            return numerator / denominator
    else:
        with np.errstate(divide='ignore', invalid='ignore'):
            result = np.true_divide(numerator, denominator)
            result = np.where(np.isfinite(result), result, 0)
        return result


def compute_rfa_for_industry(industry_code):
    """
    Computes relative factor abundance metrics for a given omitted industry.
    Saves results to rfa_sensitivity_national.xlsx in the industry directory.
    """
    industry_dir = Path(BASE_SENSITIVITY_DIR) / industry_code

    # Input directories (EU aggregated versions)
    production_factors_dir = industry_dir / "Factor_Endowments_EU_Agg"
    measured_fct_dir = industry_dir / "Measured_FCT_EU_Agg"

    # Output file
    output_excel_path = industry_dir / "rfa_sensitivity_national.xlsx"

    # Check if input directories exist
    if not production_factors_dir.exists():
        print(f"  ⚠️ Warning: {production_factors_dir} not found, skipping {industry_code}")
        return

    if not measured_fct_dir.exists():
        print(f"  ⚠️ Warning: {measured_fct_dir} not found, skipping {industry_code}")
        return

    print(f"  Processing RFA for {industry_code}...")

    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        # Process for each year from 2010 to 2021
        for year in YEARS:
            # Construct file paths
            prod_path = production_factors_dir / f"factor_endowments_{year}.csv"
            measured_fct_path = measured_fct_dir / f"measured_fct_{year}.csv"

            # Check if files exist
            if not prod_path.exists():
                print(f"    ⚠️ Warning: {prod_path} not found, skipping year {year}")
                continue

            if not measured_fct_path.exists():
                print(f"    ⚠️ Warning: {measured_fct_path} not found, skipping year {year}")
                continue

            # Read CSVs
            df_prod = pd.read_csv(prod_path, index_col=0)
            df_measured_fct = pd.read_csv(measured_fct_path, index_col=0)

            # === Restrict to the TARGET countries ===
            countries = [c for c in TARGET if c in df_prod.columns]

            if not countries:
                print(f"    ⚠️ Warning: No target countries found in year {year}")
                continue

            # Extract relevant rows
            ai_prod = df_prod.loc["pct_national_ai_patents", countries]
            non_ai_prod = df_prod.loc["pct_national_non_ai_patents", countries]

            ai_measured_fct = df_measured_fct.loc["pct_national_ai_patents", countries]
            non_ai_measured_fct = df_measured_fct.loc["pct_national_non_ai_patents", countries]

            # Compute ratios
            production_ratio = safe_divide(ai_prod.values, non_ai_prod.values)
            fct_ratio = safe_divide(ai_measured_fct.values, non_ai_measured_fct.values)
            consumption_ratio = safe_divide(
                ai_prod.values - ai_measured_fct.values,
                non_ai_prod.values - non_ai_measured_fct.values
            )

            # Compute Leamer_Production_By_Consumption
            Leamer_Production_By_Consumption = safe_divide(production_ratio, consumption_ratio)

            # Compute Relative Factor Abundance (Yes if Production > Consumption)
            relative_abundance = np.where(production_ratio > consumption_ratio, "Yes", "No")

            # Build output DataFrame (WITHOUT Positive_Debaere_Bilateral_FCT)
            df_out = pd.DataFrame({
                "Production_AI_By_Non_AI": production_ratio,
                "Measured_FCT_AI_By_Non_AI": fct_ratio,
                "Consumption_AI_By_Non_AI": consumption_ratio,
                "Leamer_AI_By_Non_AI": Leamer_Production_By_Consumption,
                "Leamer_Relative_AI_By_Non_AI_Factor_Abundance": relative_abundance
            }, index=countries)

            # Write each year as a separate sheet in the same Excel file
            df_out.to_excel(writer, sheet_name=str(year), index_label="Country")

        print(f"    ✅ Saved RFA results to {output_excel_path}")


# ======================== MAIN EXECUTION ========================
if __name__ == "__main__":
    print("🚀 Starting Relative Factor Abundance sensitivity analysis for all industries...\n")

    for industry_code in INDUSTRY_CODES:
        print(f"\n{'=' * 60}")
        print(f"PROCESSING RFA FOR OMITTED INDUSTRY: {industry_code}")
        print(f"{'=' * 60}")

        try:
            compute_rfa_for_industry(industry_code)
        except Exception as e:
            print(f"  ❌ Error processing {industry_code}: {e}")
            import traceback

            traceback.print_exc()

        print(f"✅ COMPLETED RFA: {industry_code}\n")

    print("\n" + "=" * 60)
    print("🎉 RFA SENSITIVITY ANALYSIS COMPLETE FOR ALL INDUSTRIES!")
    print("=" * 60)
