import os
import pandas as pd

# === Directories ===
pct_all_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_All"
pct_national_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_National"
output_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results"

DEP_RATES = [0, 5, 10, 12, 15, 17, 20, 25, 30]
YEAR = 2021


def format_rfa(leamer_value, abundance):
    """Format RFA as 'X.XXX (Yes/No)'"""
    return f"{leamer_value:.3f} ({abundance})"


if __name__ == "__main__":

    results = []

    # Process both application types
    application_types = [
        ("All PCT Applications (including ones in international phase)", pct_all_dir),
        ("PCT Applications entering National Phase", pct_national_dir)
    ]

    for app_type, input_dir in application_types:

        print(f"\n▶ Processing: {app_type}")

        for dep in DEP_RATES:
            # Read the excel file for this depreciation rate
            excel_path = os.path.join(input_dir, f"rfa_robustness_{dep}.xlsx")

            try:
                # Read the 2021 sheet
                df = pd.read_excel(excel_path, sheet_name=str(YEAR), index_col=0)

                # Extract data for CN, US, EU27
                cn_leamer = df.loc["CN", "Leamer_AI_By_Non_AI"]
                cn_abundance = df.loc["CN", "Leamer_Relative_AI_By_Non_AI_Factor_Abundance"]

                us_leamer = df.loc["US", "Leamer_AI_By_Non_AI"]
                us_abundance = df.loc["US", "Leamer_Relative_AI_By_Non_AI_Factor_Abundance"]

                eu_leamer = df.loc["EU27", "Leamer_AI_By_Non_AI"]
                eu_abundance = df.loc["EU27", "Leamer_Relative_AI_By_Non_AI_Factor_Abundance"]

                # Format the RFA values
                cn_rfa = format_rfa(cn_leamer, cn_abundance)
                us_rfa = format_rfa(us_leamer, us_abundance)
                eu_rfa = format_rfa(eu_leamer, eu_abundance)

                # Add to results
                results.append({
                    "Patent Application Type": app_type,
                    "Patent Depreciation Rate": f"{dep}%",
                    "China RFA": cn_rfa,
                    "US RFA": us_rfa,
                    "EU RFA": eu_rfa
                })

                print(f"  ✓ Depreciation rate {dep}% processed")

            except Exception as e:
                print(f"  ✗ Error processing depreciation rate {dep}%: {e}")

    # Create DataFrame
    df_final = pd.DataFrame(results)

    # Save to Excel
    output_path = os.path.join(output_dir, "robustness_tests_rfa_2021.xlsx")
    df_final.to_excel(output_path, index=False, sheet_name="RFA_Sensitivity_2021")

    print(f"\n✅ Created: {output_path}")
    print(f"\nFinal table preview:")
    print(df_final.to_string(index=False))
    print(f"\nTotal rows: {len(df_final)}")