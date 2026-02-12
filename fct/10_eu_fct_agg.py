import os
import pandas as pd

EU27 = [
    "BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT",
    "CY", "LV", "LT", "LU", "HU", "MT", "NL", "AT", "PL", "PT", "RO", "SI",
    "SK", "FI", "SE"
]


def aggregate_eu27_columns(df: pd.DataFrame, eu_list=EU27, new_col="EU27"):
    """
    Sum the values across all EU27 columns, drop them, insert aggregated EU27 column.
    """
    eu_cols = [c for c in df.columns if c in eu_list]
    df[new_col] = df[eu_cols].sum(axis=1)
    df = df.drop(columns=eu_cols)
    return df


def aggregate_eu27_rows(df: pd.DataFrame, eu_list=EU27, new_row="EU27"):
    """
    For the consumption share panel: rows are countries and columns are years.
    Aggregate EU rows into one.
    """
    eu_rows = df.index.intersection(eu_list)
    df.loc[new_row] = df.loc[eu_rows].sum(axis=0)
    df = df.drop(index=eu_rows)
    return df


def process_factor_files(input_dir, output_dir, file_prefix):
    """
    Loads 2010–2023 CSV factor files, aggregates EU27 columns, and saves output.
    """
    os.makedirs(output_dir, exist_ok=True)

    for year in range(2010, 2022):
        file_path = os.path.join(input_dir, f"{file_prefix}_{year}.csv")
        df = pd.read_csv(file_path, index_col=0)

        # Aggregate EU27 columns
        df = aggregate_eu27_columns(df)

        # Save output
        out_path = os.path.join(output_dir, f"{file_prefix}_{year}.csv")
        df.to_csv(out_path)


def process_consumption_share(consumption_path, output_dir):
    """
    Loads consumption share Excel sheet, aggregates EU27 rows, and saves output.
    """
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_excel(consumption_path, index_col=0)

    # Aggregate rows for EU27
    df = aggregate_eu27_rows(df)

    out_path = os.path.join(output_dir, "consumption_share_aggregated.xlsx")
    df.to_excel(out_path)


# ===============================================================
# Main Execution
# ===============================================================
if __name__ == "__main__":

    # --- STATIC STRING INPUTS (edit these) ---
    measured_fct_input_dir = "/Users/nikhil/Documents/Thesis/FCT/Measured_FCT/"
    predicted_fct_input_dir = "/Users/nikhil/Documents/Thesis/FCT/Predicted_FCT/"
    factor_endowments_input_dir = "/Users/nikhil/Documents/Thesis/FCT/Factor_Endowments/"
    consumption_share_path = "/Users/nikhil/Documents/Thesis/FCT/Consumption_Shares/consumption_shares.xlsx"

    measured_fct_output_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Measured_FCT/"
    predicted_fct_output_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Predicted_FCT/"
    factor_endowments_output_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Factor_Endowments/"
    consumption_share_output_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Consumption_Shares/"

    # --- Process each dataset ---
    process_factor_files(measured_fct_input_dir, measured_fct_output_dir, "measured_fct")
    process_factor_files(predicted_fct_input_dir, predicted_fct_output_dir, "predicted_fct")
    process_factor_files(factor_endowments_input_dir, factor_endowments_output_dir, "factor_endowments")

    process_consumption_share(consumption_share_path, consumption_share_output_dir)
