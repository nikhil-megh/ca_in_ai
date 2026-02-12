import pandas as pd


def validate_capital_stock():
    excel_path = "/Users/nikhil/Documents/Thesis/Capital/PROCESSED_NetCapitalStock.xlsx"

    countries_order = [
        "AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CN", "CY", "CZ", "DE", "DK",
        "EE", "ES", "FI", "FIGW1", "FR", "GB", "GR", "HR", "HU", "ID", "IE", "IN",
        "IT", "JP", "KR", "LT", "LU", "LV", "MT", "MX", "NL", "NO", "PL", "PT", "RO",
        "RU", "SA", "SE", "SI", "SK", "TR", "US", "ZA"
    ]

    years = [str(y) for y in range(2010, 2021 + 1)]
    cs_cols = [f"CS_{y}" for y in years]

    print("\n=== VALIDATION START ===\n")

    for cc in countries_order:
        try:
            df = pd.read_excel(excel_path, sheet_name=cc)
        except Exception as e:
            print(f"[ERROR] Could not read sheet for {cc}: {e}")
            continue

        # ensure required columns exist
        missing_cols = [c for c in cs_cols if c not in df.columns]
        if missing_cols:
            print(f"[ERROR] Missing CS columns in {cc}: {missing_cols}")
            continue

        for _, row in df.iterrows():
            industry = row["Industry"]

            for y in years:
                col = f"CS_{y}"
                value = row[col]

                # check for ":"
                if isinstance(value, str) and value.strip() == ":":
                    print(f"[MISSING] {cc} | {industry} | {y} | value=':'")
                    continue

                # check float conversion
                try:
                    v = float(value)
                except:
                    print(f"[NON-FLOAT] {cc} | {industry} | {y} | value='{value}'")
                    continue

                # check negative
                if v < 0:
                    print(f"[NEGATIVE] {cc} | {industry} | {y} | value={v}")

    print("\n=== VALIDATION COMPLETE ===\n")


if __name__ == "__main__":
    validate_capital_stock()
