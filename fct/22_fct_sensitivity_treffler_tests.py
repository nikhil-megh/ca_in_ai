import os
from pathlib import Path
import numpy as np
import pandas as pd

# ======================== CONFIGURATION ========================

# --- FIGARO
FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/IOT_v2"
GO_FILE = "/Users/nikhil/Documents/Thesis/Figaro/FIGARO_GrossOutput_2010_2021.xlsx"

# --- inputs already in your pipeline
SC_FILE = "/Users/nikhil/Documents/Thesis/FCT/Consumption_Shares/consumption_shares.xlsx"
FACTOR_ENDOWMENTS_DIR = "/Users/nikhil/Documents/Thesis/FCT/Factor_Endowments"

# --- NEW consolidated output base
BASE_DIR = "/Users/nikhil/Documents/Thesis/FCT/Sensitivity_HOV"

# --- factors source files (same as your factor-vector generator)
FACTOR_FILES = {
    "labour": "/Users/nikhil/Documents/Thesis/Labour/EMP_figaro2025.xlsx",
    "capital": "/Users/nikhil/Documents/Thesis/Capital/CAPITAL_figaro2025.xlsx",
    "pct_all_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_all_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
}

YEARS = list(range(2010, 2022))

# --- constants
N_COUNTRIES = 46
N_INDUSTRIES = 64
N_SECTORS = N_COUNTRIES * N_INDUSTRIES  # 2944
N_FINAL_DEMAND = 5

COUNTRIES = [
    "AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CN", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FIGW1", "FR",
    "GB", "GR", "HR", "HU", "ID", "IE", "IN", "IT", "JP", "KR", "LT", "LU", "LV", "MT", "MX", "NL", "NO", "PL",
    "PT", "RO", "RU", "SA", "SE", "SI", "SK", "TR", "US", "ZA"
]

INDUSTRY_CODES = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]

INDUSTRY_NAMES = {
    "A01": "Agriculture", "A02": "Forestry", "A03": "Fishing",
    "B": "Mining", "C10T12": "Food", "C13T15": "Textiles",
    "C16": "Wood", "C17": "Paper", "C18": "Printing",
    "C19": "Petroleum", "C20": "Chemicals", "C21": "Pharmaceuticals",
    "C22": "Rubber/Plastics", "C23": "Non-Metallic Minerals", "C24": "Basic Metals",
    "C25": "Fabricated Metals", "C26": "Electronics", "C27": "Electrical Equipment",
    "C28": "Machinery", "C29": "Motor Vehicles", "C30": "Other Transport",
    "C31_32": "Furniture", "C33": "Repair", "D35": "Electricity",
    "E36": "Water", "E37T39": "Waste", "F": "Construction",
    "G45": "Motor Vehicle Trade", "G46": "Wholesale", "G47": "Retail",
    "H49": "Land Transport", "H50": "Water Transport", "H51": "Air Transport",
    "H52": "Warehousing", "H53": "Postal", "I": "Accommodation",
    "J58": "Publishing", "J59_60": "Media", "J61": "Telecommunications",
    "J62_63": "IT Services", "K64": "Financial Services", "K65": "Insurance",
    "K66": "Financial Support", "L": "Real Estate", "M69_70": "Legal/Accounting",
    "M71": "Architecture", "M72": "R&D", "M73": "Advertising",
    "M74_75": "Professional Services", "N77": "Rental", "N78": "Employment",
    "N79": "Travel Agency", "N80T82": "Security", "O84": "Government",
    "P85": "Education", "Q86": "Health", "Q87_88": "Social Work",
    "R90T92": "Arts", "R93": "Sports", "S94": "Membership Orgs",
    "S95": "Repair Services", "S96": "Personal Services", "T": "Households",
    "U": "Extraterritorial"
}

# --- sector keys used everywhere (must match your factor_key ordering)
SECTOR_KEYS = [f"{COUNTRIES[i // N_INDUSTRIES]}_{INDUSTRY_CODES[i % N_INDUSTRIES]}"
               for i in range(N_SECTORS)]

# --- output structure
MATRICES_DIR = os.path.join(BASE_DIR, "Matrices")
NET_TRADE_DIR = os.path.join(MATRICES_DIR, "Net_Trade_Vectors")
FACTOR_VEC_DIR = os.path.join(MATRICES_DIR, "Factor_Vectors")
TECH_DIR = os.path.join(MATRICES_DIR, "Technical_Coefficient_Matrix")
LEONTIEF_DIR = os.path.join(MATRICES_DIR, "Leontief_Inverse_Matrix")
CONSUMPTION_DIR = os.path.join(MATRICES_DIR, "Consumption")
MEASURED_DIR = os.path.join(BASE_DIR, "Measured_FCT")
PREDICTED_DIR = os.path.join(BASE_DIR, "Predicted_FCT")
TESTS_DIR = os.path.join(BASE_DIR, "Consumption_Similarity_Tests")


def ensure_dirs():
    for p in [
        BASE_DIR, MATRICES_DIR, NET_TRADE_DIR, FACTOR_VEC_DIR, TECH_DIR, LEONTIEF_DIR,
        CONSUMPTION_DIR, MEASURED_DIR, PREDICTED_DIR, TESTS_DIR
    ]:
        Path(p).mkdir(parents=True, exist_ok=True)


# ======================== STEP 0: HELPERS ========================

def load_figaro_numeric(year) -> np.ndarray:
    fp = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
    df = pd.read_csv(fp, header=None)
    df_numeric = df.apply(pd.to_numeric, errors="coerce")
    df_numeric = df_numeric.dropna(how="all", axis=0).dropna(how="all", axis=1)
    return df_numeric.to_numpy(dtype=float)


def load_IIO_matrix_with_labels(year) -> pd.DataFrame:
    """Matches your working L-generation script: take labelled 2944x2944 block."""
    fp = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
    df = pd.read_csv(fp, header=None)

    row_labels = df.iloc[1:N_SECTORS + 1, 0].values
    col_labels = df.iloc[0, 1:N_SECTORS + 1].values

    iio_numeric = df.iloc[1:N_SECTORS + 1, 1:N_SECTORS + 1].apply(pd.to_numeric, errors="coerce")
    iio_numeric.index = row_labels
    iio_numeric.columns = col_labels

    return iio_numeric


def load_go_df() -> pd.DataFrame:
    go_df = pd.read_excel(GO_FILE, index_col=0)
    go_df.columns = go_df.columns.map(str)
    return go_df


def load_shares(year) -> pd.Series:
    sc = pd.read_excel(SC_FILE)
    sc.set_index(sc.columns[0], inplace=True)
    s = sc[str(year)]
    # enforce country order
    return s.reindex(COUNTRIES)


def get_factor_tests_dir(base_tests_dir: str, factor_name: str) -> str:
    p = os.path.join(base_tests_dir, factor_name)
    Path(p).mkdir(parents=True, exist_ok=True)
    return p


def year_excel_path(factor_tests_dir: str, year: int) -> str:
    return os.path.join(factor_tests_dir, f"consumption_similarity_{year}.xlsx")


def consolidated_excel_path(factor_tests_dir: str) -> str:
    return os.path.join(factor_tests_dir, "consumption_similarity_ALL_YEARS.xlsx")


def write_year_excel(
    out_path: str,
    table2: pd.DataFrame,
    table3: pd.DataFrame,
    country_check: pd.DataFrame
):
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        table2.to_excel(writer, sheet_name="Table2_Errors", index=False)
        table3.to_excel(writer, sheet_name="Table3_Variance", index=False)
        country_check.to_excel(writer, sheet_name="Country_Check", index=False)


def write_consolidated_excel(
    out_path: str,
    table2_all: pd.DataFrame,
    table3_all: pd.DataFrame,
    country_check_all: pd.DataFrame
):
    # Ensure year columns exist (they should)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        table2_all.to_excel(writer, sheet_name="Table2_Errors", index=False)
        table3_all.to_excel(writer, sheet_name="Table3_Variance", index=False)
        country_check_all.to_excel(writer, sheet_name="Country_Check", index=False)


# ======================== STEP 1: NET TRADE MATRIX T (2944 x 46) ========================

def compute_net_trade_T(year) -> pd.DataFrame:
    """
    Reproduces your net-trade-vector script exactly:
    - M = FIGARO numeric matrix
    - drop last 6 VA rows
    - use intermediate (2944x2944) and final demand (2944x230)
    - aggregate destination at country level (sum 64 cols, sum 5 cols)
    - zero diagonal blocks
    - exports = row sums
    - negate imports and replace diagonal with exports
    """
    M = load_figaro_numeric(year)
    M = M[:-6, :]  # drop VA rows (as in your code)

    inter_end = N_SECTORS
    fd_start, fd_end = inter_end, inter_end + N_COUNTRIES * N_FINAL_DEMAND

    inter_matrix = M[:, :inter_end]  # 2944x2944
    fd_matrix = M[:, fd_start:fd_end]  # 2944x230

    # aggregate intermediate to country destinations
    inter_country = np.hstack([
        inter_matrix[:, i * N_INDUSTRIES:(i + 1) * N_INDUSTRIES].sum(axis=1, keepdims=True)
        for i in range(N_COUNTRIES)
    ])

    # aggregate final demand to country destinations
    fd_country = np.hstack([
        fd_matrix[:, i * N_FINAL_DEMAND:(i + 1) * N_FINAL_DEMAND].sum(axis=1, keepdims=True)
        for i in range(N_COUNTRIES)
    ])

    total_use = inter_country + fd_country  # 2944x46

    # zero diagonal (intra-country)
    for i in range(N_COUNTRIES):
        rs, re = i * N_INDUSTRIES, (i + 1) * N_INDUSTRIES
        total_use[rs:re, i] = 0

    export_col = total_use.sum(axis=1, keepdims=True)  # 2944x1
    total_use_neg = -1 * total_use

    # replace diagonal with exports
    for i in range(N_COUNTRIES):
        rs, re = i * N_INDUSTRIES, (i + 1) * N_INDUSTRIES
        total_use_neg[rs:re, i] = export_col[rs:re, 0]

    return pd.DataFrame(total_use_neg, index=SECTOR_KEYS, columns=COUNTRIES)


# ======================== STEP 2: FACTOR VECTORS E (6 x 2944) ========================

def build_factor_vectors_yearwise():
    """
    Same logic as your factor-vectors generator: read each xlsx "Final", then output factors_{year}.csv
    """
    # Load all factor sheets once
    data = {}
    for factor_name, filepath in FACTOR_FILES.items():
        df = pd.read_excel(filepath, sheet_name="Final")
        if df.columns[0] != "factor_key":
            df.rename(columns={df.columns[0]: "factor_key"}, inplace=True)
        df.set_index("factor_key", inplace=True)
        df.columns = df.columns.map(str)
        data[factor_name] = df

    # build yearwise
    for year in YEARS:
        y = str(year)
        rows = []
        for factor_name, df in data.items():
            if y not in df.columns:
                raise ValueError(f"Year {y} missing in factor: {factor_name}")
            s = df[y]
            s.name = factor_name
            rows.append(s)

        out_df = pd.DataFrame(rows)

        # ensure ordering of sector keys (critical)
        out_df = out_df.reindex(columns=SECTOR_KEYS)

        out_path = os.path.join(FACTOR_VEC_DIR, f"factors_{year}.csv")
        out_df.to_csv(out_path, float_format="%.6f")


# ======================== STEP 3: TECH COEFFICIENTS B and LEONTIEF L ========================

def compute_B_and_L(year, go_df):
    """
    Matches your working L-generation script:
      B = IIO @ inv(diag(GO + eps))
      L = inv(I - B)
    """
    IIO = load_IIO_matrix_with_labels(year)

    if str(year) not in go_df.columns:
        raise KeyError(f"Year {year} missing in GO dataset!")

    GO = go_df[str(year)].values
    eps_vec = np.full_like(GO, 1e-8)
    GOnz = GO + eps_vec

    B = IIO.values @ np.linalg.inv(np.diag(GOnz))
    B_df = pd.DataFrame(B, index=IIO.index, columns=IIO.index)

    I = np.identity(B.shape[0])
    L = np.linalg.inv(I - B)
    L_df = pd.DataFrame(L, index=IIO.index, columns=IIO.index)

    # save
    B_df.to_csv(os.path.join(TECH_DIR, f"technical_coefficients_matrix_{year}.csv"))
    L_df.to_csv(os.path.join(LEONTIEF_DIR, f"leontief_matrix_{year}.csv"))

    return B_df, L_df


# ======================== STEP 4: CONSUMPTION MATRIX C (2944 x 46) ========================

def compute_consumption_C(year) -> pd.DataFrame:
    """
    Same as your earlier approach:
      C[:, i] = sum across 5 FD columns for country i
    """
    M = load_figaro_numeric(year)
    M = M[:-6, :]  # producer rows only

    inter_end = N_SECTORS
    fd_start = inter_end
    fd_end = inter_end + N_COUNTRIES * N_FINAL_DEMAND

    fd_matrix = M[:, fd_start:fd_end]  # 2944 x 230

    C = np.zeros((N_SECTORS, N_COUNTRIES), dtype=float)
    for c in range(N_COUNTRIES):
        s = c * N_FINAL_DEMAND
        e = (c + 1) * N_FINAL_DEMAND
        C[:, c] = fd_matrix[:, s:e].sum(axis=1)

    return pd.DataFrame(C, index=SECTOR_KEYS, columns=COUNTRIES)


# ======================== STEP 5: MEASURED FCT (correct A = D L) ========================

def compute_measured_fct(year, go_df) -> pd.DataFrame:
    """
    Matches your working measured FCT script:
      E = factors_{year}  (6x2944)
      D = E / GO
      A = D L
      F = A T
    """
    E = pd.read_csv(os.path.join(FACTOR_VEC_DIR, f"factors_{year}.csv"), index_col=0)
    L = pd.read_csv(os.path.join(LEONTIEF_DIR, f"leontief_matrix_{year}.csv"), index_col=0)
    T = pd.read_csv(os.path.join(NET_TRADE_DIR, f"net_trade_vector_{year}.csv"), index_col=0)

    # GO series aligned to sector keys
    GO = go_df[str(year)]
    GO = GO.reindex(E.columns)  # align
    GO_series = GO.replace(0, np.nan)

    if not (list(E.columns) == list(L.index) == list(T.index)):
        raise ValueError(f"Sector alignment mismatch in year {year}!")

    D = E.div(GO_series).fillna(0.0)
    A = D.values @ L.values  # (6x2944)

    F = A @ T.values  # (6x46)
    F_df = pd.DataFrame(F, index=E.index, columns=T.columns)

    # save
    F_df.to_csv(os.path.join(MEASURED_DIR, f"measured_fct_{year}.csv"))
    return F_df, pd.DataFrame(A, index=E.index, columns=E.columns)  # return A as well


# ======================== STEP 6: PREDICTED FCT (Vi - si Vw) ========================

def compute_predicted_fct(year) -> pd.DataFrame:
    """
    Matches your predicted FCT script:
      Vc (6x46) from factor_endowments_{year}.csv
      Fc = Vc - s_i * Vw
    """
    sc = pd.read_excel(SC_FILE)
    sc.set_index(sc.columns[0], inplace=True)

    Vc = pd.read_csv(os.path.join(FACTOR_ENDOWMENTS_DIR, f"factor_endowments_{year}.csv"), index_col=0)

    Sc_year = sc[str(year)].loc[Vc.columns]  # align countries

    Sc_matrix = np.tile(Sc_year.values, (Vc.shape[0], 1))
    Vw = Vc.sum(axis=1).values.reshape(-1, 1)
    Vw_matrix = np.tile(Vw, (1, Vc.shape[1]))

    Fc = Vc.values - (Sc_matrix * Vw_matrix)
    Fc_df = pd.DataFrame(Fc, index=Vc.index, columns=Vc.columns)

    Fc_df.to_csv(os.path.join(PREDICTED_DIR, f"predicted_fct_{year}.csv"))
    return Fc_df


# ======================== STEP 7: TZ SECTION 7.1 ERRORS + TABLES ========================

def compute_epsilons_for_factor(
    year: int,
    A_factor_by_sector: pd.Series,   # A.loc[factor_name], indexed by sector key
    C: pd.DataFrame,                 # (2944 x 46)
    s: pd.Series,                    # (46,)
    countries: list                  # COUNTRIES
) -> pd.DataFrame:
    """
    εgij = Agj(Cgij - si*Cgwj) for a specific factor.
    """
    Cw = C.sum(axis=1)  # world consumption per sector

    rows = []
    for sector in C.index:
        parts = sector.split("_")
        producer = parts[0]
        industry = "_".join(parts[1:])

        Agj = float(A_factor_by_sector.loc[sector])
        Cgwj = float(Cw.loc[sector])

        for consumer in countries:
            si = float(s.loc[consumer])
            Cgij = float(C.loc[sector, consumer])
            eps = Agj * (Cgij - si * Cgwj)

            rows.append({
                "year": year,
                "consumer": consumer,
                "producer": producer,
                "industry": industry,
                "industry_name": INDUSTRY_NAMES.get(industry, industry),
                "sector": sector,
                "Agj": Agj,
                "Cgij": Cgij,
                "Cgwj": Cgwj,
                "si": si,
                "error": eps,
                "is_diagonal": (consumer == producer)
            })

    return pd.DataFrame(rows)


def make_table2_top_errors(errors_df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    """
    Table 2 style:
      - Top N diagonal errors by raw level (descending)
      - Top N off-diagonal errors by absolute value (descending)

    Output is a single sheet-friendly stacked table with YEAR included.
    """
    df = errors_df.copy().reset_index(drop=True)

    diag = df[df["is_diagonal"]].copy().reset_index(drop=True)
    off = df[~df["is_diagonal"]].copy().reset_index(drop=True)

    top_diag = diag.nlargest(top_n, "error")[["year", "consumer", "industry_name", "error"]].copy()
    top_diag.rename(columns={"consumer": "country"}, inplace=True)
    top_diag["panel"] = "DIAGONAL (i=j)"
    top_diag = top_diag[["panel", "year", "country", "industry_name", "error"]]

    off["abs_error"] = off["error"].abs()
    top_off = off.nlargest(top_n, "abs_error")[["year", "consumer", "producer", "industry_name", "error"]].copy()
    top_off["panel"] = "OFF-DIAGONAL (i≠j)"
    top_off = top_off[["panel", "year", "consumer", "producer", "industry_name", "error"]]

    # Stack into one table
    # Make columns consistent via union (off has producer; diag doesn't)
    top_diag["producer"] = ""
    top_diag.rename(columns={"country": "consumer"}, inplace=True)
    stacked = pd.concat(
        [top_diag, top_off],
        ignore_index=True
    )

    # Sort within each panel (nice for read)
    stacked["abs_error"] = stacked["error"].abs()
    stacked = stacked.sort_values(["panel", "abs_error"], ascending=[True, False]).drop(columns=["abs_error"])
    stacked.reset_index(drop=True, inplace=True)

    # Clean rounding (optional)
    # stacked["error"] = stacked["error"].round(6)

    return stacked


def make_table3_industry_variance(errors_df: pd.DataFrame) -> pd.DataFrame:
    """
    Table 3 style:
      σ_g^2 = var(ε_gij) for each industry (within-year).
      Prop_i=j = Σ_j(ε_gjj - ε_g)^2 / Σ_ij(ε_gij - ε_g)^2

    Includes a YEAR column.
    """
    df = errors_df.copy()

    stats = []
    for code in INDUSTRY_CODES:
        sub = df[df["industry"] == code].copy()
        if sub.empty:
            continue

        year_val = int(sub["year"].iloc[0])
        var = sub["error"].var()
        mean = sub["error"].mean()
        diag = sub[sub["is_diagonal"]]

        diag_ss = ((diag["error"] - mean) ** 2).sum()
        total_ss = ((sub["error"] - mean) ** 2).sum()
        prop = (diag_ss / total_ss) if total_ss > 0 else 0.0

        stats.append({
            "year": year_val,
            "Industry": INDUSTRY_NAMES.get(code, code),
            "Code": code,
            "σ_g²": var,
            "Prop_i=j": prop,
            "N_obs": len(sub),
            "N_diag": len(diag)
        })

    out = pd.DataFrame(stats).sort_values("σ_g²", ascending=False).reset_index(drop=True)
    out["σ_g²"] = out["σ_g²"].round(6)
    out["Prop_i=j"] = out["Prop_i=j"].round(6)
    return out


def country_identity_check_for_factor(
    year: int,
    factor_name: str,
    measured_fct: pd.DataFrame,   # (factors x countries)
    predicted_fct: pd.DataFrame,  # (factors x countries)
    errors_df: pd.DataFrame,      # epsilons for THIS factor, includes year
    countries: list
) -> pd.DataFrame:
    """
    For the given factor:
      residual_i = Fi_measured - Fi_predicted
      sum_eps_i = ΣjΣg εgij
      difference = |residual_i| - |sum_eps_i|   (as requested)
    """
    if factor_name not in measured_fct.index or factor_name not in predicted_fct.index:
        raise KeyError(f"Expected factor '{factor_name}' in both measured and predicted FCT.")

    Fi = measured_fct.loc[factor_name].reindex(countries)
    Pi = predicted_fct.loc[factor_name].reindex(countries)
    residual = Fi - Pi

    sum_eps = errors_df.groupby("consumer")["error"].sum().reindex(countries).fillna(0.0)

    out = pd.DataFrame({
        "year": year,
        "country": countries,
        "Fi_measured": Fi.values,
        "Fi_predicted_(Vi-siVw)": Pi.values,
        "Residual_(Measured-Predicted)": residual.values,
        "Sum_eps_(ΣjΣg εgij)": sum_eps.values,
    })

    out["Difference_(|Residual|-|Sum_eps|)"] = out["Residual_(Measured-Predicted)"].abs() - out["Sum_eps_(ΣjΣg εgij)"].abs()

    return out


# ======================== MAIN ========================

def run():
    ensure_dirs()

    # Load GO once
    go_df = load_go_df()

    # Build factor vectors once (yearwise CSVs)
    build_factor_vectors_yearwise()
    # Initialize consumption similarity tables
    table2_all = {f: [] for f in FACTOR_FILES.keys()}
    table3_all = {f: [] for f in FACTOR_FILES.keys()}
    check_all = {f: [] for f in FACTOR_FILES.keys()}

    for year in YEARS:
        print(f"\n{'=' * 70}\nYEAR {year}\n{'=' * 70}")

        # 1) Net trade matrix T
        T = compute_net_trade_T(year)
        T.to_csv(os.path.join(NET_TRADE_DIR, f"net_trade_vector_{year}.csv"))

        # 2) B and L
        _, _ = compute_B_and_L(year, go_df)

        # 3) Consumption matrix C
        C = compute_consumption_C(year)
        C.to_csv(os.path.join(CONSUMPTION_DIR, f"consumption_{year}.csv"))

        # 4) Measured FCT and A (= D L)
        measured_fct, A = compute_measured_fct(year, go_df)

        # 5) Predicted FCT
        predicted_fct = compute_predicted_fct(year)

        # 6) Similarity errors for all factors
        s = load_shares(year)
        for factor_name in A.index:  # all 6 factors
            factor_tests_dir = get_factor_tests_dir(TESTS_DIR, factor_name)

            A_factor_by_sector = A.loc[factor_name]  # Series over sectors

            errors_df = compute_epsilons_for_factor(year, A_factor_by_sector, C, s, COUNTRIES)  # no saving

            table2 = make_table2_top_errors(errors_df, top_n=100)
            table3 = make_table3_industry_variance(errors_df)
            check = country_identity_check_for_factor(year, factor_name, measured_fct, predicted_fct, errors_df,
                                                      COUNTRIES)

            # write yearly excel in that factor folder
            write_year_excel(year_excel_path(factor_tests_dir, year), table2, table3, check)

            # accumulate for consolidated (create dicts outside loop)
            table2_all[factor_name].append(table2)
            table3_all[factor_name].append(table3)
            check_all[factor_name].append(check)

        print(f"✅ Completed for : {year}")

    for factor_name in table2_all.keys():
        factor_tests_dir = get_factor_tests_dir(TESTS_DIR, factor_name)

        t2 = pd.concat(table2_all[factor_name], ignore_index=True)
        t3 = pd.concat(table3_all[factor_name], ignore_index=True)
        ck = pd.concat(check_all[factor_name], ignore_index=True)

        write_consolidated_excel(consolidated_excel_path(factor_tests_dir), t2, t3, ck)


if __name__ == "__main__":
    run()
