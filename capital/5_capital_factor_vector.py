import pandas as pd


def build_final_sheet_from_processed():
    # Input (processed) workbook created previously
    input_path = "/Users/nikhil/Documents/Thesis/Capital/PROCESSED_NetCapitalStock.xlsx"
    # Output workbook to create (single sheet "Final")
    output_path = "/Users/nikhil/Documents/Thesis/Capital/CAPITAL_v2_figaro2025.xlsx"

    countries_order = [
        "AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CN", "CY", "CZ", "DE", "DK",
        "EE", "ES", "FI", "FIGW1", "FR", "GB", "GR", "HR", "HU", "ID", "IE", "IN",
        "IT", "JP", "KR", "LT", "LU", "LV", "MT", "MX", "NL", "NO", "PL", "PT", "RO",
        "RU", "SA", "SE", "SI", "SK", "TR", "US", "ZA"
    ]

    years = [str(y) for y in range(2010, 2021 + 1)]
    cs_cols = [f"CS_{y}" for y in years]

    rows_out = []  # list of dicts -> will become DataFrame rows

    print("Reading processed workbook:", input_path)
    for cc in countries_order:
        try:
            df = pd.read_excel(input_path, sheet_name=cc)
        except Exception as e:
            print(f"[WARNING] Could not read sheet '{cc}': {e}. Skipping.")
            continue

        # Check presence of Industry column
        if "Industry" not in df.columns:
            print(f"[WARNING] Sheet '{cc}' missing 'Industry' column. Skipping.")
            continue

        # Check CS columns presence
        missing_cs = [c for c in cs_cols if c not in df.columns]
        if missing_cs:
            print(f"[WARNING] Sheet '{cc}' missing CS columns: {missing_cs}. Will use available columns only.")

        # Use the industry order present in the sheet (preserve order)
        for _, row in df.iterrows():
            industry = row.get("Industry")
            if pd.isna(industry):
                # skip empty industry rows just in case
                continue

            factor_key = f"{cc}_{industry}"

            # build output row dictionary
            out_row = {"factor_key": factor_key}
            for y, col in zip(years, cs_cols):
                if col in df.columns:
                    val = row[col]
                    # keep ":" as-is, keep NaN as empty string (or keep NaN if you prefer)
                    if isinstance(val, str) and val.strip() == ":":
                        out_row[y] = ":"
                    else:
                        # attempt to preserve numeric values; if NaN, leave as empty string
                        try:
                            if pd.isna(val):
                                out_row[y] = ""
                            else:
                                out_row[y] = float(val)
                        except Exception:
                            # if any non-numeric junk, keep raw representation
                            out_row[y] = val
                else:
                    # column missing in sheet -> empty
                    out_row[y] = ""

            rows_out.append(out_row)

        print(f"  → processed {cc} ({len(df)} rows)")

    # Build final DataFrame in same column order as requested
    final_cols = ["factor_key"] + years
    final_df = pd.DataFrame(rows_out, columns=final_cols)

    # Write output workbook with single sheet "Final"
    print("Writing final output to:", output_path)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        final_df.to_excel(writer, sheet_name="Final", index=False)

    print("Done. Final sheet rows:", len(final_df))


if __name__ == "__main__":
    build_final_sheet_from_processed()
