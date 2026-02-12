import os
import pandas as pd
import numpy as np

# === Static directories ===
# production_factors_dir = "/Users/nikhil/Documents/Thesis/FCT/Factor_Endowments"
# measured_fct_dir = "/Users/nikhil/Documents/Thesis/FCT/Measured_FCT"
# consumption_share_path = "/Users/nikhil/Documents/Thesis/FCT/Consumption_Shares/consumption_shares.xlsx"
# output_excel_path = "/Users/nikhil/Documents/Thesis/FCT/Results/PCT_All/single_factor_abundance.xlsx"

production_factors_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Factor_Endowments"
measured_fct_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Measured_FCT"
consumption_share_path = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Consumption_Shares/consumption_share_aggregated.xlsx"
output_excel_path = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_All/single_factor_abundance.xlsx"


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


if __name__ == "__main__":
    # Read the Excel sheet containing consumption shares
    df_cons_share = pd.read_excel(consumption_share_path, index_col=0)

    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        # Process for each year from 2010 to 2021
        for year in range(2010, 2022):
            # Construct file paths
            prod_path = os.path.join(production_factors_dir, f"factor_endowments_{year}.csv")
            measured_fct_path = os.path.join(measured_fct_dir, f"measured_fct_{year}.csv")

            # Read CSVs
            df_prod = pd.read_csv(prod_path, index_col=0)
            df_measured_fct = pd.read_csv(measured_fct_path, index_col=0)

            # Extract relevant rows
            ai_prod = df_prod.loc["pct_all_ai_patents"]
            non_ai_prod = df_prod.loc["pct_all_non_ai_patents"]

            ai_measured_fct = df_measured_fct.loc["pct_all_ai_patents"]
            non_ai_measured_fct = df_measured_fct.loc["pct_all_non_ai_patents"]

            # Get AI_measured_fct directly from df_fct
            AI_measured_fct = df_measured_fct.loc["pct_all_ai_patents"]

            # Get consumption share for each country for the given year
            Consumption_share = df_cons_share[str(year)]

            # Compute factor_endowment_share
            AI_prod_factor = df_prod.loc["pct_all_ai_patents"]
            total_AI_patents = AI_prod_factor.sum()
            Treffler_Factor_Abundance = safe_divide(AI_prod_factor, total_AI_patents)

            countries = df_prod.columns
            n = len(countries)

            # Hakura bilateral FCT
            positive_hakura_counts = []
            for i in countries:
                count_pos = 0
                for j in countries:
                    if i == j:
                        continue
                    a_ij = safe_divide(Consumption_share[i], Consumption_share[j])
                    hakura_val = ai_measured_fct[i] - a_ij * ai_measured_fct[j]
                    if hakura_val > 0:
                        count_pos += 1
                positive_hakura_counts.append(count_pos)

            # Build output DataFrame
            df_out = pd.DataFrame({
                "AI_Factor_Endowment": AI_prod_factor,
                "Consumption_Share": Consumption_share,
                "Treffler_AI_Patent_Factor_Abundance": Treffler_Factor_Abundance,
                "AI_Measured_FCT": AI_measured_fct,
                "Positive_Hakura_Bilateral_FCT": positive_hakura_counts,
            }, index=df_prod.columns)

            # Write each year as a separate sheet in the same Excel file
            df_out.to_excel(writer, sheet_name=str(year), index_label="Country")
            print(f"✅ Processed year {year}: added to Excel workbook")

