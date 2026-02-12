import pandas as pd
import os
from collections import defaultdict

# ---------- CONFIG: set your file paths here ----------
#INPUT_PATENTS_CSV = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/All_Patents/PCT_All_Patents.csv"
INPUT_PATENTS_CSV = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_Patents/PCT_AI_Patents.csv"
INPUT_IPC4_ISIC_CSV = "/Users/nikhil/Documents/Thesis/Patents/Crosswalk/ipc4_nace_alp.csv"
INPUT_IPC3_ISIC_CSV = "/Users/nikhil/Documents/Thesis/Patents/Crosswalk/ipc3_nace_alp.csv"
INPUT_IPC2_ISIC_CSV = "/Users/nikhil/Documents/Thesis/Patents/Crosswalk/ipc2_nace_alp.csv"
INPUT_IPC1_ISIC_CSV = "/Users/nikhil/Documents/Thesis/Patents/Crosswalk/ipc1_nace_alp.csv"
INPUT_FIGARO_ISIC_CSV = "/Users/nikhil/Documents/Thesis/Patents/Crosswalk/figaro_nace.csv"
OUTPUT_FILE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_Patents/PCT_AI_Patents_By_Industry_Year.xlsx"
OUTPUT_INTERMEDIATE = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_Patents/PCT_AI_Patents_By_Industry_Year_Intermediate.xlsx"
# ------------------------------------------------------


def load_ipc_to_isic_map(ipc_csv_path, ipc_col_name):
    df = pd.read_csv(ipc_csv_path, dtype=str)
    # Normalize column names
    df.columns = df.columns.str.strip()
    if not {ipc_col_name, "isic_rev4_2", "probability_weight"}.issubset(set(df.columns.str.lower())):
        # Try case-insensitive mapping
        df.columns = [c.lower() for c in df.columns]
    # ensure correct columns now:
    df = df.rename(columns=lambda s: s.strip())
    # Some rows might have been read with whitespace - handle
    colmap = {c.lower(): c for c in df.columns}
    ipc_col = colmap.get(ipc_col_name, ipc_col_name)
    isic_col = colmap.get("isic_rev4_2", "isic_rev4_2")
    prob_col = colmap.get("probability_weight", "probability_weight")

    ipc_map = defaultdict(list)
    for _, r in df.iterrows():
        ipc = str(r[ipc_col]).strip()
        if ipc == "" or ipc.lower() == "nan":
            continue
        try:
            prob = float(r[prob_col])
        except Exception:
            prob = 0.0
        isic = str(r[isic_col]).strip()
        if isic == "" or isic.lower() == "nan":
            continue
        ipc_map[ipc].append((isic, prob))
    return dict(ipc_map)


def load_figaro_map(figaro_csv_path):
    df = pd.read_csv(figaro_csv_path, dtype=str)
    df.columns = df.columns.str.strip()

    # normalize column names (case-insensitive)
    colmap = {c.lower(): c for c in df.columns}
    figaro_col = colmap.get("figaro_code", list(df.columns)[0])
    isics_col = colmap.get("isic_rev4_2_codes", list(df.columns)[1])

    figaro_to_isics = {}
    isic_to_figaro = {}

    for _, r in df.iterrows():
        figaro = str(r[figaro_col]).strip()
        isics_cell = str(r[isics_col]).strip()

        if not isics_cell or isics_cell.lower() == "nan":
            isics = []
        else:
            # split on semicolon (the new format)
            isics = [s.strip() for s in isics_cell.split(";") if s.strip() != ""]

        figaro_to_isics[figaro] = isics

        # Build reverse map
        for isic in isics:
            isic_to_figaro[isic] = figaro

    return figaro_to_isics, isic_to_figaro


def safe_split_ipc4_cell(cell):
    if pd.isna(cell):
        return []
    cell = str(cell).strip()
    if cell == "":
        return []
    # Primary separator is ';' per your example; also handle commas just in case
    parts = []
    for part in cell.replace(",", ";").split(";"):
        p = part.strip()
        if p:
            parts.append(p)
    return parts


def main():
    # Load mappings
    print("Loading IPC4 -> ISIC probability map from:", INPUT_IPC4_ISIC_CSV)
    ipc4_map = load_ipc_to_isic_map(INPUT_IPC4_ISIC_CSV, "ipc4")
    print(f"IPC4 crosswalk: {ipc4_map}")
    print(f"  loaded {len(ipc4_map)} ipc4 entries.")

    print("Loading IPC3 -> ISIC probability map from:", INPUT_IPC3_ISIC_CSV)
    ipc3_map = load_ipc_to_isic_map(INPUT_IPC3_ISIC_CSV, "ipc3")
    print(f"IPC3 crosswalk: {ipc3_map}")
    print(f"  loaded {len(ipc3_map)} ipc3 entries.")

    print("Loading IPC2 -> ISIC probability map from:", INPUT_IPC2_ISIC_CSV)
    ipc2_map = load_ipc_to_isic_map(INPUT_IPC2_ISIC_CSV, "ipc2")
    print(f"IPC2 crosswalk: {ipc2_map}")
    print(f"  loaded {len(ipc2_map)} ipc2 entries.")

    print("Loading IPC1 -> ISIC probability map from:", INPUT_IPC1_ISIC_CSV)
    ipc1_map = load_ipc_to_isic_map(INPUT_IPC1_ISIC_CSV, "ipc1")
    print(f"IPC1 crosswalk: {ipc1_map}")
    print(f"  loaded {len(ipc1_map)} ipc1 entries.")

    print("Loading Figaro -> ISIC map from:", INPUT_FIGARO_ISIC_CSV)
    figaro_to_isics, isic_to_figaro = load_figaro_map(INPUT_FIGARO_ISIC_CSV)
    print(f"Figaro crosswalk: {figaro_to_isics}")
    print(f"Figaro reverse crosswalk: {isic_to_figaro}")
    print(f"  loaded {len(figaro_to_isics)} figaro codes, {len(isic_to_figaro)} reverse mappings.")

    # Read patents file
    #print("Reading patents file:", INPUT_PATENTS_XLSX)
    #patents_df = pd.read_excel(INPUT_PATENTS_XLSX, dtype=str)
    print("Reading patents file:", INPUT_PATENTS_CSV)
    patents_df = pd.read_csv(INPUT_PATENTS_CSV, dtype=str)
    # normalize column names (strip)
    patents_df.columns = patents_df.columns.str.strip()

    # Required columns (case-insensitive match)
    col_map = {c.lower(): c for c in patents_df.columns}
    required = {
        "country_col": None,
        "year_col": None,
        "unique_ipc4_col": None,
        "patent_weight_col": None,
        "ipc4_weight_col": None
    }
    # heuristics to find columns
    for k in col_map:
        if "applicant residence" in k and "country" in k:
            required["country_col"] = col_map[k]
        if "application year" in k or (k == "year"):
            required["year_col"] = col_map[k]
        if "unique ipc4" in k or "unique_ipc4" in k or "unique ipc" in k:
            required["unique_ipc4_col"] = col_map[k]
        if "patent weight" in k:
            required["patent_weight_col"] = col_map[k]
        if "ipc4 weight" in k or "ipc4_weight" in k:
            required["ipc4_weight_col"] = col_map[k]

    # if some columns weren't auto-found, try known names
    # final fallback: try exact names used in your example
    if required["country_col"] is None and "Applicant Residence Country" in patents_df.columns:
        required["country_col"] = "Applicant Residence Country"
    if required["year_col"] is None and "Application Year" in patents_df.columns:
        required["year_col"] = "Application Year"
    if required["unique_ipc4_col"] is None and "Unique IPC4" in patents_df.columns:
        required["unique_ipc4_col"] = "Unique IPC4"
    if required["patent_weight_col"] is None and "Patent Weight" in patents_df.columns:
        required["patent_weight_col"] = "Patent Weight"
    if required["ipc4_weight_col"] is None and "IPC4 Weight" in patents_df.columns:
        required["ipc4_weight_col"] = "IPC4 Weight"

    # validate
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise ValueError(f"Could not locate required columns in patents file. Missing: {missing}. "
                         f"Found columns: {list(patents_df.columns)}")

    country_col = required["country_col"]
    year_col = required["year_col"]
    unique_ipc4_col = required["unique_ipc4_col"]
    patent_weight_col = required["patent_weight_col"]
    ipc4_weight_col = required["ipc4_weight_col"]

    # We'll accumulate into a nested dict: (country, isic, year) -> sum_weight
    accum = defaultdict(float)

    n_rows = len(patents_df)
    print(f"Processing {n_rows} patent rows...")
    skipped_ipc4_missing = 0
    missing_ipc1_codes = set()
    skipped_ipc1_not_in_map = 0
    for idx, row in patents_df.iterrows():
        country = str(row.get(country_col, "")).strip()
        year = str(row.get(year_col, "")).strip()
        if year == "" or year.lower() == "nan":
            year = "N/A"
        # safe numeric conversion for weights
        try:
            patent_weight = float(row.get(patent_weight_col, 0) if row.get(patent_weight_col, 0) not in (None, "nan") else 0)
        except Exception:
            raise ValueError("Could not find patent_weight")
        try:
            ipc4_weight = float(row.get(ipc4_weight_col, 0) if row.get(ipc4_weight_col, 0) not in (None, "nan") else 0)
        except Exception:
            raise ValueError("Could not find ipc4_weight")

        ipc4_list = safe_split_ipc4_cell(row.get(unique_ipc4_col, ""))
        if not ipc4_list:
            print(f"Could not find unique ipcs4 codes for {idx}")
            skipped_ipc4_missing += 1
            continue

        to_skip = False
        for ipc4 in ipc4_list:
            ipc4_key = ipc4.strip()
            if ipc4_key in ipc4_map:
                mapping = ipc4_map[ipc4_key]
            else:
                ipc3_key = ipc4_key[:3]
                if ipc3_key in ipc3_map:
                    mapping = ipc3_map[ipc3_key]
                else:
                    ipc2_key = ipc4_key[:2]
                    if ipc2_key in ipc2_map:
                        mapping = ipc2_map[ipc2_key]
                    else:
                        ipc1_key = ipc4_key[:1]
                        if ipc1_key in ipc1_map:
                            mapping = ipc1_map[ipc1_key]
                        else:
                            skipped_ipc1_not_in_map += (patent_weight * ipc4_weight)
                            missing_ipc1_codes.add(ipc1_key)
                            to_skip = True

            if to_skip:
                continue

            for (isic_code, prob_weight) in mapping:
                try:
                    prob_weight_f = float(prob_weight)
                except Exception:
                    raise ValueError(f"error converting {prob_weight} to float")
                add_value = patent_weight * ipc4_weight * prob_weight_f
                accum[(country, isic_code, year)] += add_value

    print("Done processing patents.")
    print(f"  skipped rows with no Unique IPC4: {skipped_ipc4_missing}")
    print(f"  ipc1 codes not found in map (count occurrences): {skipped_ipc1_not_in_map}")
    print(f"  ipc1 codes not found in map: {list(missing_ipc1_codes)}")

    # Convert accum to DataFrame: country, isic, year, count
    rows = []
    for (country, isic_code, year), val in accum.items():
        rows.append({
            "Country": country,
            "ISIC_rev4_2": isic_code,
            "Year": year,
            "Count": val
        })
    df_country_isic_year = pd.DataFrame(rows)
    if df_country_isic_year.empty:
        print("WARNING: No aggregated rows produced (empty). Exiting.")
        # still write empty file
        df_country_isic_year.to_excel(OUTPUT_INTERMEDIATE, index=False)
        return

    # Save intermediate country-isic-year aggregation (optional but helpful)
    print("Writing intermediate country-isic-year aggregation to:", OUTPUT_INTERMEDIATE)
    df_country_isic_year.sort_values(["Country", "ISIC_rev4_2", "Year"], inplace=True)
    df_country_isic_year.to_excel(OUTPUT_INTERMEDIATE, index=False)

    # Now transform ISIC -> figaro_code using isic_to_figaro mapping
    # If an ISIC has no figaro mapping, put 'UNMAPPED' or keep ISIC as industry.
    def map_isic_to_figaro(isic_code):
        return isic_to_figaro.get(isic_code, None)

    df_country_isic_year["FigaroCode"] = df_country_isic_year["ISIC_rev4_2"].apply(map_isic_to_figaro)
    # Where FigaroCode is None, you may want to keep ISIC code as fallback:
    df_country_isic_year["Industry Code"] = df_country_isic_year["FigaroCode"].fillna(df_country_isic_year["ISIC_rev4_2"])

    # Aggregate by Country, Industry Code (Figaro or fallback), Year
    df_final = (
        df_country_isic_year
        .groupby(["Country", "Industry Code", "Year"], as_index=False)["Count"]
        .sum()
    )

    # Sort for readability
    df_final.sort_values(["Country", "Industry Code", "Year"], inplace=True)

    # Write final output
    print("Writing final Country-Industry-Year aggregation to:", OUTPUT_FILE)
    df_final.to_excel(OUTPUT_FILE, index=False)

    # Summary
    total_patent_weight_sum = df_final["Count"].sum()
    print("Complete.")
    print(f"  Output rows: {len(df_final)}")
    print(f"  Total aggregated count (sum of Count column): {total_patent_weight_sum:.6f}")
    print("Saved:", OUTPUT_FILE)
    print("Also saved intermediate ISIC-level file:", OUTPUT_INTERMEDIATE)


if __name__ == "__main__":
    # Basic sanity: check paths exist
    for p in [INPUT_PATENTS_CSV, INPUT_IPC4_ISIC_CSV, INPUT_FIGARO_ISIC_CSV]:
        if not os.path.exists(p):
            print(f"ERROR: input path not found: {p}")
    main()
