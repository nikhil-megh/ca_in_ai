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
        "pct_national_ai_patents",
        "pct_national_non_ai_patents",
]
YEARS = list(range(2010, 2022))
MARKERS = [
    "o",
    "s",
    "D",
    "^"
]
COLORS = [
    "tab:blue",
    "tab:orange",
    "tab:green",
    "tab:red"
]


def run_country_level_fct_tests(base_dir):
    """
    Performs Feenstra-style FCT tests but at the COUNTRY level.

    For each country:
        - Aggregates its Measured and Predicted FCT across all factors & years.
        - Runs correlations, regression, missing trade ratio, sign match tests.
    """

    # First: Collect full list of countries from the first factor’s file
    first_factor_file = os.path.join(base_dir, f"fct_{FACTORS[0]}.xlsx")
    sample_sheet = pd.read_excel(first_factor_file, sheet_name=str(YEARS[0]))
    country_list = sample_sheet.iloc[:, 0].tolist()
    country_list = [c for c in country_list if c != "Total"]

    # Storage for results and for plotting
    results = []
    all_measured_total = []
    all_predicted_total = []

    # Each country is now treated like a "factor previously"
    for country in country_list:
        country_measured = []
        country_predicted = []

        # Loop over factors and years
        for factor in FACTORS:
            file_path = os.path.join(base_dir, f"fct_{factor}.xlsx")

            for year in YEARS:
                try:
                    df = pd.read_excel(file_path, sheet_name=str(year))
                    df = df[df.iloc[:, 0] == country]

                    if df.empty:
                        continue

                    meas = df["Weighted_Measured_FCT"].astype(float).values
                    pred = df["Weighted_Predicted_FCT"].astype(float).values

                    # append
                    country_measured.extend(meas)
                    country_predicted.extend(pred)

                    # global storage for “Total”
                    all_measured_total.extend(meas)
                    all_predicted_total.extend(pred)

                except Exception as e:
                    print(f"⚠️ Error reading {factor}-{year} for {country}: {e}")

        country_measured = np.array(country_measured)
        country_predicted = np.array(country_predicted)
        n_obs = len(country_measured)

        if n_obs < 3:
            print(f"⚠️ Not enough observations for {country} — skipping.")
            continue

        # Pearson correlation
        corr, corr_p = pearsonr(country_measured, country_predicted)

        # Spearman rank correlation
        rank_corr, rank_p = spearmanr(country_measured, country_predicted)

        # Missing trade ratio
        var_meas = np.var(country_measured, ddof=1)
        var_pred = np.var(country_predicted, ddof=1)
        missing_trade_ratio = var_meas / var_pred if var_pred != 0 else np.nan

        # # Sign agreement
        # same_sign_ratio = np.mean(np.sign(country_measured) == np.sign(country_predicted))
        # Sign Same Ratio
        same_sign = np.sign(country_measured) == np.sign(country_predicted)
        n = np.sum(country_measured != 0)
        k = np.sum(same_sign)
        result = binomtest(k, n, p=0.5, alternative='greater')
        same_sign_ratio = k / n
        sign_pvalue = result.pvalue

        # Regression
        X = sm.add_constant(country_predicted)
        model = sm.OLS(country_measured, X).fit()
        slope = model.params[1]
        t_stat = model.tvalues[1]
        r2 = model.rsquared

        results.append({
            "Country": country,
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

    # -----------------------------
    # TOTAL (all countries + factors + years)
    # -----------------------------

    all_measured_total = np.array(all_measured_total)
    all_predicted_total = np.array(all_predicted_total)
    n_obs_total = len(all_measured_total)

    corr, corr_p = pearsonr(all_measured_total, all_predicted_total)
    rank_corr, rank_p = spearmanr(all_measured_total, all_predicted_total)
    var_meas = np.var(all_measured_total, ddof=1)
    var_pred = np.var(all_predicted_total, ddof=1)
    missing_trade_ratio = var_meas / var_pred if var_pred != 0 else np.nan
    # same_sign_ratio = np.mean(np.sign(all_measured_total) == np.sign(all_predicted_total))
    # Sign Same Ratio
    same_sign = np.sign(all_measured_total) == np.sign(all_predicted_total)
    n = np.sum(all_measured_total != 0)
    k = np.sum(same_sign)
    result = binomtest(k, n, p=0.5, alternative='greater')
    same_sign_ratio = k / n
    sign_pvalue = result.pvalue

    X = sm.add_constant(all_predicted_total)
    model = sm.OLS(all_measured_total, X).fit()

    results.append({
        "Country": "Total",
        "Observations": n_obs_total,
        "Correlation": corr,
        "Corr_pval": corr_p,
        "Rank_Corr": rank_corr,
        "Rank_pval": rank_p,
        "Missing_Trade_Ratio": missing_trade_ratio,
        "Sign_Same_Ratio": same_sign_ratio,
        "Sign_Same_pval": sign_pvalue,
        "Slope": model.params[1],
        "Slope_tstat": model.tvalues[1],
        "R2": model.rsquared
    })

    # -----------------------------
    # Scatter plot for TOTAL
    # -----------------------------
    plt.figure(figsize=(8, 6))
    plt.scatter(all_predicted_total, all_measured_total, alpha=0.5)

    min_val = min(all_predicted_total.min(), all_measured_total.min())
    max_val = max(all_predicted_total.max(), all_measured_total.max())
    line_x = np.linspace(min_val, max_val, 200)

    plt.plot(line_x, model.params[0] + model.params[1] * line_x, "k-", label="Linear fit")
    plt.plot(line_x, line_x, "--", color="gray", label="45° line")

    plt.xlabel("Predicted FCT")
    plt.ylabel("Measured FCT")
    plt.title("FCT Test (Country-Level)")
    plt.grid(True, linestyle=":")
    plt.legend()
    plt.tight_layout()

    plot_path = os.path.join(base_dir, "fct_country_scatter_plot.png")
    plt.savefig(plot_path, dpi=300)
    print(f"📈 Country-level plot saved to {plot_path}")

    # -----------------------------
    # Save results
    # -----------------------------
    results_df = pd.DataFrame(results)
    out_path = os.path.join(base_dir, "fct_country_tests.xlsx")
    results_df.to_excel(out_path, index=False)
    print(f"✅ Country-level results saved to {out_path}")


if __name__ == "__main__":
    base_directory = r"/Users/nikhil/Documents/Thesis/FCT/FCT_Tests"
    run_country_level_fct_tests(base_directory)
