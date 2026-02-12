import pandas as pd
import os

# -------- CONFIGURATION --------
#INPUT_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/All_Patents/PCT_All_Patents.csv"
INPUT_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_Patents/PCT_AI_Patents.csv"


def calc_ipc4_weight(ipc_str):
    if not isinstance(ipc_str, str) or not ipc_str.strip():
        return 1.0
    codes = [c.strip() for c in ipc_str.split(";") if c.strip()]
    return 1 / len(set(codes)) if len(codes) > 0 else 1.0


def main():
    print("Loading data...")
    df = pd.read_csv(INPUT_FILE, dtype=str)  # Read all as str to avoid dtype issues

    # Count how many times each Application Number appears
    print("Counting patent frequencies...")
    app_counts = df["Application Number"].value_counts().to_dict()

    # Add Patent Weight column (1 / count)
    df["Patent Weight"] = df["Application Number"].apply(
        lambda x: 1 / app_counts.get(x, 1) if pd.notna(x) and x != "N/A" else 1
    )

    # Add IPC4 Weight column (1 / number of unique IPC4 codes)
    print("Calculating IPC4 weights...")
    df["IPC4 Weight"] = df["Unique IPC4"].apply(calc_ipc4_weight)

    # Save to same CSV file
    temp_file = INPUT_FILE + ".tmp"
    print(f"Saving updated data to '{INPUT_FILE}'...")
    df.to_csv(temp_file, index=False)
    os.replace(temp_file, INPUT_FILE)

    print("\n✅ Done! File updated in place.")
    print(f"Columns added: Patent Weight, IPC4 Weight")
    print(f"Total rows processed: {len(df)}")


if __name__ == "__main__":
    main()
