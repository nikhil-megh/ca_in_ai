import pandas as pd
from pathlib import Path

FACTOR_FILES = {
    "labour": "/Users/nikhil/Documents/Thesis/Labour/EMP_figaro2025.xlsx",
    "capital": "/Users/nikhil/Documents/Thesis/Capital/CAPITAL_figaro2025.xlsx",
    "pct_all_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_all_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
}

OUTPUT_DIR = Path("/Users/nikhil/Documents/Thesis/FCT/Matrices/Factor_Vectors")

YEARS = list(range(2010, 2022))  # 2010–2021

if __name__ == "__main__":
    # Load everything first
    data = {}
    for factor_name, filepath in FACTOR_FILES.items():
        print(f"Loading: {factor_name} from {filepath}")
        df = pd.read_excel(filepath, sheet_name="Final")

        # Ensure factor_key column exists and is index
        if df.columns[0] != "factor_key":
            df.rename(columns={df.columns[0]: "factor_key"}, inplace=True)
        df.set_index("factor_key", inplace=True)
        df.columns = df.columns.map(str)

        data[factor_name] = df

    # Create year-wise files
    for year in YEARS:
        year_str = str(year)

        rows = []
        for factor_name, df in data.items():
            if year_str not in df.columns:
                raise ValueError(f"⚠️ Year {year_str} missing in factor: {factor_name}")

            series = df[year_str]
            series.name = factor_name  # set row label
            rows.append(series)

        # Combine and transpose horizontally (rows=6 factors)
        out_df = pd.DataFrame(rows)

        outfile = OUTPUT_DIR / f"factors_{year}.csv"
        out_df.to_csv(outfile, float_format="%.3f")

        print(f"✅ Saved {outfile}  ({out_df.shape[0]} rows × {out_df.shape[1]} columns)")

    print("\n🎯 All factor vectors generated successfully!")
