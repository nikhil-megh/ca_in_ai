import os
import pandas as pd
import numpy as np

# === Static directories ===
# production_factors_dir = "/Users/nikhil/Documents/Thesis/FCT/Factor_Endowments"
# measured_fct_dir = "/Users/nikhil/Documents/Thesis/FCT/Measured_FCT"
# consumption_share_path = "/Users/nikhil/Documents/Thesis/FCT/Consumption_Shares/consumption_shares.xlsx"
# output_excel_path = "/Users/nikhil/Documents/Thesis/FCT/Results/PCT_National/eu_relative_factor_abundance.xlsx"
# TARGET = ["DE", "FR", "NL", "SE", "FI", "IT"]

production_factors_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Factor_Endowments"
measured_fct_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Measured_FCT"
consumption_share_path = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Consumption_Shares/consumption_share_aggregated.xlsx"
output_excel_path = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_National/relative_factor_abundance.xlsx"
TARGET = ["US", "CN", "EU27", "JP", "KR"]


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

            # Get consumption share for each country for the given year
            Consumption_share = df_cons_share[str(year)]

            # === Restrict to the TARGET countries ===
            countries = [c for c in TARGET if c in df_prod.columns]

            # Extract relevant rows
            ai_prod = df_prod.loc["pct_national_ai_patents", countries]
            non_ai_prod = df_prod.loc["pct_national_non_ai_patents", countries]

            ai_measured_fct = df_measured_fct.loc["pct_national_ai_patents", countries]
            non_ai_measured_fct = df_measured_fct.loc["pct_national_non_ai_patents", countries]

            Consumption_share = Consumption_share.reindex(countries)

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

            # Debaere bilateral FCT
            positive_debaere_counts = []
            Fstar_AI = pd.Series(safe_divide(ai_measured_fct, Consumption_share), index=countries)
            Vstar_AI = pd.Series(safe_divide(ai_prod, Consumption_share), index=countries)
            Fstar_nonAI = pd.Series(safe_divide(non_ai_measured_fct, Consumption_share), index=countries)
            Vstar_nonAI = pd.Series(safe_divide(non_ai_prod, Consumption_share), index=countries)
            for i in countries:
                count_pos = 0
                for j in countries:
                    if i == j:
                        continue
                    # numerator and denominator for factor f = AI
                    num_AI = Fstar_AI[i] - Fstar_AI[j]
                    den_AI = Vstar_AI[i] + Vstar_AI[j]
                    val_AI = safe_divide(num_AI, den_AI)
                    # numerator and denominator for factor f' = non-AI
                    num_nonAI = Fstar_nonAI[i] - Fstar_nonAI[j]
                    den_nonAI = Vstar_nonAI[i] + Vstar_nonAI[j]
                    val_nonAI = safe_divide(num_nonAI, den_nonAI)
                    # Debaere Eq. (5): double-difference across factors
                    deb_val = val_AI - val_nonAI
                    if deb_val > 0:
                        count_pos += 1
                positive_debaere_counts.append(count_pos)

            # Build output DataFrame
            df_out = pd.DataFrame({
                "Production_AI_By_Non_AI": production_ratio,
                "Measured_FCT_AI_By_Non_AI": fct_ratio,
                "Consumption_AI_By_Non_AI": consumption_ratio,
                "Leamer_AI_By_Non_AI": Leamer_Production_By_Consumption,
                "Leamer_Relative_AI_By_Non_AI_Factor_Abundance": relative_abundance,
                "Positive_Debaere_Bilateral_FCT": positive_debaere_counts
            }, index=countries)

            # Write each year as a separate sheet in the same Excel file
            df_out.to_excel(writer, sheet_name=str(year), index_label="Country")
            print(f"✅ Processed year {year}: added to Excel workbook")

