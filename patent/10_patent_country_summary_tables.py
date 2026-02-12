import pandas as pd
import numpy as np
import os

# -------- CONFIGURATION --------
INPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/PCT_Patents_By_Country.xlsx"
OUTPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/PCT_Patents_Country_Summary.xlsx"

# Define EU27 countries
EU27 = [
    "BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT",
    "CY", "LV", "LT", "LU", "HU", "MT", "NL", "AT", "PL", "PT", "RO", "SI",
    "SK", "FI", "SE"
]


def main():
    # --- Step 1: Read input file ---
    df = pd.read_excel(INPUT_PATH)
    df.columns = df.columns.str.strip()

    required_cols = [
        "Country", "Year",
        "Total Weighted Count", "AI Weighted Count", "Non AI Weighted Count",
        "Total Weighted Stock", "AI Weighted Stock", "Non AI Weighted Stock"
    ]
    assert all(col in df.columns for col in required_cols), "Missing required columns!"
    df = df[required_cols]

    # --- Step 2: Add EU27 aggregate ---
    eu27_df = (
        df[df["Country"].isin(EU27)]
        .groupby("Year", as_index=False)[
            [
                "Total Weighted Count", "AI Weighted Count", "Non AI Weighted Count",
                "Total Weighted Stock", "AI Weighted Stock", "Non AI Weighted Stock"
            ]
        ]
        .sum()
    )
    eu27_df["Country"] = "EU27"

    # --- Step 3: Global AI and Non-AI Share (Exclude EU members, include EU27) ---
    df_global = df.copy()
    df_global = df_global[~df_global["Country"].isin(EU27)]  # Exclude individual EU countries
    df_global = pd.concat([df_global, eu27_df])  # Add EU27 as one

    # AI share
    denom_ai_global = df_global.groupby("Year")["AI Weighted Stock"].sum().rename("denom")
    df_ai_global = df_global.merge(denom_ai_global, on="Year", how="left")
    df_ai_global["AI_Share"] = df_ai_global["AI Weighted Stock"] / df_ai_global["denom"]

    global_ai_share = df_ai_global.pivot(index="Country", columns="Year", values="AI_Share")
    if 2023 in global_ai_share.columns:
        global_ai_share = global_ai_share.sort_values(by=2023, ascending=False)

    # Non-AI share
    denom_nonai_global = df_global.groupby("Year")["Non AI Weighted Stock"].sum().rename("denom")
    df_nonai_global = df_global.merge(denom_nonai_global, on="Year", how="left")
    df_nonai_global["Non_AI_Share"] = df_nonai_global["Non AI Weighted Stock"] / df_nonai_global["denom"]

    global_nonai_share = df_nonai_global.pivot(index="Country", columns="Year", values="Non_AI_Share")
    if 2023 in global_nonai_share.columns:
        global_nonai_share = global_nonai_share.sort_values(by=2023, ascending=False)

    # --- Step 4: EU AI and Non-AI Share (Within EU27 only) ---
    df_eu = df.copy()
    df_eu = df_eu[df_eu["Country"].isin(EU27)]

    # AI share
    denom_ai_eu = df_eu.groupby("Year")["AI Weighted Stock"].sum().rename("denom")
    df_ai_eu = df_eu.merge(denom_ai_eu, on="Year", how="left")
    df_ai_eu["EU_AI_Share"] = df_ai_eu["AI Weighted Stock"] / df_ai_eu["denom"]

    eu_ai_share = df_ai_eu.pivot(index="Country", columns="Year", values="EU_AI_Share")
    if 2023 in eu_ai_share.columns:
        eu_ai_share = eu_ai_share.sort_values(by=2023, ascending=False)

    # Non-AI share
    denom_nonai_eu = df_eu.groupby("Year")["Non AI Weighted Stock"].sum().rename("denom")
    df_nonai_eu = df_eu.merge(denom_nonai_eu, on="Year", how="left")
    df_nonai_eu["EU_Non_AI_Share"] = df_nonai_eu["Non AI Weighted Stock"] / df_nonai_eu["denom"]

    eu_nonai_share = df_nonai_eu.pivot(index="Country", columns="Year", values="EU_Non_AI_Share")
    if 2023 in eu_nonai_share.columns:
        eu_nonai_share = eu_nonai_share.sort_values(by=2023, ascending=False)

    # --- ✅ Step 5: Global AI Intensity (AI / Total Stock per country, incl. EU27) ---
    df_global_int = df.copy()
    df_global_int = df_global_int[~df_global_int["Country"].isin(EU27)]  # Exclude individual EU countries
    df_global_int = pd.concat([df_global_int, eu27_df])  # Add EU27 as one

    # 🔹 Filter: remove countries whose Total Weighted Count in 2023 > 2000
    high_count_countries = df_global_int.loc[
        (df_global_int["Year"] == 2021) & (df_global_int["Total Weighted Count"] > 900), #triadic
        "Country"
    ].unique()
    df_global_int = df_global_int[df_global_int["Country"].isin(high_count_countries)]

    # Simple per-country ratio
    df_global_int["AI_Intensity"] = df_global_int["AI Weighted Stock"] / df_global_int["Total Weighted Stock"]

    # Pivot to wide format (countries × years)
    global_ai_intensity = df_global_int.pivot(index="Country", columns="Year", values="AI_Intensity")
    if 2023 in global_ai_intensity.columns:
        global_ai_intensity = global_ai_intensity.sort_values(by=2023, ascending=False)

    # --- ✅ Step 6: EU AI Intensity (AI / Total Stock per country within EU27) ---
    df_eu_int = df.copy()
    df_eu_int = df_eu_int[df_eu_int["Country"].isin(EU27)]
    df_eu_int["EU_AI_Intensity"] = df_eu_int["AI Weighted Stock"] / df_eu_int["Total Weighted Stock"]

    # 🔹 Filter: remove EU countries whose Total Weighted Count in 2023 > 2000
    high_count_eu = df_eu_int.loc[
        (df_eu_int["Year"] == 2021) & (df_eu_int["Total Weighted Count"] > 400), #triadic
        "Country"
    ].unique()
    df_eu_int = df_eu_int[df_eu_int["Country"].isin(high_count_eu)]

    eu27_int = eu27_df.copy()
    eu27_int["EU_AI_Intensity"] = eu27_int["AI Weighted Stock"] / eu27_int["Total Weighted Stock"]

    df_eu_int = pd.concat([df_eu_int, eu27_int], ignore_index=True)

    eu_ai_intensity = df_eu_int.pivot(index="Country", columns="Year", values="EU_AI_Intensity")
    if 2023 in eu_ai_intensity.columns:
        eu_ai_intensity = eu_ai_intensity.sort_values(by=2023, ascending=False)

    # --- Step 7: Write results to Excel ---
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        global_ai_share.to_excel(writer, sheet_name="Global_AI_Share")
        global_nonai_share.to_excel(writer, sheet_name="Global_Non_AI_Share")
        eu_ai_share.to_excel(writer, sheet_name="EU_AI_Share")
        eu_nonai_share.to_excel(writer, sheet_name="EU_Non_AI_Share")
        global_ai_intensity.to_excel(writer, sheet_name="Global_AI_Intensity")
        eu_ai_intensity.to_excel(writer, sheet_name="EU_AI_Intensity")

    print(f"✅ Output written to: {OUTPUT_PATH}")


# -------- MAIN EXECUTION GUARD --------
if __name__ == "__main__":
    main()
