import os
import pandas as pd
import numpy as np

# -------- CONFIGURATION --------
IO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/DPA"  # ← change this to your folder path
EXCLUDE_PREFIXES = ("AL", "ME", "MK", "RS")


def clean_io_file(file_path):
    print(f"Processing: {os.path.basename(file_path)}")

    # Read CSV (no header assumed)
    df = pd.read_csv(file_path, header=None, dtype=str)

    # Drop completely empty rows/cols
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)

    # Identify column and row labels (first row/col might be codes)
    # If all cells are numeric, there may be no headers — handle both cases
    first_row = df.iloc[0, :].astype(str).tolist()
    first_col = df.iloc[:, 0].astype(str).tolist()

    # Detect columns to remove (any starting with excluded prefixes)
    cols_to_remove = [
        i for i, val in enumerate(first_row)
        if any(val.startswith(prefix) for prefix in EXCLUDE_PREFIXES)
    ]

    # Detect rows to remove (any starting with excluded prefixes)
    rows_to_remove = [
        i for i, val in enumerate(first_col)
        if any(val.startswith(prefix) for prefix in EXCLUDE_PREFIXES)
    ]

    # Drop unwanted rows/columns
    df_cleaned = df.drop(index=rows_to_remove, columns=cols_to_remove)

    # Write cleaned version to new file
    out_path = file_path.replace(".csv", "_v2.csv")
    df_cleaned.to_csv(out_path, index=False, header=False)
    print(f"Saved cleaned file → {os.path.basename(out_path)} ({df_cleaned.shape[0]}x{df_cleaned.shape[1]})\n")


def main():
    for file in os.listdir(IO_DIR):
        if file.endswith(".csv"):
            clean_io_file(os.path.join(IO_DIR, file))


if __name__ == "__main__":
    main()
