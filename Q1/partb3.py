from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SALES_DIR = Path(
    r"C:\Users\ub02-glab-005\Downloads\data_2\data\sales"
)


# ============================================================
# NORMALIZE ONE SALES FILE
# ============================================================

def normalize_file(file_path: Path) -> pd.DataFrame:

    # --------------------------------------------------------
    # Determine store and business date from filename
    # Example:
    # SALES_S01_20240101.csv
    # --------------------------------------------------------

    name = file_path.stem

    parts = name.split("_")

    store_id = parts[1]
    date_string = parts[2]

    business_date = pd.to_datetime(
        date_string,
        format="%Y%m%d"
    ).date()

    # --------------------------------------------------------
    # Detect file format from the header
    # --------------------------------------------------------

    with open(
        file_path,
        "r",
        encoding="utf-8-sig"
    ) as f:
        header = f.readline().strip()

    # --------------------------------------------------------
    # S06-S09
    # Semicolon separated
    # --------------------------------------------------------

    if ";" in header:

        df = pd.read_csv(
            file_path,
            sep=";",
            encoding="utf-8-sig"
        )

        df = df.rename(
            columns={
                "item_code": "product_code",
                "quantity": "qty",
                "rate": "unit_price",
                "type": "line_type",
                "txn_time": "ts",
            }
        )

        df["ts"] = pd.to_datetime(
            df["ts"],
            format="%d-%m-%Y %H:%M:%S"
        )

    # --------------------------------------------------------
    # S10-S12
    # Comma separated
    # Timestamp is epoch seconds
    # --------------------------------------------------------

    elif header.startswith("ts,bill_no"):

        df = pd.read_csv(
            file_path,
            encoding="utf-8-sig"
        )

        df["ts"] = pd.to_datetime(
            df["ts"],
            unit="s",
            utc=True
        )

    # --------------------------------------------------------
    # S01-S05
    # Standard comma-separated format
    # --------------------------------------------------------

    else:

        df = pd.read_csv(
            file_path,
            encoding="utf-8-sig"
        )

        df["ts"] = pd.to_datetime(
            df["ts"]
        )

    # --------------------------------------------------------
    # Add metadata
    # --------------------------------------------------------

    df["store_id"] = store_id
    df["business_date"] = pd.to_datetime(
        business_date
    )

    df["source_file"] = file_path.name

    # --------------------------------------------------------
    # Select canonical schema
    # --------------------------------------------------------

    df = df[
        [
            "store_id",
            "business_date",
            "ts",
            "bill_no",
            "line_no",
            "product_code",
            "qty",
            "unit_price",
            "line_type",
            "source_file",
        ]
    ]

    return df


# ============================================================
# TEST THREE BILLING FORMATS
# ============================================================

if __name__ == "__main__":

    test_files = [
        SALES_DIR / "SALES_S01_20240101.csv",
        SALES_DIR / "SALES_S06_20240101.csv",
        SALES_DIR / "SALES_S10_20240101.csv",
    ]

    for file_path in test_files:

        print("\n" + "=" * 70)
        print(f"Testing: {file_path.name}")
        print("=" * 70)

        try:

            df = normalize_file(file_path)

            print(f"Rows: {len(df)}")
            print("\nColumns:")
            print(list(df.columns))

            print("\nFirst 3 rows:")
            print(df.head(3).to_string(index=False))

            print("\nLine types:")
            print(df["line_type"].value_counts().to_string())

            print("\nData types:")
            print(df.dtypes)

            print("\nSUCCESS")

        except Exception as e:

            print(f"\nFAILED: {e}")