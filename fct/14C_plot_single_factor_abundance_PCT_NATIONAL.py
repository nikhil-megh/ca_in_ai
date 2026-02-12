import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap

# === Static input ===
# input_excel_path = "/Users/nikhil/Documents/Thesis/FCT/Results/PCT_National/single_factor_abundance.xlsx"
# output_dir = "/Users/nikhil/Documents/Thesis/FCT/Results/PCT_National"
# countries_to_plot = ["US", "CN", "JP", "KR", "DE", "FR", "NL", "SE", "FI", "GB"]

input_excel_path = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_National/single_factor_abundance.xlsx"
output_dir = "/Users/nikhil/Documents/Thesis/FCT_EU_aggregated/Results/PCT_National"
countries_to_plot = ["US", "CN", "EU27", "JP", "KR"]

# === Columns to plot (variable name → pretty title) ===
variables = {
    "Treffler_AI_Patent_Factor_Abundance": "Treffler AI Patent Share",
    "AI_Measured_FCT": "AI Patents Measured FCT",
    "Positive_Hakura_Bilateral_FCT": "Hakura Bilateral FCT Positive Count"
}


def plot_over_time(df, column, title, ylabel):
    plt.figure(figsize=(10, 6))

    # Use a colormap with enough distinct colors
    cmap = get_cmap("tab10", len(countries_to_plot))  # tab20 gives up to 20 distinct colors
    colors = [cmap(i) for i in range(len(countries_to_plot))]

    for i, country in enumerate(countries_to_plot):
        subset = df[df["Country"] == country]
        if not subset.empty:
            plt.plot(
                subset["Year"],
                subset[column],
                marker="o",
                linewidth=2,
                label=country,
                color=colors[i],
                markersize=5,
                alpha=0.9
            )

    plt.title(title, fontsize=14, weight="bold")
    plt.xlabel("Year", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.legend(
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=9,
        ncol=1,
        title="Country",
        title_fontsize=10
    )
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout(rect=[0, 0, 0.85, 1])  # leave room for legend

    # Save the plot
    save_path = os.path.join(output_dir, f"{column}.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"✅ Saved plot: {save_path}")


if __name__ == "__main__":
    # === Step 1: Read all yearly sheets ===
    xls = pd.ExcelFile(input_excel_path)
    all_years = {}

    for sheet in xls.sheet_names:
        try:
            if int(sheet) > 2022:
                continue
            df = pd.read_excel(input_excel_path, sheet_name=sheet, index_col="Country")
            df["Year"] = int(sheet)
            all_years[int(sheet)] = df
        except Exception as e:
            print(f"⚠️ Skipping sheet {sheet}: {e}")

    # Combine all into one DataFrame
    df_all = pd.concat(all_years.values())
    df_all.reset_index(inplace=True)

    # Keep only desired countries and years (sort them)
    df_all = df_all[df_all["Country"].isin(countries_to_plot)]
    df_all.sort_values(by=["Country", "Year"], inplace=True)

    # === Step 2: Generate 4 Plots ===
    for col, title in variables.items():
        if col in df_all.columns:
            plot_over_time(df_all, col, title, title)
        else:
            print(f"⚠️ Column '{col}' not found in data — skipping.")

    print("\n🎯 All plots generated successfully!")
