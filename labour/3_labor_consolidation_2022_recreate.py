import numpy as np
import pandas as pd
import time

# === CONFIGURATION ===
FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/"
EUROSTAT_DIR = "/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/"
OECD_DIR = "/Users/nikhil/Documents/Thesis/L-M_Compilation/OECD/"
OUTPUT_FILE = "/Users/nikhil/Documents/Thesis/L-M_Compilation/EMP_figaro2022_recreatev1.xlsx"

# Scalars
FIGARO_INDUSTRIES = 64  # sectors
FIGARO_COUNTRIES = 46  # regions (countries)
FIGARO_DEMAND_CATEGORIES = 5  # final demand categories
FIGARO_TIME_RANGE = 11  # years (2010–2020)
W = []


def load_figaro_data():
    years = list(range(2010, 2021))
    for year in years:
        file_path = FIGARO_DIR + f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv"

        # Read CSV
        # FIGARO files have metadata columns (industry codes, country codes, etc.)
        # We only need numeric data, so we skip the first row/col if they contain text.
        df = pd.read_csv(file_path, header=None)

        # Try to automatically detect and drop non-numeric rows/columns
        df_numeric = df.apply(pd.to_numeric, errors='coerce')  # convert to numeric; non-numeric → NaN
        df_numeric = df_numeric.dropna(how='all', axis=0).dropna(how='all', axis=1)  # remove empty rows/cols

        # Convert to NumPy matrix
        W.append(df_numeric.to_numpy())
    print(f"Loaded {len(W)} FIGARO matrices with shapes:", [w.shape for w in W])


def impute_country(emp_dict, vshare_dict, country_idx, country_code):
    """
    Reads adjusted employment data from existing Excel file for a given country.
    Mirrors MATLAB's logic:
      1. Writes Vshare and EMP to Excel (for reference/imputation)
      2. Pauses (not needed here since we already have the adjusted files)
      3. Reads adjusted data from '*_emp_ADJ' sheet
    """
    file_path = EUROSTAT_DIR + f"{country_code}.xlsx"

    # Optional: Save current data (mimics MATLAB’s xlswrite for transparency)
    # pd.DataFrame(vshare_dict[country_idx]).to_excel(
    #     file_path, sheet_name=f"{country_code}_Xshare", index=False, header=False, startrow=1, startcol=1
    # )
    # pd.DataFrame(emp_dict[country_idx]).to_excel(
    #     file_path, sheet_name=f"{country_code}_emp", index=False, header=False, startrow=1, startcol=1
    # )

    # MATLAB used pause(4–5); we'll just wait a bit for I/O sync
    # time.sleep(2)

    # Now read the adjusted employment data (which you already have)
    emp_adj = pd.read_excel(
        file_path,
        sheet_name=f"{country_code}_emp_ADJ",
        usecols="B:L",  # corresponds to columns 2–12 in Excel (same as MATLAB)
        skiprows=1,  # skip the first row (header)
        nrows=64,  # 64 industries
        header=None
    ).to_numpy()

    return emp_adj


def main():
    # -------------------------------------
    # 1. Load FIGARO data (previously saved)
    # -------------------------------------
    load_figaro_data()

    # -------------------------------------
    # 2. Load order of countries
    # -------------------------------------
    order = pd.read_excel(
        EUROSTAT_DIR + "order_countries.xlsx",
        sheet_name="order_countries",
        usecols="B:C",
        skiprows=1,  # skip header (starts from row 2)
        nrows=46,  # read rows 2–47 inclusive
        header=None
    ).to_numpy()

    # -------------------------------------
    # 3. Compute Value Added (VA) shares
    # -------------------------------------
    v = np.zeros((FIGARO_INDUSTRIES * FIGARO_COUNTRIES, FIGARO_TIME_RANGE))

    # Each W[i] contains a large matrix. Last 6 rows (end-5:end) = value-added components
    for i in range(FIGARO_TIME_RANGE):
        v[:, i] = np.sum(W[i][-6:, :FIGARO_INDUSTRIES * FIGARO_COUNTRIES], axis=0)
    print(f"--- v shape after stacking Figaro IO data for demand columns --- {np.shape(v)}")

    # Split by country
    V = []
    Vshare = []
    for i in range(FIGARO_COUNTRIES):
        a = int(order[i, 1])  # Figaro index
        print(f"Creating value-added shares for eurostat index: {i+1}, figaro index: {a}")
        country_V = v[(a - 1) * FIGARO_INDUSTRIES: a * FIGARO_INDUSTRIES, :]
        V.append(country_V)
        # Normalize to share
        Vshare.append(country_V / np.sum(country_V, axis=0, keepdims=True))

    Vshare_shapes = [arr.shape for arr in Vshare]
    print("\n--- Vshare array shapes summary ---")
    for i, s in enumerate(Vshare_shapes):
        print(f"{i:02d} | shape={s}")
    print("--------------------------------------")
    # DEBUG - Vshare for countries
    # with pd.ExcelWriter("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/Vshare_Recreate.xlsx", engine="openpyxl") as writer:
    #     for i, arr in enumerate(Vshare):
    #         df = pd.DataFrame(arr)
    #         df.to_excel(writer, sheet_name=f"Sheet {i + 1}", index=False, startrow=1, startcol=1)
    #         print(f"✅ Wrote Sheet {i + 1} | shape={df.shape}")

    # -------------------------------------
    # 4. Read EUROSTAT employment data (11 sheets)
    # -------------------------------------
    eurostat = []
    for i in range(FIGARO_TIME_RANGE):
        df = pd.read_excel(EUROSTAT_DIR + "data_eurostat.xlsx",
                           sheet_name=f"Sheet {i + 1}",
                           usecols="C:AF",
                           skiprows=12,
                           nrows=64,
                           header=None)
        df = df.replace(':', np.nan)
        eurostat.append(df.to_numpy().reshape(-1, 1, order='F'))  # reshape to vector

    for i, arr in enumerate(eurostat):
        if isinstance(arr, np.ndarray):
            try:
                arr_numeric = arr.astype(float)
                print(f"[{i:02d}] loaded: shape={arr.shape}, "
                      f"min={np.nanmin(arr_numeric):.2f}, max={np.nanmax(arr_numeric):.2f}")
            except Exception as e:
                print(
                    f"[{i:02d}] loaded: shape={arr.shape} ❌ Non-numeric values detected ({type(arr[0, 0])})")
                print(f"  Example values: {arr[0, :5]}")
                print(f"  Error: {e}")
        else:
            print(f"[{i:02d}] is not a NumPy array (type={type(arr)})")

    shapes = [arr.shape for arr in eurostat]
    print("\n--- Eurostat array shapes summary ---")
    for i, s in enumerate(shapes):
        print(f"{i:02d} | shape={s}")
    print("--------------------------------------")

    # Check for unique row counts
    unique_row_counts = set(s[0] for s in shapes)
    print(f"Unique row counts found: {unique_row_counts}")

    # Combine across years into a big matrix
    emp = np.hstack(eurostat)
    print(f"--- emp shape after stacking eurostat for all years --- {np.shape(emp)}")

    # Split by 30 Eurostat countries
    EMP = [emp[i * FIGARO_INDUSTRIES:(i + 1) * FIGARO_INDUSTRIES, :] for i in range(30)]
    # Debug
    EMP_Shapes = [arr.shape for arr in EMP]
    print("\n--- EMP array shapes summary ---")
    for i, s in enumerate(EMP_Shapes):
        print(f"{i:02d} | shape={s}")
    print("--------------------------------------")
    # write to file
    # with pd.ExcelWriter("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/EMP_Recreate.xlsx", engine="openpyxl") as writer:
    #     for i, arr in enumerate(EMP):
    #         df = pd.DataFrame(arr)
    #         df.to_excel(writer, sheet_name=f"Sheet {i + 1}", index=False, startrow=1, startcol=1)
    #         print(f"✅ Wrote Sheet {i + 1} | shape={df.shape}")
    #
    # print("Saving LU VShare")
    # lu_vshare_df = pd.DataFrame(Vshare[15])
    # lu_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/LU_Vshare_Recreate.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving LU EMP")
    # lu_emp_df = pd.DataFrame(EMP[15])
    # lu_emp_df.to_excel("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/LU_EMP_Recreate.xlsx",
    #                       sheet_name="EMP", index=False, startrow=1, startcol=1)

    # -------------------------------------
    # 5. Read OECD-TiM data
    # -------------------------------------
    tim = pd.read_excel(OECD_DIR + "TiM_2021.xlsx",
                        sheet_name="OECD.Stat export",
                        usecols="W:AE",
                        skiprows=7,
                        nrows=1050,
                        header=None)
    tim = tim.replace(':', np.nan).to_numpy()
    print("\n--- tim shape ---")
    print(np.shape(tim))

    aggTiMto64 = pd.read_excel(OECD_DIR + "TiM_2021.xlsx",
                               sheet_name="agg_TiM_to64",
                               usecols="S:CD",
                               skiprows=2,
                               nrows=70,
                               header=None)
    aggTiMto64 = aggTiMto64.replace(':', np.nan).to_numpy()
    print("\n--- aggTiMto64 shape ---")
    print(np.shape(aggTiMto64))

    growth = pd.read_excel(OECD_DIR + "TiM_2021.xlsx",
                           sheet_name="Growth",
                           usecols="D:E",
                           skiprows=1,
                           nrows=15,
                           header=None)
    growth = growth.replace(':', np.nan).to_numpy()
    print("\n--- growth shape ---")
    print(np.shape(growth))

    # Fill 2019–2020 with 2018 values
    # Add 2019 and 2020 columns by duplicating 2018
    tim_2019 = tim[:, [8]]  # column index 8 = 2018
    tim_2020 = tim[:, [8]]
    tim = np.hstack([tim, tim_2019, tim_2020])
    print(f"--- tim shape after adding 2019/2020 --- {np.shape(tim)}")

    # Split OECD-TiM data into 15-country chunks (each 70x11 matrix)
    aux_TiM = [tim[i * 70:(i + 1) * 70, :] for i in range(15)]
    # DEBUG: print
    aux_TiM_Shapes = [arr.shape for arr in aux_TiM]
    print("\n--- aux_TiM array shapes summary ---")
    for i, s in enumerate(aux_TiM_Shapes):
        print(f"{i:02d} | shape={s}")
    print("--------------------------------------") # 15 x (70 x 11)

    # DEBUG: write to file
    # print("writing aux_tim to excel")
    # with pd.ExcelWriter("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/AUX_TIM_Recreate.xlsx", engine="openpyxl") as writer:
    #     for i, arr in enumerate(aux_TiM):
    #         df = pd.DataFrame(arr)
    #         df.to_excel(writer, sheet_name=f"Sheet {i + 1}", index=False, startrow=1, startcol=1)
    #         print(f"✅ Wrote Sheet {i + 1} | shape={df.shape}")

    # Map OECD countries (31–45)
    EMP_TiM = [None] * 46
    EMP_TiM[30] = aux_TiM[5]  # Turkey
    EMP_TiM[31] = aux_TiM[6]  # USA
    EMP_TiM[32] = aux_TiM[1]  # Canada
    EMP_TiM[33] = aux_TiM[4]  # Mexico
    EMP_TiM[34] = aux_TiM[7]  # Argentina
    EMP_TiM[35] = aux_TiM[8]  # Brazil
    EMP_TiM[36] = aux_TiM[12]  # Russia
    EMP_TiM[37] = aux_TiM[10]  # India
    EMP_TiM[38] = aux_TiM[9]  # China
    EMP_TiM[39] = aux_TiM[14]  # South Africa
    EMP_TiM[40] = aux_TiM[2]  # Japan
    EMP_TiM[41] = aux_TiM[3]  # Korea
    EMP_TiM[42] = aux_TiM[11]  # Indonesia
    EMP_TiM[43] = aux_TiM[0]  # Australia
    EMP_TiM[44] = aux_TiM[13]  # Saudi Arabia

    # -------------------------------------
    # 6. Imputations for Eurostat countries
    # -------------------------------------

    # 16) Luxembourg - LU
    EMP[15] = impute_country(EMP, Vshare, 15, "LU")

    # 18) Malta - MT
    EMP[17] = impute_country(EMP, Vshare, 17, "MT")

    # 28) Norway - NO
    EMP[27] = impute_country(EMP, Vshare, 27, "NO")

    # 29) Switzerland - CH
    EMP[28] = impute_country(EMP, Vshare, 28, "CH")

    # 30) Great Britain - GB (handled separately below)
    EMP[29][:, 10] = 0.998033798 * EMP[29][:, 9]  # Impute 2020 from 2019

    # -------------------------------------
    # 7. TiM 45→64 industry disaggregation
    # -------------------------------------
    # with pd.ExcelWriter("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/EMP_TiM_Recreate.xlsx",
    #                     engine="openpyxl") as writer:
    for i in range(30, 45):
        EMP_TiM[i] = aggTiMto64.T @ EMP_TiM[i]  # Expand to 64 industries
        # DEBUG
        # print("writing EMP_TiM_Aggregated to excel")
        # df = pd.DataFrame(EMP_TiM[i])
        # df.to_excel(writer, sheet_name=f"Sheet {i-29}", index=False, startrow=1, startcol=1)
        # print(f"✅ Wrote Sheet {i-29} | shape={df.shape}")

    # with pd.ExcelWriter("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/EMP_TiM_normalize_Recreate.xlsx",
    #                     engine="openpyxl") as writer:
    for i in range(30, 45):
        print(f"--- Processing country index {i} ---")
        print(f"Vshare Shape: {np.shape(Vshare[i])}")
        Vshare_TiM = np.ones((64, 11))

        V_i = np.array(Vshare[i])  # ensure numpy array

        def normalize_rows(rng):
            rows = np.arange(rng.start, rng.stop)  # e.g., 0,1 or 7,8
            print(f"Normalizing rows from {rng.start + 1}:{rng.stop} -> {rows} for V_i")
            block = V_i[rows, :]
            block_sum = np.sum(block, axis=0, keepdims=True)
            # Avoid divide-by-zero
            block_sum[block_sum == 0] = np.nan
            Vshare_TiM[rows, :] = block / block_sum

        # Apply the same groups as in MATLAB (remember Python is 0-based)
        normalize_rows(slice(0, 2))  # 1–2
        normalize_rows(slice(7, 9))  # 8–9
        normalize_rows(slice(21, 23))  # 22–23
        normalize_rows(slice(24, 26))  # 25–26
        normalize_rows(slice(27, 30))  # 28–30
        normalize_rows(slice(36, 38))  # 37–38
        normalize_rows(slice(40, 43))  # 41–43
        normalize_rows(slice(44, 49))  # 45–49
        normalize_rows(slice(49, 53))  # 50–53
        normalize_rows(slice(55, 57))  # 56–57
        normalize_rows(slice(57, 59))  # 58–59
        normalize_rows(slice(59, 62))  # 60–62
        normalize_rows(slice(62, 64))  # 63–64
        # Apply element-wise multiplication
        EMP_TiM[i] = EMP_TiM[i] * Vshare_TiM
        # DEBUG
        # print("writing EMP_TiM_Normalized to excel")
        # df = pd.DataFrame(EMP_TiM[i])
        # df.to_excel(writer, sheet_name=f"Sheet {i-29}", index=False, startrow=1, startcol=1)
        # print(f"✅ Wrote Sheet {i-29} | shape={df.shape}")

    # Apply growth factors for 2019 & 2020
    for i in range(30, 45):
        EMP_TiM[i][:, 9] *= growth[i - 31, 0]
        EMP_TiM[i][:, 10] *= growth[i - 31, 1]

    # -------------------------------------
    # 8. Assign TiM countries to EMP list
    # -------------------------------------
    for i in range(30, 45):
        EMP.append(EMP_TiM[i])

    # 46th region = Rest of World (zeros)
    EMP.append(np.zeros((64, 11)))

    # -------------------------------------
    # 9. Replace NaN with zeros
    # -------------------------------------
    EMP = [np.nan_to_num(e) for e in EMP]

    # -------------------------------------
    # 10. Restore Figaro order and export
    # -------------------------------------
    EMP_figaro = np.zeros((FIGARO_INDUSTRIES * FIGARO_COUNTRIES, FIGARO_TIME_RANGE))
    for i in range(FIGARO_COUNTRIES):
        a = int(order[i, 1])
        EMP_figaro[(a - 1) * FIGARO_INDUSTRIES:a * FIGARO_INDUSTRIES, :] = EMP[i]

    # Save to Excel
    final_df = pd.DataFrame(EMP_figaro)
    final_df.to_excel(OUTPUT_FILE, sheet_name="Final", index=False, startrow=1, startcol=1)


if __name__ == "__main__":
    main()

