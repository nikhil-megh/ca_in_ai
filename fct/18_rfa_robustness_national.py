import os
import pandas as pd
import numpy as np

# === Directories ===
production_factors_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Factor_Endowments"
measured_fct_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Measured_FCT"
consumption_share_path = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Consumption_Shares/consumption_share_aggregated.xlsx"
output_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_National"

TARGET = ["US", "CN", "EU27", "JP", "KR"]
DEP_RATES = [0, 5, 10, 12, 15, 17, 20, 25, 30]


def safe_divide(numerator, denominator):
    if np.isscalar(numerator) and np.isscalar(denominator):
        if denominator == 0 or not np.isfinite(denominator) or not np.isfinite(numerator):
            return 0.0
        return numerator / denominator
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.true_divide(numerator, denominator)
        return np.where(np.isfinite(result), result, 0)


if __name__ == "__main__":

    # Read consumption shares once
    df_cons_share = pd.read_excel(consumption_share_path, index_col=0)

    for dep in DEP_RATES:
        print(f"\n▶ Processing depreciation rate = {dep}")

        output_excel_path = os.path.join(
            output_dir, f"rfa_robustness_{dep}.xlsx"
        )

        ai_row = f"pct_national_ai_patents_{dep}"
        non_ai_row = f"pct_national_non_ai_patents_{dep}"

        with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:

            for year in range(2010, 2022):

                prod_path = os.path.join(
                    production_factors_dir, f"factor_endowments_{year}.csv"
                )
                measured_fct_path = os.path.join(
                    measured_fct_dir, f"measured_fct_{year}.csv"
                )

                df_prod = pd.read_csv(prod_path, index_col=0)
                df_measured_fct = pd.read_csv(measured_fct_path, index_col=0)

                Consumption_share = df_cons_share[str(year)]

                countries = [c for c in TARGET if c in df_prod.columns]

                # === Extract factors for this depreciation rate ===
                ai_prod = df_prod.loc[ai_row, countries]
                non_ai_prod = df_prod.loc[non_ai_row, countries]

                ai_measured_fct = df_measured_fct.loc[ai_row, countries]
                non_ai_measured_fct = df_measured_fct.loc[non_ai_row, countries]

                Consumption_share = Consumption_share.reindex(countries)

                # === Ratios ===
                production_ratio = safe_divide(ai_prod.values, non_ai_prod.values)
                fct_ratio = safe_divide(ai_measured_fct.values, non_ai_measured_fct.values)
                consumption_ratio = safe_divide(
                    ai_prod.values - ai_measured_fct.values,
                    non_ai_prod.values - non_ai_measured_fct.values
                )

                Leamer_Production_By_Consumption = safe_divide(
                    production_ratio, consumption_ratio
                )

                relative_abundance = np.where(
                    production_ratio > consumption_ratio, "Yes", "No"
                )

                # === Debaere bilateral FCT ===
                positive_debaere_counts = []

                Fstar_AI = pd.Series(
                    safe_divide(ai_measured_fct, Consumption_share), index=countries
                )
                Vstar_AI = pd.Series(
                    safe_divide(ai_prod, Consumption_share), index=countries
                )
                Fstar_nonAI = pd.Series(
                    safe_divide(non_ai_measured_fct, Consumption_share), index=countries
                )
                Vstar_nonAI = pd.Series(
                    safe_divide(non_ai_prod, Consumption_share), index=countries
                )

                for i in countries:
                    count_pos = 0
                    for j in countries:
                        if i == j:
                            continue

                        val_AI = safe_divide(
                            Fstar_AI[i] - Fstar_AI[j],
                            Vstar_AI[i] + Vstar_AI[j]
                        )
                        val_nonAI = safe_divide(
                            Fstar_nonAI[i] - Fstar_nonAI[j],
                            Vstar_nonAI[i] + Vstar_nonAI[j]
                        )

                        if (val_AI - val_nonAI) > 0:
                            count_pos += 1

                    positive_debaere_counts.append(count_pos)

                # === Output ===
                df_out = pd.DataFrame({
                    "Production_AI_By_Non_AI": production_ratio,
                    "Measured_FCT_AI_By_Non_AI": fct_ratio,
                    "Consumption_AI_By_Non_AI": consumption_ratio,
                    "Leamer_AI_By_Non_AI": Leamer_Production_By_Consumption,
                    "Leamer_Relative_AI_By_Non_AI_Factor_Abundance": relative_abundance,
                    "Positive_Debaere_Bilateral_FCT": positive_debaere_counts
                }, index=countries)

                df_out.to_excel(writer, sheet_name=str(year), index_label="Country")

                print(f"  ✓ Year {year} written")

        print(f"✅ Finished: rfa_robustness_{dep}.xlsx")
