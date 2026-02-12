import pandas as pd

# -------- CONFIGURATION --------
ALL_PATENTS_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/All_Patents/PCT_All_Patents_By_Industry_Year.xlsx"
AI_PATENTS_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_Patents/PCT_AI_Patents_By_Industry_Year.xlsx"
OUTPUT_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/PCT_Patents_By_Industry.xlsx"


def main():
    # -------- LOAD DATA --------
    df_all = pd.read_excel(ALL_PATENTS_FILE)
    df_ai = pd.read_excel(AI_PATENTS_FILE)

    # Ensure consistent column names
    df_all.columns = df_all.columns.str.strip()
    df_ai.columns = df_ai.columns.str.strip()

    # -------- MERGE AND CALCULATE --------
    merged = pd.merge(
        df_all,
        df_ai,
        on=["Country", "Industry Code", "Year"],
        how="left",
        suffixes=("_all", "_ai")
    )

    # Fill missing AI counts with 0
    merged["Count_ai"] = merged["Count_ai"].fillna(0)

    # Compute non-AI patents
    merged["Non AI Count"] = merged["Count_all"] - merged["Count_ai"]

    # -------- HANDLE NEGATIVE VALUES --------
    # If Non AI Count < 0, set AI Count = Total Count and Non AI Count = 0
    mask = merged["Non AI Count"] < 0
    merged.loc[mask, "Count_ai"] = merged.loc[mask, "Count_all"]
    merged.loc[mask, "Non AI Count"] = 0

    # -------- CLEAN AND SAVE --------
    # Rename columns for clarity
    merged = merged.rename(
        columns={
            "Count_all": "Total Count",
            "Count_ai": "AI Count"
        }
    )

    # Keep only desired columns
    result = merged[["Country", "Industry Code", "Year", "Total Count", "AI Count", "Non AI Count"]]

    # Save to Excel
    result.to_excel(OUTPUT_FILE, index=False)

    print(f"✅ Patent summary (Total, AI, Non-AI) saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
