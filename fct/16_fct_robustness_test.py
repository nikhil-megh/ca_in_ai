import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr
from scipy.stats import binomtest
import statsmodels.api as sm


FACTORS = [
    "labour",
    "capital",
    # "pct_all_ai_patents",
    # "pct_all_non_ai_patents",
    # "pct_national_ai_patents",
    # "pct_national_non_ai_patents",
    "pct_all_ai_patents_0",
    "pct_all_non_ai_patents_0",
    "pct_national_ai_patents_0",
    "pct_national_non_ai_patents_0",
    "pct_all_ai_patents_5",
    "pct_all_non_ai_patents_5",
    "pct_national_ai_patents_5",
    "pct_national_non_ai_patents_5",
    "pct_all_ai_patents_10",
    "pct_all_non_ai_patents_10",
    "pct_national_ai_patents_10",
    "pct_national_non_ai_patents_10",
    "pct_all_ai_patents_12",
    "pct_all_non_ai_patents_12",
    "pct_national_ai_patents_12",
    "pct_national_non_ai_patents_12",
    "pct_all_ai_patents_15",
    "pct_all_non_ai_patents_15",
    "pct_national_ai_patents_15",
    "pct_national_non_ai_patents_15",
    "pct_all_ai_patents_17",
    "pct_all_non_ai_patents_17",
    "pct_national_ai_patents_17",
    "pct_national_non_ai_patents_17",
    "pct_all_ai_patents_20",
    "pct_all_non_ai_patents_20",
    "pct_national_ai_patents_20",
    "pct_national_non_ai_patents_20",
    "pct_all_ai_patents_25",
    "pct_all_non_ai_patents_25",
    "pct_national_ai_patents_25",
    "pct_national_non_ai_patents_25",
    "pct_all_ai_patents_30",
    "pct_all_non_ai_patents_30",
    "pct_national_ai_patents_30",
    "pct_national_non_ai_patents_30"
]
YEARS = list(range(2010, 2022))


def run_fct_tests(base_dir):
    """
    Performs Feenstra-style FCT tests across all years and factors.

    Each Excel file: fct_<factor>.xlsx
    Each sheet (2010–2023): Weighted_Measured_FCT, Weighted_Predicted_FCT, Sign
    """
    plt.figure(figsize=(8, 6))
    results = []
    all_measured, all_predicted = [], []

    for f_i, factor in enumerate(FACTORS):
        file_path = os.path.join(base_dir, f"fct_{factor}.xlsx")
        print(f"Processing {file_path} ...")

        measured_all, predicted_all = [], []

        for year in YEARS:
            try:
                df = pd.read_excel(file_path, sheet_name=str(year))
                df = df[df.iloc[:, 0] != "Total"]
                df = df.dropna(subset=["Weighted_Measured_FCT", "Weighted_Predicted_FCT"])

                measured_all.extend(df["Weighted_Measured_FCT"].astype(float).tolist())
                predicted_all.extend(df["Weighted_Predicted_FCT"].astype(float).tolist())

                # collect for overall totals
                all_measured.extend(df["Weighted_Measured_FCT"].astype(float).tolist())
                all_predicted.extend(df["Weighted_Predicted_FCT"].astype(float).tolist())

            except Exception as e:
                print(f"⚠️ Error reading {factor}-{year}: {e}")

        measured_all = np.array(measured_all)
        predicted_all = np.array(predicted_all)
        n_obs = len(measured_all)

        # Correlation (Pearson)
        corr, corr_p = pearsonr(measured_all, predicted_all)

        # Rank correlation (Spearman)
        rank_corr, rank_p = spearmanr(measured_all, predicted_all)

        # Missing Trade Ratio
        var_meas = np.var(measured_all, ddof=1)
        var_pred = np.var(predicted_all, ddof=1)
        missing_trade_ratio = var_meas / var_pred if var_pred != 0 else np.nan

        # Sign Same Ratio
        # measured_all and predicted_all are numpy arrays
        # compute which ones have the same sign
        same_sign = np.sign(measured_all) == np.sign(predicted_all)
        # total number of comparisons (excluding zeros if needed)
        n = np.sum(measured_all != 0)  # optionally exclude zeros in measured
        k = np.sum(same_sign)  # number of matches
        # perform a one-sided binomial test: are matches significantly more than 50%?
        result = binomtest(k, n, p=0.5, alternative='greater')
        # sign-ratio with statistical significance
        same_sign_ratio = k/n
        sign_pvalue = result.pvalue

        # Regression (Measured = β0 + β1 * Predicted)
        X = sm.add_constant(predicted_all)
        model = sm.OLS(measured_all, X).fit()
        slope = model.params[1]
        t_stat = model.tvalues[1]
        r2 = model.rsquared

        results.append({
            "Factor": factor,
            "Observations": n_obs,
            "Correlation": corr,
            "Corr_pval": corr_p,
            "Rank_Corr": rank_corr,
            "Rank_pval": rank_p,
            "Missing_Trade_Ratio": missing_trade_ratio,
            "Sign_Same_Ratio": same_sign_ratio,
            "Sign_Same_pval": sign_pvalue,
            "Slope": slope,
            "Slope_tstat": t_stat,
            "R2": r2
        })

    # TOTAL (all factors + years)
    all_measured = np.array(all_measured)
    all_predicted = np.array(all_predicted)
    n_obs_total = len(all_measured)

    corr, corr_p = pearsonr(all_measured, all_predicted)
    rank_corr, rank_p = spearmanr(all_measured, all_predicted)
    var_meas = np.var(all_measured, ddof=1)
    var_pred = np.var(all_predicted, ddof=1)
    missing_trade_ratio = var_meas / var_pred if var_pred != 0 else np.nan
    # Sign Same Ratio
    same_sign = np.sign(all_measured) == np.sign(all_predicted)
    n = np.sum(all_measured != 0)
    k = np.sum(same_sign)
    result = binomtest(k, n, p=0.5, alternative='greater')
    same_sign_ratio = k / n
    sign_pvalue = result.pvalue

    X = sm.add_constant(all_predicted)
    model = sm.OLS(all_measured, X).fit()
    slope = model.params[1]
    t_stat = model.tvalues[1]
    r2 = model.rsquared

    results.append({
        "Factor": "Total",
        "Observations": n_obs_total,
        "Correlation": corr,
        "Corr_pval": corr_p,
        "Rank_Corr": rank_corr,
        "Rank_pval": rank_p,
        "Missing_Trade_Ratio": missing_trade_ratio,
        "Sign_Same_Ratio": same_sign_ratio,
        "Sign_Same_pval": sign_pvalue,
        "Slope": slope,
        "Slope_tstat": t_stat,
        "R2": r2
    })

    # Save results
    results_df = pd.DataFrame(results)
    out_path = os.path.join(base_dir, "fct_robustness_tests.xlsx")
    results_df.to_excel(out_path, index=False)
    print(f"✅ Results saved to {out_path}")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    base_directory = r"/Users/nikhil/Documents/Thesis/FCT/FCT_Tests"
    run_fct_tests(base_directory)
