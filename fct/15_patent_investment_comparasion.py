import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.stats import pearsonr

# =====================
# INPUT / OUTPUT PATHS
# =====================
input_excel_path = "/Users/nikhil/Documents/Thesis/JRC/patent_investment_comparison.xlsx"
output_excel_path = "/Users/nikhil/Documents/Thesis/JRC/patent_investment_comparison_tests.xlsx"

# =====================
# COLUMNS TO ANALYZE
# =====================
investment_columns = [
    "Public and Private AI Investment",
    "Private AI Investment in ICT Specialists, R&D, Computer Software and Databases",
    "Talent Investment per Capita",
    "Innovation Investment per Capita",
    "Infra Investment per Capita",
    "ICT specialists’ compensation",
    "Academic teachers’ compensation",
    "Corporate training",
    "Organisational capital",
    "Brand",
    "Design",
    "Research & development",
    "Computer hardware",
    "Computer software & databases",
    "Telecommunications equipment"
]

if __name__ == "__main__":

    # Load data
    df = pd.read_excel(input_excel_path, sheet_name="Patent")

    df = df.rename(columns={
        "AI Patent Stock per Million Capita": "patents"
    })

    # Excel writer
    writer = pd.ExcelWriter(output_excel_path, engine="openpyxl")

    # Store correlation coefficients for MAIN sheet
    summary_corr = []

    # Loop through investment metrics
    for col in investment_columns:
        if col not in df.columns:
            print(f"WARNING: Column '{col}' not found. Skipping.")
            continue

        print(f"Running analysis for: {col}")

        # Drop missing values
        sub_df = df.dropna(subset=["Country", "patents", col])

        # =====================
        # CORRELATION
        # =====================
        corr_coef, corr_pval = pearsonr(sub_df[col], sub_df["patents"])

        # store for summary sheet
        summary_corr.append((col, corr_coef))

        # =====================
        # OLS REGRESSION
        # =====================
        X = sm.add_constant(sub_df[col])
        y = sub_df["patents"]

        model = sm.OLS(y, X).fit()

        slope = model.params[col]
        t_stat = model.tvalues[col]
        r_squared = model.rsquared

        # =====================
        # SAVE RESULTS TABLE
        # =====================
        results_df = pd.DataFrame({
            "Metric": [
                "Correlation Coefficient",
                "Correlation p-value",
                "Regression Slope",
                "t-statistic (Slope)",
                "R-squared"
            ],
            "Value": [
                corr_coef,
                corr_pval,
                slope,
                t_stat,
                r_squared
            ]
        })

        sheet_name = col[:31]
        results_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # =====================
        # OPTIONAL: GENERATE PLOT FOR EACH COLUMN
        # =====================
        plt.figure(figsize=(12, 8))
        plt.scatter(sub_df[col], sub_df["patents"], alpha=0.7)

        x_vals = pd.Series(sorted(sub_df[col]))
        y_vals = model.params["const"] + slope * x_vals
        plt.plot(x_vals, y_vals)

        for _, row in sub_df.iterrows():
            plt.text(row[col], row["patents"], row["Country"], fontsize=8, alpha=0.8)

        plt.xlabel(f"{col} per Capita")
        plt.ylabel("AI Patent Stock per Million Capita")
        plt.title(f"{col} vs AI Patent Stock")
        plt.tight_layout()
        plt.savefig(f"/Users/nikhil/Documents/Thesis/JRC/{col.replace('/', '_')}.png", dpi=300)
        plt.close()

    # =====================
    # MAIN SUMMARY SHEET
    # =====================
    summary_df = pd.DataFrame(summary_corr, columns=["Investment Variable", "Correlation Coefficient"])
    summary_df = summary_df.sort_values(by="Correlation Coefficient", ascending=False)

    summary_df.to_excel(writer, sheet_name="MAIN", index=False)

    # Save and close
    writer.close()

    print("All analyses complete.")
    print(f"Results written to: {output_excel_path}")
