import pandas as pd
import os

# -------- CONFIGURATION --------
INPUT_PATH = "/Users/nikhil/Downloads/OECD_STAN/OECD_STAN_data.csv"
OUTPUT_PATH = "/Users/nikhil/Downloads/OECD_STAN/OECD_NetCapitalStock_CurrentPrices.csv"
CHUNKSIZE = 100000  # adjust depending on available memory
TARGET_AREAS = ["AUS", "CAN", "JPN", "KOR", "USA"]
TARGET_INDUSTRIES = ["A", "A01", "A01_02", "A02", "A03", "B", "B05_06", "B07_08", "B09", "BTE", "C", "C10", "C10T12", "C10_11", "C11", "C12", "C13", "C13T15", "C13_14", "C14", "C15", "C16", "C16T18", "C17", "C18", "C19", "C19T23", "C20", "C20_21", "C21", "C22", "C22_23", "C23", "C24", "C24_25", "C25", "C26", "C26T28", "C26_27", "C27", "C28", "C29", "C29_30", "C30", "C31T33", "C31_32", "C33", "D", "D_E", "E", "E36", "E37T39", "F", "G", "G45", "G46", "G47", "GTI", "GTN", "GTU", "H", "H49", "H50", "H51", "H52", "H53", "I", "I55", "I56", "J", "J58", "J58T60", "J59_60", "J61", "J62", "J62_63", "J63", "K", "K64", "K65", "K66", "L", "L68A", "LTN", "M", "M69", "M69T71", "M69_70", "M70", "M71", "M72", "M73", "M73T75", "M74", "M74_75", "M75", "M_N", "N", "N77", "N78", "N79", "N80T82", "O", "OTQ", "OTU", "P", "Q", "Q86", "Q87_88", "R", "R90T92", "R93", "RTU", "S", "S94", "S95", "S96", "T", "U", "_T"]
KEEP_COLS = [
    "REF_AREA", "Reference area",
    "ACTIVITY",
    "TIME_PERIOD", "OBS_VALUE"
]
START_YEAR = 2010
END_YEAR = 2023


def filter_net_capital_stock(input_path: str, output_path: str, chunksize: int = 100000):
    """
    Reads a large OECD STAN CSV in chunks, filters rows with MEASURE == 'Net capital stock',
    and saves the filtered data into a new CSV file.
    """
    # Track whether header has been written to output
    write_header = True
    total_rows = 0
    filtered_rows = 0

    for chunk in pd.read_csv(input_path, chunksize=chunksize, dtype=str):
        total_rows += len(chunk)
        chunk["TIME_PERIOD_NUM"] = pd.to_numeric(chunk["TIME_PERIOD"], errors="coerce")
        filtered_chunk = chunk[
            (chunk["Measure"] == "Net capital stock") &
            (chunk["Price base"] == "Current replacement cost") &
            (chunk["REF_AREA"].isin(TARGET_AREAS)) &
            (chunk["TIME_PERIOD_NUM"].between(START_YEAR, END_YEAR)) &
            (chunk["ACTIVITY"]).isin(TARGET_INDUSTRIES)
        ][KEEP_COLS]
        filtered_rows += len(filtered_chunk)

        if not filtered_chunk.empty:
            filtered_chunk.to_csv(output_path, mode='a', index=False, header=write_header)
            write_header = False  # write header only once

    print(f"✅ Done. Total rows processed: {total_rows:,}")
    print(f"📊 Rows with 'Net capital stock': {filtered_rows:,}")
    print(f"💾 Filtered data saved to: {output_path}")


if __name__ == "__main__":
    if not os.path.exists(INPUT_PATH):
        print(f"Error: Input file not found at {INPUT_PATH}")
    else:
        filter_net_capital_stock(INPUT_PATH, OUTPUT_PATH, CHUNKSIZE)
