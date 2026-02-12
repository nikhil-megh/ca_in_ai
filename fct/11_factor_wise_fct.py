import os
import pandas as pd
import numpy as np

# ✅ USER INPUTS — UPDATE THESE PATHS
# MEASURED_DIR = "/Users/nikhil/Documents/Thesis/FCT/Measured_FCT"
# PREDICTED_DIR = "/Users/nikhil/Documents/Thesis/FCT/Predicted_FCT"
# OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/FCT_Tests"
# SC_FILE = "/Users/nikhil/Documents/Thesis/FCT/Consumption_Shares/consumption_shares.xlsx"

MEASURED_DIR = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Measured_FCT"
PREDICTED_DIR = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Predicted_FCT"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/FCT_Tests"
SC_FILE = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Consumption_Shares/consumption_share_aggregated.xlsx"

YEARS = list(range(2010, 2022))
FACTORS = [
    "labour",
    "capital",
    "pct_all_ai_patents",
    "pct_all_non_ai_patents",
    "pct_national_ai_patents",
    "pct_national_non_ai_patents",
    # "pct_all_ai_patents_0",
    # "pct_all_non_ai_patents_0",
    # "pct_national_ai_patents_0",
    # "pct_national_non_ai_patents_0",
    # "pct_all_ai_patents_5",
    # "pct_all_non_ai_patents_5",
    # "pct_national_ai_patents_5",
    # "pct_national_non_ai_patents_5",
    # "pct_all_ai_patents_10",
    # "pct_all_non_ai_patents_10",
    # "pct_national_ai_patents_10",
    # "pct_national_non_ai_patents_10",
    # "pct_all_ai_patents_12",
    # "pct_all_non_ai_patents_12",
    # "pct_national_ai_patents_12",
    # "pct_national_non_ai_patents_12",
    # "pct_all_ai_patents_15",
    # "pct_all_non_ai_patents_15",
    # "pct_national_ai_patents_15",
    # "pct_national_non_ai_patents_15",
    # "pct_all_ai_patents_17",
    # "pct_all_non_ai_patents_17",
    # "pct_national_ai_patents_17",
    # "pct_national_non_ai_patents_17",
    # "pct_all_ai_patents_20",
    # "pct_all_non_ai_patents_20",
    # "pct_national_ai_patents_20",
    # "pct_national_non_ai_patents_20",
    # "pct_all_ai_patents_25",
    # "pct_all_non_ai_patents_25",
    # "pct_national_ai_patents_25",
    # "pct_national_non_ai_patents_25",
    # "pct_all_ai_patents_30",
    # "pct_all_non_ai_patents_30",
    # "pct_national_ai_patents_30",
    # "pct_national_non_ai_patents_30"
]


def sign_consistency(meas, pred):
    """Return 1 if both measured & predicted have same sign, else 0"""
    meas_sign = np.sign(meas)
    pred_sign = np.sign(pred)
    return int(meas_sign == pred_sign)


def process_factor(factor):
    # Load Sc (share in global consumption)
    sc_df = pd.read_excel(SC_FILE)
    sc_df.set_index("country", inplace=True)

    output_path = os.path.join(OUTPUT_DIR, f"fct_{factor}.xlsx")
    writer = pd.ExcelWriter(output_path, engine="openpyxl")

    for year in YEARS:
        measured_path = os.path.join(MEASURED_DIR, f"measured_fct_{year}.csv")
        predicted_path = os.path.join(PREDICTED_DIR, f"predicted_fct_{year}.csv")

        # Load both files
        df_meas = pd.read_csv(measured_path, index_col=0)
        df_pred = pd.read_csv(predicted_path, index_col=0)

        # Extract rows for selected factor
        meas_values = df_meas.loc[factor].to_frame(name="Measured_FCT")
        pred_values = df_pred.loc[factor].to_frame(name="Predicted_FCT")

        # Combine into a single sheet
        combined = pd.concat([meas_values, pred_values], axis=1)
        # Add columns for testing
        combined["Error"] = combined["Measured_FCT"] - combined["Predicted_FCT"]
        avg_error = combined["Error"].mean()
        combined["Variance"] = (combined["Error"] - avg_error) ** 2
        std_dev = np.sqrt(combined["Variance"].sum() / (len(combined) - 1))
        combined["Sc"] = sc_df[str(year)]
        combined["Weight"] = std_dev * np.sqrt(combined["Sc"])
        combined["Weighted_Measured_FCT"] = combined["Measured_FCT"] / combined["Weight"]
        combined["Weighted_Predicted_FCT"] = combined["Predicted_FCT"] / combined["Weight"]
        combined["Sign"] = np.where(
            combined["Weighted_Measured_FCT"] * combined["Weighted_Predicted_FCT"] > 0, 1, 0
        )
        same_sign_ratio = combined["Sign"].sum() / len(combined)

        combined.loc["Total"] = [np.nan, np.nan, avg_error, std_dev, np.nan, np.nan, np.nan, np.nan, same_sign_ratio]

        # Write sheet to file
        combined.to_excel(writer, sheet_name=str(year))

    writer.close()
    print(f"✅ Saved: {output_path}")


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


if __name__ == "__main__":
    ensure_output_dir()
    for fac in FACTORS:
        process_factor(fac)

    print("🎯 All factor comparison Excel files have been created!")
