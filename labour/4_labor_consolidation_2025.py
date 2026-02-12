import numpy as np
import pandas as pd
import time

# === CONFIGURATION ===
FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/"
EUROSTAT_DIR = "/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/"
OECD_DIR = "/Users/nikhil/Documents/Thesis/Labour/OECD/"
OUTPUT_FILE = "/Users/nikhil/Documents/Thesis/Labour/EMP_figaro2025.xlsx"

# Scalars
FIGARO_INDUSTRIES = 64  # sectors
FIGARO_COUNTRIES = 46  # regions (countries)
FIGARO_TIME_RANGE = 14  # years (2010–2023)
W = []


def load_figaro_data():
    years = list(range(2010, 2024))
    for year in years:
        # read from v2 as it is updated to remove the 4 extra country codes: AL, ME, MK, RS
        file_path = FIGARO_DIR + f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv"

        # Read CSV
        # FIGARO files have metadata columns (industry codes, country codes, etc.)
        # We only need numeric data, so we skip the first row/col
        df = pd.read_csv(file_path, header=None)

        # Try to automatically detect and drop non-numeric rows/columns
        df_numeric = df.apply(pd.to_numeric, errors='coerce')  # convert to numeric; non-numeric → NaN
        df_numeric = df_numeric.dropna(how='all', axis=0).dropna(how='all', axis=1)  # remove empty rows/cols

        # Convert to NumPy matrix
        W.append(df_numeric.to_numpy())
    print(f"Loaded {len(W)} FIGARO matrices with shapes:", [w.shape for w in W])


def impute_country(country_code):
    """
    Reads adjusted data from '*_emp_ADJ' sheet for EUROSTAT countries with missing data
    """
    file_path = EUROSTAT_DIR + f"{country_code}_2025.xlsx"

    # Now read the adjusted employment data (which you already have)
    emp_adj = pd.read_excel(
        file_path,
        sheet_name=f"{country_code}_emp_ADJ",
        usecols="B:O",  # corresponds to columns 2–12 in Excel (same as MATLAB)
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
        EUROSTAT_DIR + "order_countries_2025.xlsx",
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
        df = pd.read_excel(EUROSTAT_DIR + "data_eurostat_2025.xlsx",
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

    # TO BE RUN FIRST TO HELP GENERATE emp_ADJ in EUROSTAT COUNTRIES WITH MISSING DATA
    # print("Saving LT VShare")
    # lt_vshare_df = pd.DataFrame(Vshare[14])
    # lt_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/LT_2025_Vshare.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving LT EMP")
    # lt_emp_df = pd.DataFrame(EMP[14])
    # lt_emp_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/LT_2025_EMP.xlsx",
    #                    sheet_name="EMP", index=False, startrow=1, startcol=1)
    #
    # print("Saving LU VShare")
    # lu_vshare_df = pd.DataFrame(Vshare[15])
    # lu_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/LU_2025_Vshare.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving LU EMP")
    # lu_emp_df = pd.DataFrame(EMP[15])
    # lu_emp_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/LU_2025_EMP.xlsx",
    #                       sheet_name="EMP", index=False, startrow=1, startcol=1)
    #
    # print("Saving MT VShare")
    # mt_vshare_df = pd.DataFrame(Vshare[17])
    # mt_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/MT_2025_Vshare.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving MT EMP")
    # mt_emp_df = pd.DataFrame(EMP[17])
    # mt_emp_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/MT_2025_EMP.xlsx",
    #                    sheet_name="EMP", index=False, startrow=1, startcol=1)
    #
    # print("Saving NO VShare")
    # no_vshare_df = pd.DataFrame(Vshare[27])
    # no_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/NO_2025_Vshare.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving NO EMP")
    # no_emp_df = pd.DataFrame(EMP[27])
    # no_emp_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/NO_2025_EMP.xlsx",
    #                    sheet_name="EMP", index=False, startrow=1, startcol=1)
    #
    # print("Saving RO VShare")
    # ro_vshare_df = pd.DataFrame(Vshare[22])
    # ro_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/RO_2025_Vshare.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving RO EMP")
    # ro_emp_df = pd.DataFrame(EMP[22])
    # ro_emp_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/RO_2025_EMP.xlsx",
    #                    sheet_name="EMP", index=False, startrow=1, startcol=1)
    #
    # print("Saving CH VShare")
    # ch_vshare_df = pd.DataFrame(Vshare[28])
    # ch_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/CH_2025_Vshare.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving CH EMP")
    # ch_emp_df = pd.DataFrame(EMP[28])
    # ch_emp_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/CH_2025_EMP.xlsx",
    #                    sheet_name="EMP", index=False, startrow=1, startcol=1)
    #
    # print("Saving SE VShare")
    # se_vshare_df = pd.DataFrame(Vshare[26])
    # se_vshare_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/SE_2025_Vshare.xlsx",
    #                       sheet_name="Vshare", index=False, startrow=1, startcol=1)
    # print("Saving SE EMP")
    # se_emp_df = pd.DataFrame(EMP[26])
    # se_emp_df.to_excel("/Users/nikhil/Documents/Thesis/Labour/EUROSTAT/SE_2025_EMP.xlsx",
    #                    sheet_name="EMP", index=False, startrow=1, startcol=1)

    # -------------------------------------
    # 5. Read OECD-TiM data
    # -------------------------------------
    tim = pd.read_excel(OECD_DIR + "TiM_2020.xlsx",
                        sheet_name="OECD.Stat_export",
                        usecols="D:N",
                        skiprows=1,
                        nrows=1050,
                        header=None)
    tim = tim.replace(':', np.nan).to_numpy()
    print("\n--- tim shape ---")
    print(np.shape(tim))

    aggTiMto64 = pd.read_excel(OECD_DIR + "TiM_2020.xlsx",
                               sheet_name="agg_TiM_to64",
                               usecols="O:BZ",
                               skiprows=2,
                               nrows=70,
                               header=None)
    aggTiMto64 = aggTiMto64.replace(':', np.nan).to_numpy()
    print("\n--- aggTiMto64 shape ---")
    print(np.shape(aggTiMto64))

    growth = pd.read_excel(OECD_DIR + "TiM_2020.xlsx",
                           sheet_name="Growth",
                           usecols="D:F",
                           skiprows=1,
                           nrows=15,
                           header=None)
    growth = growth.replace(':', np.nan).to_numpy()
    print("\n--- growth shape ---")
    print(np.shape(growth))

    # Fill 2021–2023 with 2020 values
    # Add 2019 and 2020 columns by duplicating 2020
    tim_2021 = tim[:, [10]]  # column index 10 = 2020
    tim_2022 = tim[:, [10]]
    tim_2023 = tim[:, [10]]
    tim = np.hstack([tim, tim_2021, tim_2022, tim_2023])
    print(f"--- tim shape after adding 2021-2023 --- {np.shape(tim)}")

    # Split OECD-TiM data into 15-country chunks (each 70x11 matrix)
    aux_TiM = [tim[i * 70:(i + 1) * 70, :] for i in range(15)]
    # DEBUG: print
    aux_TiM_Shapes = [arr.shape for arr in aux_TiM]
    print("\n--- aux_TiM array shapes summary ---")
    for i, s in enumerate(aux_TiM_Shapes):
        print(f"{i:02d} | shape={s}")
    print("--------------------------------------") # 15 x (70 x 14)

    # DEBUG: write to file
    # print("writing aux_tim to excel")
    # with pd.ExcelWriter("/Users/nikhil/Documents/Thesis/L-M_Compilation/EUROSTAT/AUX_TIM_Recreate.xlsx", engine="openpyxl") as writer:
    #     for i, arr in enumerate(aux_TiM):
    #         df = pd.DataFrame(arr)
    #         df.to_excel(writer, sheet_name=f"Sheet {i + 1}", index=False, startrow=1, startcol=1)
    #         print(f"✅ Wrote Sheet {i + 1} | shape={df.shape}")

    # Map OECD countries (31–45)
    EMP_TiM = [None] * 46
    EMP_TiM[30] = aux_TiM[12]  # Turkey
    EMP_TiM[31] = aux_TiM[13]  # USA
    EMP_TiM[32] = aux_TiM[3]  # Canada
    EMP_TiM[33] = aux_TiM[9]  # Mexico
    EMP_TiM[34] = aux_TiM[0]  # Argentina
    EMP_TiM[35] = aux_TiM[2]  # Brazil
    EMP_TiM[36] = aux_TiM[10]  # Russia
    EMP_TiM[37] = aux_TiM[6]  # India
    EMP_TiM[38] = aux_TiM[4]  # China
    EMP_TiM[39] = aux_TiM[14]  # South Africa
    EMP_TiM[40] = aux_TiM[7]  # Japan
    EMP_TiM[41] = aux_TiM[8]  # Korea
    EMP_TiM[42] = aux_TiM[5]  # Indonesia
    EMP_TiM[43] = aux_TiM[1]  # Australia
    EMP_TiM[44] = aux_TiM[11]  # Saudi Arabia

    # -------------------------------------
    # 6. Imputations for Eurostat countries
    # -------------------------------------

    # Impute EUROSTAT countries with ADJ data for missing values
    EMP[14] = impute_country("LT")
    EMP[15] = impute_country("LU")
    EMP[17] = impute_country("MT")
    EMP[27] = impute_country("NO")
    EMP[22] = impute_country("RO")
    EMP[28] = impute_country("CH")
    EMP[26] = impute_country("SE")
    # Impute data for UK from 2020-2023
    EMP[29][:, 10] = 0.998034 * EMP[29][:, 9]
    EMP[29][:, 11] = 1.000296 * EMP[29][:, 10]
    EMP[29][:, 12] = 1.010998 * EMP[29][:, 11]
    EMP[29][:, 13] = 1.010190 * EMP[29][:, 12]

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
        Vshare_TiM = np.ones((FIGARO_INDUSTRIES, FIGARO_TIME_RANGE))

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
        EMP_TiM[i][:, 11] = EMP_TiM[i][:, 11] * growth[i - 30, 0]
        EMP_TiM[i][:, 12] = EMP_TiM[i][:, 12] * growth[i - 30, 0] * growth[i - 30, 1]
        EMP_TiM[i][:, 13] = EMP_TiM[i][:, 13] * growth[i - 30, 0] * growth[i - 30, 1] * growth[i - 30, 2]

    # -------------------------------------
    # 8. Assign TiM countries to EMP list
    # -------------------------------------
    for i in range(30, 45):
        EMP.append(EMP_TiM[i])

    # 46th region = Rest of World (zeros)
    EMP.append(np.zeros((FIGARO_INDUSTRIES, FIGARO_TIME_RANGE)))

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
        print(f"Eurostat Country Position {i}, Figaro Country Position {a}")
        print(f"Shape of EMP[i]: {np.shape(EMP[i])}")
        EMP_figaro[(a - 1) * FIGARO_INDUSTRIES:a * FIGARO_INDUSTRIES, :] = EMP[i]

    # Save to Excel
    final_df = pd.DataFrame(EMP_figaro)
    final_df.to_excel(OUTPUT_FILE, sheet_name="Final", index=False, startrow=1, startcol=1)


if __name__ == "__main__":
    main()

