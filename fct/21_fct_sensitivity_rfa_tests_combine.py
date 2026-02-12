import pandas as pd
import numpy as np
from pathlib import Path

# ======================== CONFIGURATION ========================
BASE_SENSITIVITY_DIR = "/Users/nikhil/Documents/Thesis/FCT/Sensitivity"
YEAR = "2021"

INDUSTRY_CODES = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]

INDUSTRY_NAMES = {
    "A01": "Agriculture", "A02": "Forestry", "A03": "Fishing",
    "B": "Mining", "C10T12": "Food", "C13T15": "Textiles",
    "C16": "Wood", "C17": "Paper", "C18": "Printing",
    "C19": "Petroleum", "C20": "Chemicals", "C21": "Pharmaceuticals",
    "C22": "Rubber/Plastics", "C23": "Non-Metallic Minerals", "C24": "Basic Metals",
    "C25": "Fabricated Metals", "C26": "Electronics", "C27": "Electrical Equipment",
    "C28": "Machinery", "C29": "Motor Vehicles", "C30": "Other Transport",
    "C31_32": "Furniture", "C33": "Repair", "D35": "Electricity",
    "E36": "Water", "E37T39": "Waste", "F": "Construction",
    "G45": "Motor Vehicle Trade", "G46": "Wholesale", "G47": "Retail",
    "H49": "Land Transport", "H50": "Water Transport", "H51": "Air Transport",
    "H52": "Warehousing", "H53": "Postal", "I": "Accommodation",
    "J58": "Publishing", "J59_60": "Media", "J61": "Telecommunications",
    "J62_63": "IT Services", "K64": "Financial Services", "K65": "Insurance",
    "K66": "Financial Support", "L": "Real Estate", "M69_70": "Legal/Accounting",
    "M71": "Architecture", "M72": "R&D", "M73": "Advertising",
    "M74_75": "Professional Services", "N77": "Rental", "N78": "Employment",
    "N79": "Travel Agency", "N80T82": "Security", "O84": "Government",
    "P85": "Education", "Q86": "Health", "Q87_88": "Social Work",
    "R90T92": "Arts", "R93": "Sports", "S94": "Membership Orgs",
    "S95": "Repair Services", "S96": "Personal Services", "T": "Households",
    "U": "Extraterritorial"
}

TARGET_COUNTRIES = {
    "CN": "China RFA",
    "US": "US RFA",
    "EU27": "EU RFA"
}

OUTPUT_FILE = Path(BASE_SENSITIVITY_DIR) / "RFA_2021_Summary.xlsx"


# ======================== HELPER ========================
def format_rfa(value, flag):
    if pd.isna(value):
        return np.nan
    return f"{value:.3f} ({flag})"


if __name__ == "__main__":
    print("🚀 Starting RFA 2021 aggregation across omitted industries...\n")

    try:
        rows = []

        for industry_code in INDUSTRY_CODES:
            industry_dir = Path(BASE_SENSITIVITY_DIR) / industry_code
            excel_path = industry_dir / "rfa_sensitivity_national.xlsx"

            if not excel_path.exists():
                print(f"⚠️ Missing file for {industry_code}, skipping.")
                continue

            try:
                df_2021 = pd.read_excel(
                    excel_path,
                    sheet_name=YEAR,
                    index_col="Country"
                )
            except Exception as e:
                print(f"⚠️ Could not read 2021 sheet for {industry_code}: {e}")
                continue

            row = {
                "Industry_Code": industry_code,  # ← used only for sorting
                "Omitted Industry": f"{INDUSTRY_NAMES.get(industry_code, 'Unknown')} ({industry_code})"
            }

            for country_code, col_name in TARGET_COUNTRIES.items():
                if country_code not in df_2021.index:
                    row[col_name] = np.nan
                    continue

                leamer_val = df_2021.loc[country_code, "Leamer_AI_By_Non_AI"]
                leamer_flag = df_2021.loc[
                    country_code,
                    "Leamer_Relative_AI_By_Non_AI_Factor_Abundance"
                ]

                row[col_name] = format_rfa(leamer_val, leamer_flag)

            rows.append(row)

        df_final = pd.DataFrame(rows)

        # ✅ Sort by industry code, then drop helper column
        df_final.sort_values("Industry_Code", inplace=True)
        df_final.drop(columns="Industry_Code", inplace=True)

        df_final.to_excel(OUTPUT_FILE, index=False)

        print("\n" + "=" * 60)
        print("✅ RFA 2021 SUMMARY SUCCESSFULLY GENERATED")
        print(f"📁 Output file: {OUTPUT_FILE}")
        print("=" * 60)

    except Exception as e:
        print("❌ Fatal error during RFA aggregation")
        raise
