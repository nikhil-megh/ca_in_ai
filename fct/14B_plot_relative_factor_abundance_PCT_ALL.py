import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# INPUT_EXCEL_PATH = "/Users/nikhil/Documents/Thesis/FCT/Results/PCT_All/relative_factor_abundance.xlsx"
# OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT/Results/PCT_All"

INPUT_EXCEL_PATH = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_All/rfa_robustness_15.xlsx"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_All"


def load_leamer_data(excel_path):
    """Load Leamer Relative AI data from each sheet (2010–2023)."""
    years = list(range(2010, 2022))
    df_all = []

    for year in years:
        sheet_name = str(year)
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        df["Year"] = year
        df_all.append(df)

    full_df = pd.concat(df_all, ignore_index=True)
    return full_df


def plot_leamer_factor_abundance(df, output_dir):
    """Plot Leamer_Relative_AI_By_Non_AI_Factor_Abundance with shading."""
    countries = df["Country"].unique()

    plt.figure(figsize=(14, 7))

    # Plot each country’s time series
    for country in countries:
        subset = df[df["Country"] == country]
        plt.plot(
            subset["Year"],
            subset["Leamer_AI_By_Non_AI"],
            marker="o",
            linewidth=1,
            label=country
        )

    x_vals = sorted(df["Year"].unique())

    y_min = df["Leamer_AI_By_Non_AI"].min() - 0.1
    y_max = df["Leamer_AI_By_Non_AI"].max() + 0.1
    plt.ylim(y_min, y_max)

    # Shaded region ABOVE 1 (relative abundant)
    plt.fill_between(
        x_vals, 1, max(df["Leamer_AI_By_Non_AI"]) + 0.1,
        color="lightgreen", alpha=0.3,
        label="Relative factor abundant ( > 1 )"
    )

    # Shaded region BELOW 1 (relative scarce)
    plt.fill_between(
        x_vals, 0, 1,
        color="lightcoral", alpha=0.3,
        label="Relative factor scarce ( < 1 )"
    )

    plt.axhline(1, color="black", linewidth=1, linestyle="--")

    plt.title("Leamer Relative AI By Non-AI Factor Abundance (2010–2022)")
    plt.xlabel("Year")
    plt.ylabel("Leamer Relative AI Factor Abundance")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "Leamer_Relative_Factor_Abundance.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Plot saved to: {output_path}")


if __name__ == "__main__":
    df = load_leamer_data(INPUT_EXCEL_PATH)
    plot_leamer_factor_abundance(df, OUTPUT_DIR)
