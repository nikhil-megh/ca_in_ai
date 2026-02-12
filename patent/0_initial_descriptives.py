import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import os


def load_data(path):
    sheets = ["WO", "US", "CN", "JP", "KR", "EPO"]
    data = {sheet: pd.read_excel(path, sheet_name=sheet) for sheet in sheets}

    percent_columns = {
        "WO": ["National Phase Conversion Rate"],
        "US": ["Grant Rate"],
        "CN": ["Grant Rate"],
        "JP": ["Grant Rate"],
        "KR": ["Grant Rate"]
    }

    # Clean percent columns robustly
    for sheet, cols in percent_columns.items():
        for col in cols:
            if col in data[sheet].columns:
                data[sheet][col] = (
                    data[sheet][col]
                    .astype(str)                  # convert everything to string
                    .str.replace("%", "", regex=False)  # remove % if present
                    .str.strip()
                    .replace("", None)
                )
                data[sheet][col] = pd.to_numeric(data[sheet][col], errors="coerce")

    return data


def save_plot(fig, outdir, filename):
    os.makedirs(outdir, exist_ok=True)
    filepath = os.path.join(outdir, filename)
    fig.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close(fig)


def descriptive_1_time_series(data, outdir):
    """1. High-level time series of PCT vs national filings"""
    fig = plt.figure()

    plt.plot(data["WO"]["Year"], data["WO"]["Applications"], label="PCT Applications")
    for sheet in ["US", "JP", "KR"]:
        plt.plot(data[sheet]["Year"], data[sheet]["Applications"], label=f"{sheet} Applications")
    plt.plot(data["EPO"]["Year"], data["EPO"]["Publications"], label="EPO Publications")

    plt.title("Applications/Publications Over Time")
    plt.xlabel("Year")

    ax = plt.gca()
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((3, 3))
    ax.yaxis.set_major_formatter(formatter)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(3, 3))

    plt.ylabel("Count (Thousands)")
    plt.legend()
    plt.tight_layout()

    save_plot(fig, outdir, "1_time_series_minus_china.png")


def descriptive_2_pct_conversion(data, outdir):
    """2. PCT National Phase trends"""
    fig = plt.figure()
    plt.plot(data["WO"]["Year"], data["WO"]["National Phase"], label="National Phase Entries")
    plt.title("PCT National Phase Entries")
    plt.xlabel("Year")
    plt.ylabel("Count")
    plt.tight_layout()
    save_plot(fig, outdir, "2a_pct_national_phase.png")

    fig = plt.figure()
    plt.plot(data["WO"]["Year"], data["WO"]["National Phase Conversion Rate"], label="Conversion Rate")
    plt.title("PCT National Phase Conversion Rate")
    plt.xlabel("Year")
    plt.ylabel("%")
    plt.tight_layout()
    save_plot(fig, outdir, "2b_pct_conversion_rate.png")


def descriptive_3_ratios(data, outdir):
    """3. Ratio of national filings to PCT applications"""
    pct = data["WO"][["Year", "Applications"]].copy()
    ratios = pd.DataFrame({"Year": pct["Year"]})

    for sheet in ["US", "CN", "JP", "KR"]:
        ratios[sheet + "_Ratio"] = data[sheet]["Applications"] / pct["Applications"]

    ratios.to_csv(os.path.join(outdir, "3_ratios.csv"), index=False)
    print("\n=== Ratio of National Applications to PCT Applications ===")
    print(ratios)


def descriptive_4_grant_rates(data, outdir):
    """4. Grant rates for the major offices"""
    for sheet in ["US", "CN", "JP", "KR"]:
        fig = plt.figure()
        plt.plot(data[sheet]["Year"], data[sheet]["Grant Rate"], label=f"{sheet} Grant Rate")
        plt.title(f"{sheet} Grant Rate Over Time")
        plt.xlabel("Year")
        plt.ylabel("%")
        plt.tight_layout()
        save_plot(fig, outdir, f"4_grant_rate_{sheet}.png")


def descriptive_5_cross_comparison(data, outdir):
    """5. Cross office comparison (applications)"""
    fig = plt.figure()
    for sheet in ["US", "CN", "JP", "KR"]:
        plt.plot(data[sheet]["Year"], data[sheet]["Applications"], label=f"{sheet} Applications")
    plt.plot(data["EPO"]["Year"], data["EPO"]["Publications"], label="EPO Publications")
    plt.title("Cross-Office Filing Trends")
    plt.legend()
    plt.tight_layout()
    save_plot(fig, outdir, "5_cross_office_comparison.png")


def descriptive_6_bias_diagnostics(data, outdir):
    """6. Compare national trends vs PCT trends"""
    pct = data["WO"]

    for sheet in ["US", "CN", "JP", "KR"]:
        fig = plt.figure()
        plt.plot(pct["Year"], pct["Applications"], label="PCT Applications")
        plt.plot(data[sheet]["Year"], data[sheet]["Applications"], label=f"{sheet} Applications")
        plt.title(f"PCT vs {sheet} National Applications")
        plt.legend()
        plt.tight_layout()
        save_plot(fig, outdir, f"6_bias_pct_vs_{sheet}.png")


def descriptive_7_summary_statistics(data, outdir):
    """7. Growth rates & descriptive statistics"""
    stats = {}

    for name, df in data.items():
        if "Applications" in df.columns:
            col = "Applications"
        else:
            col = "Publications"

        df["Growth Rate"] = df[col].pct_change() * 100
        stats[name] = df[["Year", col, "Growth Rate"]]

    output_file = os.path.join(outdir, "7_summary_statistics.xlsx")
    with pd.ExcelWriter(output_file) as writer:
        for name, df in stats.items():
            df.to_excel(writer, sheet_name=name, index=False)

    print("\n=== Summary Statistics with Growth Rates ===")
    for name, df in stats.items():
        print(f"\n{name}:\n", df)


if __name__ == "__main__":
    path = "/Users/nikhil/Documents/Thesis/Patents/Patent_Office_Counts.xlsx"
    data = load_data(path)
    output_dir = "/Users/nikhil/Documents/Thesis/Patents/Plots"

    descriptive_1_time_series(data, output_dir)
    # descriptive_2_pct_conversion(data, output_dir)
    # descriptive_3_ratios(data, output_dir)
    # descriptive_4_grant_rates(data, output_dir)
    # descriptive_5_cross_comparison(data, output_dir)
    # descriptive_6_bias_diagnostics(data, output_dir)
    # descriptive_7_summary_statistics(data, output_dir)
