import pandas as pd
import numpy as np
import os

# -------- CONFIGURATION --------
INPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/Descriptives_Industry/PCT_Patents_By_Industry.xlsx"
OUTPUT_PATH = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/Descriptives_Industry/PCT_Patents_Industry_Summary.xlsx"

# Define EU27 countries
EU27 = [
    "BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT",
    "CY", "LV", "LT", "LU", "HU", "MT", "NL", "AT", "PL", "PT", "RO", "SI",
    "SK", "FI", "SE"
]

# Define industry codes (for filtering if needed)
INDUSTRY_CODES = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]


def main():
    # --- Step 1: Read input file ---
    df = pd.read_excel(INPUT_PATH)
    df.columns = df.columns.str.strip()

    required_cols = [
        "Country", "Industry Code", "Year",
        "Total Count", "AI Count", "Non AI Count",
        "Total Stock", "AI Stock", "Non AI Stock"
    ]
    assert all(col in df.columns for col in required_cols), "Missing required columns!"
    df = df[required_cols]

    # --- Step 3: Add EU27 aggregate (sum across EU countries by Industry × Year) ---
    eu27_df = (
        df[df["Country"].isin(EU27)]
        .groupby(["Industry Code", "Year"], as_index=False)[
            ["Total Count", "AI Count", "Non AI Count",
             "Total Stock", "AI Stock", "Non AI Stock"]
        ]
        .sum()
    )
    eu27_df["Country"] = "EU27"

    # --- Step 4: Global AI and Non AI Industry Share ---
    # Exclude EU27 members individually (treat EU27 as one)
    df_global = df[~df["Country"].isin(EU27)]
    df_global = pd.concat([df_global, eu27_df], ignore_index=True)

    # AI Share
    # Compute global AI stock share by industry
    global_ai = (
        df_global.groupby(["Industry Code", "Year"], as_index=False)["AI Stock"].sum()
    )

    total_global_ai = global_ai.groupby("Year")["AI Stock"].sum().rename("Total_AI_Stock")
    global_ai = global_ai.merge(total_global_ai, on="Year", how="left")
    global_ai["AI_Industry_Share"] = global_ai["AI Stock"] / global_ai["Total_AI_Stock"]

    # Pivot to wide format
    global_ai_share = global_ai.pivot(index="Industry Code", columns="Year", values="AI_Industry_Share")

    # Sort industries by 2023 share descending
    if 2023 in global_ai_share.columns:
        global_ai_share = global_ai_share.sort_values(by=2023, ascending=False)

    # Non AI Share
    # Compute global Non AI stock share by industry
    global_nonai = (
        df_global.groupby(["Industry Code", "Year"], as_index=False)["Non AI Stock"].sum()
    )

    total_global_nonai = global_nonai.groupby("Year")["Non AI Stock"].sum().rename("Total_Non_AI_Stock")
    global_nonai = global_nonai.merge(total_global_nonai, on="Year", how="left")
    global_nonai["Non_AI_Industry_Share"] = global_nonai["Non AI Stock"] / global_nonai["Total_Non_AI_Stock"]

    # Pivot to wide format
    global_nonai_share = global_nonai.pivot(index="Industry Code", columns="Year", values="Non_AI_Industry_Share")

    # Sort industries by 2023 share descending
    if 2023 in global_nonai_share.columns:
        global_nonai_share = global_nonai_share.sort_values(by=2023, ascending=False)

    # --- Step 5: EU AI and Non-AI Industry Share ---
    df_eu = df[df["Country"].isin(EU27)]

    # AI Share
    eu_ai = (
        df_eu.groupby(["Industry Code", "Year"], as_index=False)["AI Stock"].sum()
    )

    total_eu_ai = eu_ai.groupby("Year")["AI Stock"].sum().rename("Total_AI_Stock")
    eu_ai = eu_ai.merge(total_eu_ai, on="Year", how="left")
    eu_ai["EU_AI_Industry_Share"] = eu_ai["AI Stock"] / eu_ai["Total_AI_Stock"]

    # Pivot to wide format
    eu_ai_share = eu_ai.pivot(index="Industry Code", columns="Year", values="EU_AI_Industry_Share")

    # Sort by 2023 descending
    if 2023 in eu_ai_share.columns:
        eu_ai_share = eu_ai_share.sort_values(by=2023, ascending=False)

    # Non AI Share
    eu_nonai = (
        df_eu.groupby(["Industry Code", "Year"], as_index=False)["Non AI Stock"].sum()
    )

    total_eu_nonai = eu_nonai.groupby("Year")["Non AI Stock"].sum().rename("Total_Non_AI_Stock")
    eu_nonai = eu_nonai.merge(total_eu_nonai, on="Year", how="left")
    eu_nonai["EU_Non_AI_Industry_Share"] = eu_nonai["Non AI Stock"] / eu_nonai["Total_Non_AI_Stock"]

    # Pivot to wide format
    eu_nonai_share = eu_nonai.pivot(index="Industry Code", columns="Year", values="EU_Non_AI_Industry_Share")

    # Sort by 2023 descending
    if 2023 in eu_nonai_share.columns:
        eu_nonai_share = eu_nonai_share.sort_values(by=2023, ascending=False)

    # --- Step 6: Country-level AI Stock Share for specific industries ---
    SPECIAL_AI_INDUSTRIES = ["C26", "J59_60", "Q86", "C28", "G46", "C31_32", "M74_75", "C29", "C27", "C30", "E36", "N80T82", "C21"]
    ai_country_sheets = {}

    for industry in SPECIAL_AI_INDUSTRIES:
        # Filter df for the industry
        df_ind = df[df["Industry Code"] == industry]

        # Add EU27 aggregate
        eu27_ind = (
            df_ind[df_ind["Country"].isin(EU27)]
                .groupby("Year", as_index=False)["AI Stock"].sum()
        )
        eu27_ind["Country"] = "EU27"

        # Exclude individual EU27 countries and include EU27
        df_ind = df_ind[~df_ind["Country"].isin(EU27)]
        df_ind = pd.concat([df_ind, eu27_ind], ignore_index=True)

        # Compute total AI Stock by year
        total_ai_per_year = df_ind.groupby("Year")["AI Stock"].sum().rename("Total_AI_Stock")
        df_ind = df_ind.merge(total_ai_per_year, on="Year", how="left")
        df_ind["AI_Stock_Share"] = df_ind["AI Stock"] / df_ind["Total_AI_Stock"]

        # Pivot to wide format (Country × Year)
        pivot_df = df_ind.pivot(index="Country", columns="Year", values="AI_Stock_Share")

        # Sort rows by 2023 descending
        if 2023 in pivot_df.columns:
            pivot_df = pivot_df.sort_values(by=2023, ascending=False)

        ai_country_sheets[industry] = pivot_df

    # --- Step 7: Country-level non-AI Stock Share for specific industries ---
    SPECIAL_NON_AI_INDUSTRIES = ["Q86", "C21", "C27", "C28", "C29"]
    non_ai_country_sheets = {}

    for industry in SPECIAL_NON_AI_INDUSTRIES:
        # Filter df for the industry
        df_ind = df[df["Industry Code"] == industry]

        # Add EU27 aggregate
        eu27_ind = (
            df_ind[df_ind["Country"].isin(EU27)]
                .groupby("Year", as_index=False)["Non AI Stock"].sum()
        )
        eu27_ind["Country"] = "EU27"

        # Exclude individual EU27 countries and include EU27
        df_ind = df_ind[~df_ind["Country"].isin(EU27)]
        df_ind = pd.concat([df_ind, eu27_ind], ignore_index=True)

        # Compute total AI Stock by year
        total_non_ai_per_year = df_ind.groupby("Year")["Non AI Stock"].sum().rename("Total_Non_AI_Stock")
        df_ind = df_ind.merge(total_non_ai_per_year, on="Year", how="left")
        df_ind["Non_AI_Stock_Share"] = df_ind["Non AI Stock"] / df_ind["Total_Non_AI_Stock"]

        # Pivot to wide format (Country × Year)
        pivot_df = df_ind.pivot(index="Country", columns="Year", values="Non_AI_Stock_Share")

        # Sort rows by 2023 descending
        if 2023 in pivot_df.columns:
            pivot_df = pivot_df.sort_values(by=2023, ascending=False)

        non_ai_country_sheets[industry] = pivot_df

    # --- Step 6: Write results to Excel ---
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        global_ai_share.to_excel(writer, sheet_name="Global_AI_Industry_Share")
        global_nonai_share.to_excel(writer, sheet_name="Global_Non_AI_Industry_Share")
        eu_ai_share.to_excel(writer, sheet_name="EU_AI_Industry_Share")
        eu_nonai_share.to_excel(writer, sheet_name="EU_Non_AI_Industry_Share")
        for industry, sheet_df in ai_country_sheets.items():
            sheet_name = f"{industry}_Country_AI_Share"
            sheet_df.to_excel(writer, sheet_name=sheet_name)
        for industry, sheet_df in non_ai_country_sheets.items():
            sheet_name = f"{industry}_Country_Non_AI_Share"
            sheet_df.to_excel(writer, sheet_name=sheet_name)

    print(f"✅ Output written to: {OUTPUT_PATH}")


# -------- MAIN EXECUTION GUARD --------
if __name__ == "__main__":
    main()
