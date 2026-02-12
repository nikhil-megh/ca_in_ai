import pandas as pd
import numpy as np
from collections import defaultdict

# -------------------------
# CONSTANTS
# -------------------------

YEARS = list(range(2010, 2018))
YEARS_STR = [str(y) for y in YEARS]

INDUSTRIES_64 = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]

INDUSTRIES_91 = [
    "TOTAL", "A", "A01", "A02", "A03", "B-E", "B", "C", "C10-C12", "C13-C15",
    "C16-C18", "C16", "C17", "C18", "C19", "C20", "C21", "C22_C23", "C22", "C23",
    "C24_C25", "C24", "C25", "C26", "C27", "C28", "C29_C30", "C29", "C30",
    "C31-C33", "C31_C32", "C33", "D", "E", "E36", "E37-E39", "F", "G-I", "G",
    "G45", "G46", "G47", "H", "H49", "H50", "H51", "H52", "H53", "I", "J",
    "J58-J60", "J58", "J59_J60", "J61", "J62_J63", "K", "K64", "K65", "K66", "L",
    "L68A", "M_N", "M", "M69-M71", "M69_M70", "M71", "M72", "M73-M75", "M73", "M74_M75",
    "N", "N77", "N78", "N79", "N80-N82", "O-Q", "O", "P", "Q", "Q86", "Q87_Q88",
    "R-U", "R", "R90-R92", "R93", "S", "S94", "S95", "S96", "T", "U"
]

# Mapping 91-industries → 64-industries
MAPPING_91_TO_64 = {
    "A01": "A01", "A02": "A02", "A03": "A03",
    "B": "B",
    "C10-C12": "C10T12", "C13-C15": "C13T15",
    "C16": "C16", "C17": "C17", "C18": "C18", "C19": "C19",
    "C20": "C20", "C21": "C21",
    "C22": "C22", "C23": "C23",
    "C24": "C24", "C25": "C25",
    "C26": "C26", "C27": "C27", "C28": "C28",
    "C29": "C29", "C30": "C30",
    "C31_C32": "C31_32", "C33": "C33",
    "D": "D35",
    "E36": "E36", "E37-E39": "E37T39",
    "F": "F",
    "G45": "G45", "G46": "G46", "G47": "G47",
    "H49": "H49", "H50": "H50", "H51": "H51",
    "H52": "H52", "H53": "H53",
    "I": "I",
    "J58": "J58", "J59_J60": "J59_60",
    "J61": "J61", "J62_J63": "J62_63",
    "K64": "K64", "K65": "K65", "K66": "K66",
    "L": "L",
    "M69_M70": "M69_70", "M71": "M71", "M72": "M72",
    "M73": "M73", "M74_M75": "M74_75",
    "N77": "N77", "N78": "N78", "N79": "N79",
    "N80-N82": "N80T82",
    "O": "O84", "P": "P85", "Q86": "Q86", "Q87_Q88": "Q87_88",
    "R90-R92": "R90T92", "R93": "R93",
    "S94": "S94", "S95": "S95", "S96": "S96",
    "T": "T", "U": "U"
}

# -------------------------
# DONOR BUCKETS
# -------------------------
DONORS = {
    "NO": ["DK", "FI"],
    "SE": ["DK", "FI", "NO"],
    "US": ["GB", "AT"],
    "DE": ["AT", "GB", "DK"],
    "IE": ["AT", "GB", "DK"],
    "LU": ["AT", "GB", "DK"],
    "BE": ["AT", "GB", "DE"],
    "FR": ["AT", "GB", "DE"],
    "NL": ["AT", "GB", "DE"],
    "IT": ["FR", "GR"],
    "ES": ["FR", "GR", "IT"],
    "PT": ["FR", "GR", "ES"],
    "EE": ["LV", "FI"],
    "LT": ["LV", "FI"],
    "HR": ["AT", "GR", "CZ"],
    "SI": ["AT", "GR", "CZ"],
    "CY": ["GR", "SI"],
    "MT": ["GR", "SI"],
    "HU": ["CZ", "SK", "BG"],
    "PL": ["CZ", "SK", "BG"],
    "RO": ["CZ", "SK", "BG"],
    "CA": ["US", "GB"],
    "AU": ["US", "GB", "CA"],
    "KR": ["US", "DE", "AU"],
    "JP": ["US", "DE", "AU"],
    "IN": ["BG", "CZ", "SK", "LV", "EE", "LT", "HR", "HU", "PL", "RO", "SI", "GR"],
    "CN": ["IN", "JP", "KR"],
}

AGG_LEVEL_1_MAPPING = {
    "C16": "C16-C18",
    "C17": "C16-C18",
    "C18": "C16-C18",
    "C22": "C22_C23",
    "C23": "C22_C23",
    "C24": "C24_C25",
    "C25": "C24_C25",
    "C29": "C29_C30",
    "C30": "C29_C30",
    "C31_32": "C31-C33",
    "C33": "C31-C33",
    "J58": "J58-J60",
    "J59_60": "J58-J60",
    "M69_70": "M69-M71",
    "M71": "M69-M71",
    "M73": "M73-M75",
    "M74_75": "M73-M75"
}

AGG_LEVEL_2_MAPPING = {
    "A01": "A","A02": "A","A03": "A","B": "B",
    "C10T12": "C","C13T15": "C","C16": "C","C17": "C","C18": "C","C19": "C",
    "C20": "C","C21": "C","C22": "C","C23": "C","C24": "C","C25": "C","C26": "C",
    "C27": "C","C28": "C","C29": "C","C30": "C","C31_32": "C","C33": "C",
    "D35": "D","E36": "E","E37T39": "E","F": "F",
    "G45": "G","G46": "G","G47": "G",
    "H49": "H","H50": "H","H51": "H","H52": "H","H53": "H",
    "I": "I","J58": "J","J59_60": "J","J61": "J","J62_63": "J",
    "K64": "K","K65": "K","K66": "K",
    "L": "L","M69_70": "M","M71": "M","M72": "M","M73": "M","M74_75": "M",
    "N77": "N","N78": "N","N79": "N","N80T82": "N",
    "O84": "O","P85": "P","Q86": "Q","Q87_88": "Q",
    "R90T92": "R","R93": "R",
    "S94": "S","S95": "S","S96": "S",
    "T": "T","U": "U"
}


# -------------------------
# HELPERS
# -------------------------
def _to_numeric(df):
    return df.replace(":", np.nan).astype(float)


def _to_display(df):
    return df.where(~df.isna(), ":")


# -------------------------
# IMPUTATION
# -------------------------
def impute_missing(cap_64_num, cap_df_num, va_df_num, country_code, all_processed):
    """
    Impute missing rows in cap_64_num using:
      - AGG_LEVEL_1_MAPPING first (if aggregate exists in cap_df_num)
      - else AGG_LEVEL_2_MAPPING
    Uses donor CI values from all_processed[donor]['CI'] keyed by (industry, year).
    Steps follow 3a-3e from the spec.
    """

    # 1) Build mapping: aggregate_bucket -> list of missing ind64 that map to it
    grouped_missing = {}  # agg_bucket -> list of missing inds
    for ind in INDUSTRIES_64:
        # consider ind missing if all years are NaN
        if cap_64_num.loc[ind].isna().all():
            # check level1
            if ind in AGG_LEVEL_1_MAPPING:
                agg = AGG_LEVEL_1_MAPPING[ind]
                # only use level1 if aggregate exists in cap_df_num index and has at least one non-NaN
                if agg in cap_df_num.index and not cap_df_num.loc[agg].isna().all():
                    grouped_missing.setdefault(agg, []).append(ind)
                    continue
            # fallback to level2 (guaranteed coverage)
            agg2 = AGG_LEVEL_2_MAPPING.get(ind)
            if agg2 is None:
                # Should not happen, but guard:
                agg2 = ind
            grouped_missing.setdefault(agg2, []).append(ind)

    # Sort groups by specificity: prefer level1 (has '-') before broad level2 single-letter buckets
    # This ensures smaller aggregations are imputed before broad ones.
    def agg_specificity_key(x):
        # put strings with '-' or '_' first (more specific)
        return (0 if ("-" in x or "_" in x) else 1, x)

    sorted_groups = sorted(grouped_missing.items(), key=lambda kv: agg_specificity_key(kv[0]))

    # 2) Impute group by group
    for agg, miss_inds in sorted_groups:
        donors = DONORS.get(country_code, [])  # may be empty

        for year in YEARS_STR:
            # 3a: find aggregate total from cap_df_num (agg must be present in cap_df_num)
            if agg not in cap_df_num.index:
                # if the aggregate itself is not present in cap_df_num, we cannot use it -> skip
                continue
            total_agg = cap_df_num.loc[agg, year]
            if pd.isna(total_agg):
                continue

            # sum of already-present members of this agg (only among the 64-level constituents)
            # Need the list of members for this agg: find inds in INDUSTRIES_64 that map to this agg via level1/level2 logic
            members = [i for i in INDUSTRIES_64 if (
                (i in AGG_LEVEL_1_MAPPING and AGG_LEVEL_1_MAPPING[i] == agg) or
                (i in AGG_LEVEL_2_MAPPING and AGG_LEVEL_2_MAPPING[i] == agg) or
                (i == agg)
            )]

            # existing sum of K among members excluding the ones we're about to impute
            existing_sum = 0.0
            for m in members:
                if m in miss_inds:
                    continue
                val = cap_64_num.loc[m, year]
                if not pd.isna(val):
                    existing_sum += val

            missing_total = total_agg - existing_sum
            if pd.isna(missing_total) or missing_total <= 0:
                continue  # nothing to impute or impossible

            # 3b & 3c: for each missing industry, estimate K_i = VA_i * avg_donor_CI_i
            estimates = {}
            for m in miss_inds:
                va_m = va_df_num.loc[m, year]
                # if VA is missing or non-positive, skip this industry
                if pd.isna(va_m) or va_m <= 0:
                    estimates[m] = 0.0
                    continue

                # collect donor CI values for this particular industry m (donors' CI for same 64-industry)
                donor_cis = []
                for d in donors:
                    if d not in all_processed:
                        continue
                    donor_ci = all_processed[d]["CI"].get((m, year))
                    if donor_ci is None or pd.isna(donor_ci):
                        continue
                    # filter abnormal values as specified (<0 or >100)
                    if donor_ci < 0 or donor_ci > 100:
                        continue
                    donor_cis.append(donor_ci)

                if len(donor_cis) == 0:
                    # if no donor CI for this industry, we cannot estimate this industry's K by donor CI
                    estimates[m] = 0.0
                else:
                    avg_ci_m = float(np.mean(donor_cis))
                    estimates[m] = va_m * avg_ci_m

            sum_est_pos = sum(v for v in estimates.values() if v > 0)
            if sum_est_pos <= 0:
                # no positive estimates to scale - skip
                continue

            # 3d scale factor
            scale = missing_total / sum_est_pos

            # 3e apply scaled estimates
            for m, est in estimates.items():
                if est <= 0:
                    # leave as NaN or 0? we will set to NaN (so it becomes ":" later)
                    continue
                cap_64_num.loc[m, year] = est * scale

    return cap_64_num


# -------------------------
# MAIN PROCESSING FUNCTION
# -------------------------
def process_country(excel_path, country_code, all_processed):
    cap_raw_np = pd.read_excel(excel_path, sheet_name=country_code, usecols="C:J",
                               skiprows=11, nrows=91, header=None).to_numpy()
    va_raw_np = pd.read_excel(excel_path, sheet_name=country_code, usecols="Q:X",
                              skiprows=11, nrows=64, header=None).to_numpy()

    cap_df = pd.DataFrame(cap_raw_np, index=INDUSTRIES_91, columns=YEARS_STR)
    va_df = pd.DataFrame(va_raw_np, index=INDUSTRIES_64, columns=YEARS_STR)

    cap_df_num = _to_numeric(cap_df)
    va_df_num = _to_numeric(va_df)

    cap_64_num = pd.DataFrame(index=INDUSTRIES_64, columns=YEARS_STR, dtype=float)

    for src, tgt in MAPPING_91_TO_64.items():
        if src in cap_df_num.index:
            cap_64_num.loc[tgt] = cap_df_num.loc[src].values

    # ---------------------------
    # IMPUTATION INSERTED HERE
    # ---------------------------
    cap_64_num = impute_missing(cap_64_num, cap_df_num, va_df_num, country_code, all_processed)

    # Compute CI
    ci_num = cap_64_num.div(va_df_num).mask(va_df_num == 0, 0)

    # Save CI into dictionary for donor use
    ci_dict = {(ind, y): ci_num.loc[ind, y] for ind in INDUSTRIES_64 for y in YEARS_STR}

    # Store for future donor access
    all_processed[country_code] = {"CI": ci_dict}

    # Convert back and build final output
    cap_64_disp = _to_display(cap_64_num)
    va_disp = _to_display(va_df_num)
    ci_disp = _to_display(ci_num)

    combined = pd.DataFrame({"Industry": INDUSTRIES_64})

    for y in YEARS_STR:
        combined[f"CS_{y}"] = cap_64_disp[y].values

    combined[""] = ""

    for y in YEARS_STR:
        combined[f"VA_{y}"] = va_disp[y].values

    combined["  "] = ""

    for y in YEARS_STR:
        combined[f"CI_{y}"] = ci_disp[y].values

    return combined


# -------------------------
# CLI-LIKE MAIN
# -------------------------
if __name__ == "__main__":
    excel_path = "/Users/nikhil/Documents/Thesis/Capital/0_NetCapitalStock_input.xlsx"

    country_codes = [
        "CZ", "DK", "FI", "SK", "AT", "BG", "GR", "LV", "GB",
        "NO", "SE",
        "US",
        "DE", "IE", "LU",
        "BE", "FR", "NL",
        "IT", "ES", "PT",
        "EE", "LT", "HR",
        "SI", "CY", "MT",
        "HU", "PL", "RO",
        "CA", "AU", "KR", "JP", "IN",
        "CN"
    ]

    all_processed = {}  # donors reference this

    output_file = "/Users/nikhil/Documents/Thesis/Capital/0_NetCapitalStock_CN.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for cc in country_codes:
            print(f"Processing {cc} ...")
            out_df = process_country(excel_path, cc, all_processed)
            if cc == "CN":
                out_df.to_excel(writer, sheet_name=cc, index=False)
            print(f"  → Done {cc}")

    print("All countries processed.")
