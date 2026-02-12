import os
import pandas as pd
from datetime import datetime

# -------- CONFIGURATION --------
BASE_DIR = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_Patents"
SEGMENTS = ["Segment1", "Segment2"]
TEMP_CSV = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_Patents/PCT_AI_Patents.csv"

# Initialize
segment1_app_numbers = set()
segment2_app_numbers = set()

# Initialize CSV with header if not present
if not os.path.exists(TEMP_CSV):
    header = [
        "Applicant Residence Country",
        "Application Id",
        "Application Number",
        "Application Date",
        "Application Year",
        "Title",
        "IPC",
        "Unique IPC4"
    ]
    pd.DataFrame(columns=header).to_csv(TEMP_CSV, index=False)


def extract_ipc4_series(ipc_series):
    """Vectorized IPC4 extraction for pandas Series."""
    def extract_codes(ipc_str):
        if pd.isna(ipc_str):
            return ""
        parts = [p.strip() for p in str(ipc_str).split(";") if p.strip()]
        ipc4 = {p.split("/")[0][:4] for p in parts if len(p.split("/")[0]) >= 4}
        return ";".join(sorted(ipc4))
    return ipc_series.apply(extract_codes)


def process_segment(segment_name):
    """Process Segment1 and Segment2 folders efficiently."""
    global segment1_app_numbers, segment2_app_numbers
    segment_path = os.path.join(BASE_DIR, segment_name)
    if not os.path.exists(segment_path):
        print(f"⚠️ Segment folder not found: {segment_path}")
        return

    for country_code in os.listdir(segment_path):
        folder_path = os.path.join(segment_path, country_code)
        if not os.path.isdir(folder_path):
            continue

        print(f"Processing {segment_name} - {country_code}...")

        country_entries = []

        for filename in os.listdir(folder_path):
            if not filename.lower().endswith(('.xlsx', '.xls')):
                continue

            file_path = os.path.join(folder_path, filename)
            try:
                df = pd.read_excel(file_path, skiprows=5)
                df.dropna(how='all', inplace=True)

                if "Application Date" not in df.columns or "Application Number" not in df.columns:
                    continue

                # Convert and filter dates
                df["Application Date"] = pd.to_datetime(df["Application Date"], errors="coerce", dayfirst=True)
                df = df[
                    (df["Application Date"] >= datetime(2000, 1, 1)) &
                    (df["Application Date"] <= datetime(2023, 12, 31))
                ]

                if df.empty:
                    continue

                # Remove duplicates (Segment2 exclusion logic)
                app_numbers = df["Application Number"].astype(str).str.strip()
                if segment_name == "Segment1":
                    segment1_app_numbers.update(app_numbers)
                else:
                    segment2_app_numbers.update(app_numbers)
                    mask = ~app_numbers.isin(segment1_app_numbers)
                    df = df[mask]

                if df.empty:
                    continue

                # Add computed columns
                df["Applicant Residence Country"] = country_code
                df["Application Date"] = df["Application Date"].dt.strftime("%d.%m.%Y")
                df["Application Year"] = pd.to_datetime(df["Application Date"], format="%d.%m.%Y", errors="coerce").dt.year
                df["Unique IPC4"] = extract_ipc4_series(df.get("I P C", ""))

                # Align column names
                df.rename(columns={"I P C": "IPC"}, inplace=True)

                df = df[[
                    "Applicant Residence Country",
                    "Application Id",
                    "Application Number",
                    "Application Date",
                    "Application Year",
                    "Title",
                    "IPC",
                    "Unique IPC4"
                ]]

                country_entries.append(df)

            except Exception as e:
                print(f"[ERROR] Reading {file_path}: {e}")

        # Append once per country (minimize I/O)
        if country_entries:
            combined = pd.concat(country_entries, ignore_index=True)
            combined.to_csv(TEMP_CSV, mode='a', header=False, index=False)
            print(f"[INFO] Appended {len(combined)} rows for {segment_name} - {country_code}")


def main():
    print("\n[STEP 1] Processing Segment1 (base dataset)...")
    process_segment("Segment1")

    print("\n[STEP 2] Processing Segment2 (deduplicated union)...")
    process_segment("Segment2")

    print(f"\n✅ AI Patent consolidation complete!")
    print(f"Unique Segment 1: {len(segment1_app_numbers)}, Unique Segment 2: {len(segment2_app_numbers)}, Both: {len(segment1_app_numbers & segment2_app_numbers)}")


if __name__ == "__main__":
    main()
