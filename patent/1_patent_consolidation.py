import os
import pandas as pd
from datetime import datetime

# -------- CONFIGURATION --------
BASE_DIR = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/All_Patents"
TEMP_CSV = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/All_Patents/PCT_All_Patents.csv"
BATCH_SIZE = 10000  # process per file

# Initialize CSV header once
if not os.path.exists(TEMP_CSV):
    header = ["Applicant Residence Country", "Application Id", "Application Number",
              "Application Date", "Application Year", "Title", "IPC", "Unique IPC4"]
    pd.DataFrame(columns=header).to_csv(TEMP_CSV, index=False)


def extract_ipc4_series(ipc_series):
    """Vectorized IPC4 extraction."""
    def extract_codes(ipc_str):
        if pd.isna(ipc_str):
            return ""
        parts = [p.strip() for p in str(ipc_str).split(";") if p.strip()]
        ipc4 = {p.split("/")[0][:4] for p in parts if len(p.split("/")[0]) >= 4}
        return ";".join(sorted(ipc4))
    return ipc_series.apply(extract_codes)


def process_country_folder(country_code, folder_path):
    """Process all Excel files in a country's folder."""
    all_entries = []
    seen_app_ids = set()

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.xlsx', '.xls')):
            file_path = os.path.join(folder_path, filename)
            try:
                df = pd.read_excel(file_path, skiprows=5)
                df.dropna(how='all', inplace=True)

                if "Application Date" not in df.columns:
                    print(f"[ERROR] Missing Application Date in {filename}")
                    continue

                # Parse date efficiently
                df["Application Date"] = pd.to_datetime(df["Application Date"], errors="coerce", dayfirst=True)

                # Filter date range
                mask = (df["Application Date"] >= datetime(2000, 1, 1)) & (df["Application Date"] <= datetime(2023, 12, 31))
                df = df.loc[mask]

                if df.empty:
                    continue

                # Drop duplicates based on Application Id (using seen_app_ids)
                original_count = len(df)
                df = df[~df["Application Id"].isin(seen_app_ids)]
                new_count = len(df)

                # Update seen_app_ids
                seen_app_ids.update(df["Application Id"].dropna().astype(str).tolist())
                skipped = original_count - new_count
                if skipped > 0:
                    print(f"[INFO] Skipped {skipped} duplicate Application Ids in {filename}")

                if df.empty:
                    continue

                # Add columns
                df["Applicant Residence Country"] = country_code
                df["Application Date"] = df["Application Date"].dt.strftime("%d.%m.%Y")
                df["Application Year"] = pd.to_datetime(df["Application Date"], format="%d.%m.%Y", errors="coerce").dt.year
                df["Unique IPC4"] = extract_ipc4_series(df.get("I P C", ""))

                df.rename(columns={"I P C": "IPC"}, inplace=True)

                df = df[[
                    "Applicant Residence Country", "Application Id", "Application Number",
                    "Application Date", "Application Year", "Title", "IPC", "Unique IPC4"
                ]]

                all_entries.append(df)

            except Exception as e:
                print(f"[ERROR] Reading {file_path}: {e}")

    if all_entries:
        combined = pd.concat(all_entries, ignore_index=True)
        combined.to_csv(TEMP_CSV, mode='a', header=False, index=False)
        print(f"[INFO] Appended {len(combined)} rows for {country_code}")


def main():
    for country_code in os.listdir(BASE_DIR):
        folder_path = os.path.join(BASE_DIR, country_code)
        if os.path.isdir(folder_path):
            print(f"Processing {country_code}...")
            process_country_folder(country_code, folder_path)


if __name__ == "__main__":
    main()
