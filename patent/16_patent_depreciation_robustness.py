"""
Stages executed in order:
  1. Consolidate ALL patents from per-country Excel folders → CSV
  2. Consolidate AI  patents from Segment1/Segment2 folders → CSV
  3. Add Patent Weight & IPC4 Weight to both CSVs (in-place)
  4. Aggregate both CSVs to Country × Industry × Year via
     IPC→ISIC crosswalk (with IPC3/2/1 fallback) then ISIC→Figaro
  5. Merge All-patents and AI-patents aggregations; derive Non-AI counts
  6. Compute PIM patent stocks for range of different depreciation rates
  7. Export final AI & Non-AI endowment pivot tables (one file per rate)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
from itertools import product as iter_product

# ============================================================
# GLOBAL CONFIGURATION
# ============================================================

# ---------- Base directories ----------
BASE_DIR_ALL = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/All_Patents"
BASE_DIR_AI = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_Patents"
CROSSWALK_DIR = "/Users/nikhil/Documents/Thesis/Patents/Crosswalk"
OUTPUT_DIR = "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications"

# ---------- Intermediate file paths (preserved on disk) ----------
ALL_PATENTS_CSV = os.path.join(BASE_DIR_ALL, "PCT_All_Patents.csv")
AI_PATENTS_CSV = os.path.join(BASE_DIR_AI, "PCT_AI_Patents.csv")

ALL_BY_IND_YEAR = os.path.join(BASE_DIR_ALL, "PCT_All_Patents_By_Industry_Year.xlsx")
ALL_INTERMEDIATE = os.path.join(BASE_DIR_ALL, "PCT_All_Patents_By_Industry_Year_Intermediate.xlsx")

AI_BY_IND_YEAR = os.path.join(BASE_DIR_AI, "PCT_AI_Patents_By_Industry_Year.xlsx")
AI_INTERMEDIATE = os.path.join(BASE_DIR_AI, "PCT_AI_Patents_By_Industry_Year_Intermediate.xlsx")

MERGED_FILE = os.path.join(OUTPUT_DIR, "PCT_Patents_By_Industry.xlsx")

# ---------- Crosswalk paths ----------
IPC4_ISIC_CSV = os.path.join(CROSSWALK_DIR, "ipc4_nace_alp.csv")
IPC3_ISIC_CSV = os.path.join(CROSSWALK_DIR, "ipc3_nace_alp.csv")
IPC2_ISIC_CSV = os.path.join(CROSSWALK_DIR, "ipc2_nace_alp.csv")
IPC1_ISIC_CSV = os.path.join(CROSSWALK_DIR, "ipc1_nace_alp.csv")
FIGARO_ISIC_CSV = os.path.join(CROSSWALK_DIR, "figaro_nace.csv")

# ---------- Year scope ----------
BASE_YEAR = 2000  # earliest year for patent flows & stock initialisation
END_YEAR = 2021  # last year for flows, stocks, and final output
STOCK_START_YEAR = 2010  # first year kept in the final endowment pivots

# ---------- PIM depreciation rates (%) to sweep ----------
# Each value is expressed as a percentage; converted to a fraction inside the code.
# DEPRECIATION_RATES = [15]
DEPRECIATION_RATES = [0, 5, 10, 12, 15, 17, 20, 25, 30]

# ---------- Country & industry master lists (for the full Country×Industry×Year grid) ----------
COUNTRIES = [
    "BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT", "CY", "LV", "LT", "LU", "HU",
    "MT", "NL", "AT", "PL", "PT", "RO", "SI", "SK", "FI", "SE",
    "AR", "AU", "BR", "CA", "CH", "CN", "ID", "IN", "JP", "KR", "MX", "NO", "RU", "SA", "TR", "GB", "US", "ZA",
    "FIGW1"
]

INDUSTRIES = [
    "A01", "A02", "A03", "B",
    "C10T12", "C13T15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23",
    "C24", "C25", "C26", "C27", "C28", "C29", "C30", "C31_32", "C33",
    "D35", "E36", "E37T39", "F",
    "G45", "G46", "G47", "H49", "H50", "H51", "H52", "H53",
    "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L",
    "M69_70", "M71", "M72", "M73", "M74_75",
    "N77", "N78", "N79", "N80T82",
    "O84", "P85", "Q86", "Q87_88",
    "R90T92", "R93", "S94", "S95", "S96", "T", "U"
]


# ============================================================
# HELPER – shared IPC4 extraction
# ============================================================

def extract_ipc4_series(ipc_series: pd.Series) -> pd.Series:
    """
    For every cell in *ipc_series* (semicolon-separated IPC codes),
    extract the first 4 characters of each code, deduplicate, sort,
    and return as a semicolon-joined string.
    """

    def _extract(ipc_str):
        if pd.isna(ipc_str):
            return ""
        parts = [p.strip() for p in str(ipc_str).split(";") if p.strip()]
        ipc4 = {p.split("/")[0][:4] for p in parts if len(p.split("/")[0]) >= 4}
        return ";".join(sorted(ipc4))

    return ipc_series.apply(_extract)


# ============================================================
# STAGE 1 – Consolidate ALL patents into PCT_All_Patents.csv
# ============================================================

def consolidate_all_patents():
    """
    Walks every country-code subfolder inside BASE_DIR_ALL, reads all
    .xlsx/.xls files (skipping the first 5 header rows that WIPO uses),
    filters to BASE_YEAR–END_YEAR, deduplicates on Application Id within
    each country folder, adds the country code and computed columns, and
    appends everything to ALL_PATENTS_CSV.

    The CSV is initialised with a header row if it does not already exist.
    """
    print("\n" + "=" * 60)
    print("STAGE 1 – Consolidating ALL patents")
    print("=" * 60)

    # -- initialise output CSV with header if missing --
    HEADER = [
        "Applicant Residence Country", "Application Id", "Application Number",
        "Application Date", "Application Year", "Title", "IPC", "Unique IPC4"
    ]
    if not os.path.exists(ALL_PATENTS_CSV):
        pd.DataFrame(columns=HEADER).to_csv(ALL_PATENTS_CSV, index=False)

    for country_code in sorted(os.listdir(BASE_DIR_ALL)):
        folder_path = os.path.join(BASE_DIR_ALL, country_code)
        if not os.path.isdir(folder_path):
            continue

        print(f"  Processing country: {country_code} …")
        all_entries = []
        seen_app_ids = set()  # track duplicates within this country

        for filename in sorted(os.listdir(folder_path)):
            if not filename.lower().endswith(('.xlsx', '.xls')):
                continue
            file_path = os.path.join(folder_path, filename)
            try:
                df = pd.read_excel(file_path, skiprows=5)
                df.dropna(how='all', inplace=True)

                if "Application Date" not in df.columns:
                    print(f"    [ERROR] Missing 'Application Date' in {filename} – skipped.")
                    continue

                # -- parse & filter dates to BASE_YEAR … END_YEAR --
                df["Application Date"] = pd.to_datetime(
                    df["Application Date"], errors="coerce", dayfirst=True
                )
                df = df[
                    (df["Application Date"] >= datetime(BASE_YEAR, 1, 1)) &
                    (df["Application Date"] <= datetime(END_YEAR, 12, 31))
                    ]
                if df.empty:
                    continue

                # -- deduplicate on Application Id --
                before = len(df)
                df = df[~df["Application Id"].isin(seen_app_ids)]
                seen_app_ids.update(df["Application Id"].dropna().astype(str).tolist())
                skipped = before - len(df)
                if skipped > 0:
                    print(f"    [INFO] Skipped {skipped} duplicate Application Ids in {filename}")
                if df.empty:
                    continue

                # -- add / rename columns --
                df["Applicant Residence Country"] = country_code
                df["Application Date"] = df["Application Date"].dt.strftime("%d.%m.%Y")
                df["Application Year"] = pd.to_datetime(
                    df["Application Date"], format="%d.%m.%Y", errors="coerce"
                ).dt.year
                df["Unique IPC4"] = extract_ipc4_series(df.get("I P C", pd.Series([""] * len(df))))
                df.rename(columns={"I P C": "IPC"}, inplace=True)

                df = df[HEADER]
                all_entries.append(df)

            except Exception as e:
                print(f"    [ERROR] Reading {file_path}: {e}")

        # -- append all entries for this country to the master CSV --
        if all_entries:
            combined = pd.concat(all_entries, ignore_index=True)
            combined.to_csv(ALL_PATENTS_CSV, mode='a', header=False, index=False)
            print(f"    [INFO] Appended {len(combined)} rows for {country_code}")

    print(f"  ✅ Stage 1 complete → {ALL_PATENTS_CSV}")


# ============================================================
# STAGE 2 – Consolidate AI patents into PCT_AI_Patents.csv
# ============================================================

def consolidate_ai_patents():
    """
    AI patents arrive in two segments (Segment1 / Segment2) that may
    overlap.  Segment1 is the base; any Application Number already seen
    in Segment1 is dropped from Segment2 before writing.

    Processing is otherwise identical to Stage 1.
    """
    print("\n" + "=" * 60)
    print("STAGE 2 – Consolidating AI patents")
    print("=" * 60)

    HEADER = [
        "Applicant Residence Country", "Application Id", "Application Number",
        "Application Date", "Application Year", "Title", "IPC", "Unique IPC4"
    ]
    if not os.path.exists(AI_PATENTS_CSV):
        pd.DataFrame(columns=HEADER).to_csv(AI_PATENTS_CSV, index=False)

    # accumulator for Segment1 Application Numbers (used to deduplicate Segment2)
    segment1_app_numbers: set = set()

    for segment_name in ["Segment1", "Segment2"]:
        print(f"\n  [STEP] Processing {segment_name} …")
        segment_path = os.path.join(BASE_DIR_AI, segment_name)
        if not os.path.exists(segment_path):
            print(f"    ⚠️  Segment folder not found: {segment_path}")
            continue

        for country_code in sorted(os.listdir(segment_path)):
            folder_path = os.path.join(segment_path, country_code)
            if not os.path.isdir(folder_path):
                continue

            print(f"    Processing {segment_name} – {country_code} …")
            country_entries = []

            for filename in sorted(os.listdir(folder_path)):
                if not filename.lower().endswith(('.xlsx', '.xls')):
                    continue
                file_path = os.path.join(folder_path, filename)
                try:
                    df = pd.read_excel(file_path, skiprows=5)
                    df.dropna(how='all', inplace=True)

                    if "Application Date" not in df.columns or "Application Number" not in df.columns:
                        continue

                    # -- parse & filter dates --
                    df["Application Date"] = pd.to_datetime(
                        df["Application Date"], errors="coerce", dayfirst=True
                    )
                    df = df[
                        (df["Application Date"] >= datetime(BASE_YEAR, 1, 1)) &
                        (df["Application Date"] <= datetime(END_YEAR, 12, 31))
                        ]
                    if df.empty:
                        continue

                    # -- cross-segment deduplication --
                    app_numbers = df["Application Number"].astype(str).str.strip()
                    if segment_name == "Segment1":
                        segment1_app_numbers.update(app_numbers.tolist())
                    else:
                        # drop any Application Number already present in Segment1
                        df = df[~app_numbers.isin(segment1_app_numbers)]
                    if df.empty:
                        continue

                    # -- add / rename columns --
                    df["Applicant Residence Country"] = country_code
                    df["Application Date"] = df["Application Date"].dt.strftime("%d.%m.%Y")
                    df["Application Year"] = pd.to_datetime(
                        df["Application Date"], format="%d.%m.%Y", errors="coerce"
                    ).dt.year
                    df["Unique IPC4"] = extract_ipc4_series(
                        df.get("I P C", pd.Series([""] * len(df)))
                    )
                    df.rename(columns={"I P C": "IPC"}, inplace=True)

                    df = df[HEADER]
                    country_entries.append(df)

                except Exception as e:
                    print(f"      [ERROR] Reading {file_path}: {e}")

            # -- write once per country to minimise I/O --
            if country_entries:
                combined = pd.concat(country_entries, ignore_index=True)
                combined.to_csv(AI_PATENTS_CSV, mode='a', header=False, index=False)
                print(f"      [INFO] Appended {len(combined)} rows for {segment_name} – {country_code}")

    print(f"  ✅ Stage 2 complete → {AI_PATENTS_CSV}")


# ============================================================
# STAGE 3 – Add Patent Weight & IPC4 Weight to a patent CSV
# ============================================================

def add_weights(csv_path: str):
    """
    Adds two columns **in-place** to the given CSV:

    Patent Weight  = 1 / (number of rows sharing the same Application Number)
                     Spreads a single patent's contribution equally across the
                     technology classes it is claimed in.
    IPC4 Weight    = 1 / (number of distinct IPC4 codes in that row's Unique IPC4)
                     Spreads a single row's contribution equally across the
                     technology classes listed.
    """
    print(f"\n  Adding weights to: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str)

    # -- Patent Weight: inverse of Application Number frequency --
    app_counts = df["Application Number"].value_counts().to_dict()
    df["Patent Weight"] = df["Application Number"].apply(
        lambda x: 1.0 / app_counts.get(x, 1) if pd.notna(x) and x != "N/A" else 1.0
    )

    # -- IPC4 Weight: inverse of unique IPC4 code count --
    def _ipc4_weight(ipc_str):
        if not isinstance(ipc_str, str) or not ipc_str.strip():
            return 1.0
        codes = {c.strip() for c in ipc_str.split(";") if c.strip()}
        return 1.0 / len(codes) if codes else 1.0

    df["IPC4 Weight"] = df["Unique IPC4"].apply(_ipc4_weight)

    # -- save back to the same file (atomic via tmp) --
    tmp = csv_path + ".tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, csv_path)
    print(f"    ✅ Weights added ({len(df)} rows)")


# ============================================================
# STAGE 4 – Aggregate patents to Country × Industry × Year
# ============================================================

# ---- 4a: crosswalk loaders ----

def load_ipc_to_isic_map(ipc_csv_path: str, ipc_col_name: str) -> dict:
    """
    Reads a crosswalk CSV that maps an IPC code to one or more ISIC codes,
    each with an associated probability weight.  Returns a dict:
        { ipc_code: [(isic_code, probability_weight), …] }
    """
    df = pd.read_csv(ipc_csv_path, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]

    ipc_col = ipc_col_name.lower()
    isic_col = "isic_rev4_2"
    prob_col = "probability_weight"

    ipc_map: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for _, r in df.iterrows():
        ipc = str(r.get(ipc_col, "")).strip()
        isic = str(r.get(isic_col, "")).strip()
        if not ipc or ipc == "nan" or not isic or isic == "nan":
            continue
        try:
            prob = float(r.get(prob_col, 0))
        except (ValueError, TypeError):
            prob = 0.0
        ipc_map[ipc].append((isic, prob))
    return dict(ipc_map)


def load_figaro_map(figaro_csv_path: str):
    """
    Reads the Figaro↔ISIC crosswalk.  Returns two dicts:
        figaro_to_isics : { figaro_code: [isic1, isic2, …] }
        isic_to_figaro  : { isic_code:   figaro_code }          (last-write wins)
    """
    df = pd.read_csv(figaro_csv_path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    colmap = {c.lower(): c for c in df.columns}

    figaro_col = colmap.get("figaro_code", df.columns[0])
    isics_col = colmap.get("isic_rev4_2_codes", df.columns[1])

    figaro_to_isics, isic_to_figaro = {}, {}
    for _, r in df.iterrows():
        figaro = str(r[figaro_col]).strip()
        isics_raw = str(r[isics_col]).strip()
        isics = [s.strip() for s in isics_raw.split(";") if
                 s.strip()] if isics_raw and isics_raw.lower() != "nan" else []
        figaro_to_isics[figaro] = isics
        for isic in isics:
            isic_to_figaro[isic] = figaro
    return figaro_to_isics, isic_to_figaro


# ---- 4b: core aggregation ----

def _safe_split(cell) -> list[str]:
    """Split a semicolon-separated cell into stripped tokens; tolerates commas."""
    if pd.isna(cell):
        return []
    return [p.strip() for p in str(cell).replace(",", ";").split(";") if p.strip()]


def aggregate_to_country_industry_year(
        patents_csv: str,
        output_final: str,
        output_intermediate: str
):
    """
    For each patent row:
      1. Look up every IPC4 code in the IPC4→ISIC crosswalk.
         Fall back to IPC3 → IPC2 → IPC1 if the exact code is missing.
      2. For each resulting (ISIC, probability) pair, accumulate:
             patent_weight × ipc4_weight × probability_weight
         into a (Country, ISIC, Year) bucket.
      3. Map ISIC → Figaro industry code (keep ISIC as fallback if unmapped).
      4. Re-aggregate by (Country, Figaro/Industry Code, Year).

    Writes both an intermediate ISIC-level file and the final Figaro-level file.
    """
    print(f"\n  Aggregating: {patents_csv}")

    # -- load all crosswalks --
    ipc4_map = load_ipc_to_isic_map(IPC4_ISIC_CSV, "ipc4")
    ipc3_map = load_ipc_to_isic_map(IPC3_ISIC_CSV, "ipc3")
    ipc2_map = load_ipc_to_isic_map(IPC2_ISIC_CSV, "ipc2")
    ipc1_map = load_ipc_to_isic_map(IPC1_ISIC_CSV, "ipc1")
    _figaro_to_isics, isic_to_figaro = load_figaro_map(FIGARO_ISIC_CSV)

    print(f"    Crosswalk sizes – IPC4: {len(ipc4_map)}, IPC3: {len(ipc3_map)}, "
          f"IPC2: {len(ipc2_map)}, IPC1: {len(ipc1_map)}, Figaro: {len(isic_to_figaro)}")

    # -- read patents --
    df = pd.read_csv(patents_csv, dtype=str)
    df.columns = df.columns.str.strip()
    print(f"    Loaded {len(df)} patent rows.")

    # -- locate required columns (robust to minor name variations) --
    col_map = {c.lower(): c for c in df.columns}
    country_col = col_map.get("applicant residence country", "Applicant Residence Country")
    year_col = col_map.get("application year", "Application Year")
    unique_ipc4_col = col_map.get("unique ipc4", "Unique IPC4")
    patent_weight_col = col_map.get("patent weight", "Patent Weight")
    ipc4_weight_col = col_map.get("ipc4 weight", "IPC4 Weight")

    # -- accumulate weighted counts into (country, isic, year) buckets --
    accum: dict[tuple[str, str, str], float] = defaultdict(float)
    skipped_no_ipc4 = 0
    missing_ipc1_codes: set[str] = set()

    for _, row in df.iterrows():
        country = str(row.get(country_col, "")).strip()
        year = str(row.get(year_col, "")).strip() or "N/A"

        try:
            pw = float(row.get(patent_weight_col, 0) or 0)
        except (ValueError, TypeError):
            pw = 0.0
        try:
            iw = float(row.get(ipc4_weight_col, 0) or 0)
        except (ValueError, TypeError):
            iw = 0.0

        ipc4_list = _safe_split(row.get(unique_ipc4_col, ""))
        if not ipc4_list:
            skipped_no_ipc4 += 1
            continue

        for ipc4 in ipc4_list:
            # -- cascading crosswalk lookup: IPC4 → IPC3 → IPC2 → IPC1 --
            mapping = None
            if ipc4 in ipc4_map:
                mapping = ipc4_map[ipc4]
            elif ipc4[:3] in ipc3_map:
                mapping = ipc3_map[ipc4[:3]]
            elif ipc4[:2] in ipc2_map:
                mapping = ipc2_map[ipc4[:2]]
            elif ipc4[:1] in ipc1_map:
                mapping = ipc1_map[ipc4[:1]]
            else:
                missing_ipc1_codes.add(ipc4[:1])
                continue  # no mapping available – skip this IPC4

            for (isic_code, prob) in mapping:
                try:
                    prob_f = float(prob)
                except (ValueError, TypeError):
                    prob_f = 0.0
                accum[(country, isic_code, year)] += pw * iw * prob_f

    print(f"    Skipped rows with no Unique IPC4 : {skipped_no_ipc4}")
    print(f"    IPC1 codes with no crosswalk match: {sorted(missing_ipc1_codes)}")

    # -- build intermediate DataFrame (Country × ISIC × Year) --
    rows_isic = [
        {"Country": c, "ISIC_rev4_2": isic, "Year": y, "Count": val}
        for (c, isic, y), val in accum.items()
    ]
    df_isic = pd.DataFrame(rows_isic)
    if df_isic.empty:
        print("    ⚠️  Aggregation produced zero rows.")
        pd.DataFrame().to_excel(output_intermediate, index=False)
        pd.DataFrame().to_excel(output_final, index=False)
        return

    df_isic.sort_values(["Country", "ISIC_rev4_2", "Year"], inplace=True)
    df_isic.to_excel(output_intermediate, index=False)
    print(f"    Intermediate file written: {output_intermediate}")

    # -- map ISIC → Figaro (fall back to raw ISIC if unmapped) --
    df_isic["FigaroCode"] = df_isic["ISIC_rev4_2"].map(isic_to_figaro)
    df_isic["Industry Code"] = df_isic["FigaroCode"].fillna(df_isic["ISIC_rev4_2"])

    # -- re-aggregate at the Figaro level --
    df_final = (
        df_isic
            .groupby(["Country", "Industry Code", "Year"], as_index=False)["Count"]
            .sum()
            .sort_values(["Country", "Industry Code", "Year"])
    )

    df_final.to_excel(output_final, index=False)
    print(
        f"    Final file written : {output_final}  ({len(df_final)} rows, total count = {df_final['Count'].sum():.4f})")


# ============================================================
# STAGE 5 – Merge All-patents & AI-patents aggregations
# ============================================================

def merge_all_and_ai():
    """
    Left-joins the All-patents and AI-patents Country×Industry×Year
    tables.  Derives 'Non AI Count' = Total − AI, clamped to ≥ 0.

    Output columns: Country, Industry Code, Year,
                    Total Count, AI Count, Non AI Count
    """
    print("\n" + "=" * 60)
    print("STAGE 5 – Merging All & AI patent aggregations")
    print("=" * 60)

    df_all = pd.read_excel(ALL_BY_IND_YEAR).rename(columns=lambda c: c.strip())
    df_ai = pd.read_excel(AI_BY_IND_YEAR).rename(columns=lambda c: c.strip())

    merged = pd.merge(
        df_all, df_ai,
        on=["Country", "Industry Code", "Year"],
        how="left",
        suffixes=("_all", "_ai")
    )
    merged["Count_ai"] = merged["Count_ai"].fillna(0)
    merged["Non AI Count"] = merged["Count_all"] - merged["Count_ai"]

    # -- clamp: if rounding / crosswalk drift makes Non-AI negative, cap at 0 --
    neg_mask = merged["Non AI Count"] < 0
    if neg_mask.any():
        print(f"    ⚠️  {neg_mask.sum()} rows had Non-AI < 0; clamped AI to Total and Non-AI to 0.")
        merged.loc[neg_mask, "Count_ai"] = merged.loc[neg_mask, "Count_all"]
        merged.loc[neg_mask, "Non AI Count"] = 0

    result = merged.rename(columns={"Count_all": "Total Count", "Count_ai": "AI Count"})
    result = result[["Country", "Industry Code", "Year", "Total Count", "AI Count", "Non AI Count"]]
    result.to_excel(MERGED_FILE, index=False)
    print(f"  ✅ Merged file saved → {MERGED_FILE}")


# ============================================================
# STAGE 6 – PIM patent-stock calculation (all depreciation rates)
# ============================================================

def compute_pim_stocks():
    """
    Reads the merged Country×Industry×Year flow file and, for every
    depreciation rate in DEPRECIATION_RATES, computes patent stocks
    using the perpetual-inventory method:

        Stock(BASE_YEAR)  = Flow(BASE_YEAR)
        Stock(t)          = (1 − δ) × Stock(t−1) + Flow(t)

    The full Country × Industry × Year grid (including zero-flow cells)
    is materialised so that the recursion is correct even when a
    country–industry pair has no patents in some years.

    Returns a dict:  { dep_rate_pct : DataFrame with stock columns }
    Each DataFrame retains all flow columns plus:
        Total Stock, AI Stock, Non AI Stock
    """
    print("\n" + "=" * 60)
    print("STAGE 6 – Computing PIM patent stocks")
    print("=" * 60)

    df = pd.read_excel(MERGED_FILE).rename(columns=lambda c: c.strip())

    # -- ensure correct dtypes --
    df["Year"] = df["Year"].astype(int)
    df["Country"] = df["Country"].astype(str).str.strip()
    df["Industry Code"] = df["Industry Code"].astype(str).str.strip()
    for col in ["Total Count", "AI Count", "Non AI Count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)

    # -- materialise the full grid so every (country, industry, year) exists --
    years = list(range(BASE_YEAR, END_YEAR + 1))
    full_index = pd.MultiIndex.from_product(
        [sorted(COUNTRIES), sorted(INDUSTRIES), years],
        names=["Country", "Industry Code", "Year"]
    )
    df_full = (
        df.set_index(["Country", "Industry Code", "Year"])
            .reindex(full_index, fill_value=0)
            .reset_index()
    )
    df_full.sort_values(["Country", "Industry Code", "Year"], inplace=True)

    # -- run PIM for each depreciation rate --
    results: dict[int, pd.DataFrame] = {}

    for dep_pct in DEPRECIATION_RATES:
        dep = dep_pct / 100.0  # convert percentage → fraction
        print(f"  Computing stocks at δ = {dep_pct}% …")

        # vectorised group-wise PIM using cumulative product trick
        stock_total, stock_ai, stock_nonai = [], [], []

        for (_country, _ind), grp in df_full.groupby(
                ["Country", "Industry Code"], sort=True
        ):
            grp = grp.sort_values("Year")
            n = len(grp)

            # -- iterative PIM (straightforward, correct) --
            s_tot = s_ai = s_nai = 0.0
            for i, (_, row) in enumerate(grp.iterrows()):
                if i == 0:
                    # base year: stock = flow
                    s_tot = float(row["Total Count"])
                    s_ai = float(row["AI Count"])
                    s_nai = float(row["Non AI Count"])
                else:
                    s_tot = (1 - dep) * s_tot + float(row["Total Count"])
                    s_ai = (1 - dep) * s_ai + float(row["AI Count"])
                    s_nai = (1 - dep) * s_nai + float(row["Non AI Count"])
                stock_total.append(s_tot)
                stock_ai.append(s_ai)
                stock_nonai.append(s_nai)

        df_out = df_full.copy()
        df_out["Total Stock"] = stock_total
        df_out["AI Stock"] = stock_ai
        df_out["Non AI Stock"] = stock_nonai
        df_out = df_out[[
            "Country", "Industry Code", "Year",
            "Total Count", "AI Count", "Non AI Count",
            "Total Stock", "AI Stock", "Non AI Stock"
        ]]
        results[dep_pct] = df_out

    print("  ✅ All depreciation rates computed.")
    return results


# ============================================================
# STAGE 7 – Export final AI & Non-AI endowment pivot tables
# ============================================================

def export_endowment_pivots(stock_results: dict[int, pd.DataFrame]):
    """
    For each depreciation rate, filters stock data to
    STOCK_START_YEAR … END_YEAR, pivots on Year with
    Country_IndustryCode as the row index, and writes two Excel files.
    """
    print("\n" + "=" * 60)
    print("STAGE 7 – Exporting endowment pivot tables")
    print("=" * 60)

    for dep_pct, df in stock_results.items():
        # -- filter to the final year window --
        df_filt = df[(df["Year"] >= STOCK_START_YEAR) & (df["Year"] <= END_YEAR)].copy()

        # Define the two exports (AI and Non-AI)
        targets = [
            ("AI Stock", f"AI_PATENTS_{dep_pct}_DEPRECIATION.xlsx"),
            ("Non AI Stock", f"NON_AI_PATENTS_{dep_pct}_DEPRECIATION.xlsx")
        ]

        for stock_col, filename in targets:
            # 1. Pivot using separate index levels to ensure 'FI' sorts before 'FIGW1'
            pivot = (
                df_filt.pivot_table(
                    index=["Country", "Industry Code"],
                    columns="Year",
                    values=stock_col,
                    aggfunc="mean"
                )
                    .sort_index()  # Sorts by Country (alphabetical) then Industry
            )

            # 2. Transform the MultiIndex into the "Country_IndustryCode" string format
            # This happens AFTER sorting, so the underscore doesn't break the order.
            pivot.index = [f"{c}_{i}" for c, i in pivot.index]
            pivot.index.name = "factor_key"

            # 3. Ensure years are sorted correctly as columns
            pivot = pivot.reindex(sorted(df_filt["Year"].unique()), axis=1)

            # 4. Export to Excel
            out_path = os.path.join(OUTPUT_DIR, filename)
            pivot.to_excel(out_path, sheet_name="Final")
            print(f"    Wrote {out_path}")

    print("  ✅ All endowment files exported.")


# ============================================================
# MAIN – orchestrator
# ============================================================

if __name__ == "__main__":
    # # ----------------------------------------------------------
    # # Stage 1: read raw Excel → PCT_All_Patents.csv
    # # ----------------------------------------------------------
    # consolidate_all_patents()
    #
    # # ----------------------------------------------------------
    # # Stage 2: read raw Excel (Seg1 + Seg2) → PCT_AI_Patents.csv
    # # ----------------------------------------------------------
    # consolidate_ai_patents()
    #
    # # ----------------------------------------------------------
    # # Stage 3: attach Patent Weight & IPC4 Weight columns
    # #          (runs on both CSVs in place)
    # # ----------------------------------------------------------
    # print("\n" + "=" * 60)
    # print("STAGE 3 – Adding weights")
    # print("=" * 60)
    # add_weights(ALL_PATENTS_CSV)
    # add_weights(AI_PATENTS_CSV)
    #
    # # ----------------------------------------------------------
    # # Stage 4: IPC → ISIC → Figaro aggregation
    # #          (runs on both CSVs; writes intermediate + final xlsx)
    # # ----------------------------------------------------------
    # print("\n" + "=" * 60)
    # print("STAGE 4 – Aggregating to Country × Industry × Year")
    # print("=" * 60)
    # aggregate_to_country_industry_year(ALL_PATENTS_CSV, ALL_BY_IND_YEAR, ALL_INTERMEDIATE)
    # aggregate_to_country_industry_year(AI_PATENTS_CSV, AI_BY_IND_YEAR, AI_INTERMEDIATE)
    #
    # # ----------------------------------------------------------
    # # Stage 5: merge All & AI counts; derive Non-AI
    # # ----------------------------------------------------------
    # merge_all_and_ai()

    # ----------------------------------------------------------
    # Stage 6: perpetual-inventory stocks for every dep. rate
    # ----------------------------------------------------------
    stock_results = compute_pim_stocks()

    # ----------------------------------------------------------
    # Stage 7: pivot & export final endowment files
    # ----------------------------------------------------------
    export_endowment_pivots(stock_results)

    print("\n" + "=" * 60)
    print("✅  PIPELINE COMPLETE – all intermediate and final files written.")
    print("=" * 60)
