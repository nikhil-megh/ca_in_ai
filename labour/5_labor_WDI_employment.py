import pandas as pd

def compute_employment(df):
    # Identify year columns dynamically
    year_cols = [c for c in df.columns if "[YR" in c]

    # Convert all year columns to numeric (force non-numeric → NaN)
    df[year_cols] = df[year_cols].apply(pd.to_numeric, errors="coerce")

    # Split the dataframe by series code
    emp_ratio = df[df["Series Code"] == "SL.EMP.TOTL.SP.ZS"]
    pop_15_64 = df[df["Series Code"] == "SP.POP.1564.TO"]
    pop_65_up = df[df["Series Code"] == "SP.POP.65UP.TO"]

    # Merge on Country Name and Code
    merged = emp_ratio.merge(
        pop_15_64,
        on=["Country Name", "Country Code"],
        suffixes=("_emp", "_pop1564")
    ).merge(
        pop_65_up,
        on=["Country Name", "Country Code"]
    )

    # Compute both employment estimates for each year
    for y in year_cols:
        emp_col = f"{y}_emp" if f"{y}_emp" in merged.columns else y  # handle safe lookup
        pop1564_col = f"{y}_pop1564" if f"{y}_pop1564" in merged.columns else y
        pop65_col = y  # population 65+ column

        merged[f"Employment_15_64_{y}"] = (
            (merged[emp_col] / 100.0) * (merged[pop1564_col] / 1000.0)
        )
        merged[f"Employment_15plus_{y}"] = (
            merged[emp_col] / 100.0 * ((merged[pop1564_col] + merged[pop65_col]) / 1000.0)
        )

    # Select only relevant output columns
    keep_cols = ["Country Name", "Country Code"] + [
        c for c in merged.columns if c.startswith("Employment_")
    ]

    employment_15_64 = merged[["Country Name", "Country Code"] +
                               [c for c in merged.columns if "Employment_15_64" in c]]
    employment_15plus = merged[["Country Name", "Country Code"] +
                                [c for c in merged.columns if "Employment_15plus" in c]]

    # Write results
    employment_15_64.to_excel("/Users/nikhil/Downloads/employment_15_64.xlsx", index=False)
    employment_15plus.to_excel("/Users/nikhil/Downloads/employment_15plus.xlsx", index=False)
    print("✅ Saved employment_15_64.xlsx and employment_15plus.xlsx")


def main():
    INPUT_PATH = "/Users/nikhil/Downloads/WDI_employment_ratio.xlsx"
    df = pd.read_excel(INPUT_PATH)
    compute_employment(df)


if __name__ == "__main__":
    main()
