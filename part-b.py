from pathlib import Path
import hashlib
import pandas as pd

from normalize_sales import normalize_file


# ============================================================
# CONFIGURATION
# ============================================================

SALES_DIR = Path(
    r"C:\Users\ub02-glab-005\Downloads\data_2\data\sales"
)

OUTPUT_DIR = Path("staging/sales")


# ============================================================
# FIND ALL SOURCE FILES
# ============================================================

def find_source_files():
    csv_files = list(SALES_DIR.glob("*.csv"))
    parquet_files = list(SALES_DIR.glob("*.parquet"))

    return sorted(csv_files + parquet_files)


# ============================================================
# NORMALIZE PARQUET FILE
# ============================================================

def normalize_parquet(file_path: Path) -> pd.DataFrame:

    name = file_path.stem
    parts = name.split("_")

    store_id = parts[1]
    date_string = parts[2]

    business_date = pd.to_datetime(
        date_string,
        format="%Y%m%d"
    ).date()

    df = pd.read_parquet(file_path)

    # Normalize possible column names
    df = df.rename(
        columns={
            "item_code": "product_code",
            "quantity": "qty",
            "rate": "unit_price",
            "type": "line_type",
            "txn_time": "ts",
        }
    )

    # Handle timestamp if it is epoch seconds
    if pd.api.types.is_numeric_dtype(df["ts"]):
        df["ts"] = pd.to_datetime(
            df["ts"],
            unit="s",
            utc=True
        )
    else:
        df["ts"] = pd.to_datetime(df["ts"])

    df["store_id"] = store_id

    df["business_date"] = pd.to_datetime(
        business_date
    )

    df["source_file"] = file_path.name

    return df[
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


# ============================================================
# NORMALIZE ANY SOURCE FILE
# ============================================================

def normalize_any_file(file_path: Path) -> pd.DataFrame:

    if file_path.suffix.lower() == ".parquet":
        return normalize_parquet(file_path)

    return normalize_file(file_path)


# ============================================================
# CALCULATE DETERMINISTIC CHECKSUM
# ============================================================

def calculate_checksum(df: pd.DataFrame) -> str:

    checksum_columns = [
        "store_id",
        "business_date",
        "ts",
        "bill_no",
        "line_no",
        "product_code",
        "qty",
        "unit_price",
        "line_type",
    ]

    check_df = df[checksum_columns].copy()

    # Convert everything to deterministic strings
    for column in checksum_columns:
        check_df[column] = check_df[column].astype(str)

    check_df = check_df.sort_values(
        checksum_columns
    )

    data = check_df.to_csv(
        index=False,
        lineterminator="\n"
    ).encode("utf-8")

    return hashlib.sha256(data).hexdigest()


# ============================================================
# MAIN INGESTION
# ============================================================

def main():

    files = find_source_files()

    print("=" * 70)
    print("ANNAPURNA SALES INGESTION")
    print("=" * 70)

    print(f"Source files found: {len(files)}")

    if not files:
        raise RuntimeError("No sales files found.")

    frames = []

    for index, file_path in enumerate(files, start=1):

        try:

            df = normalize_any_file(file_path)

            frames.append(df)

            if index % 250 == 0 or index == len(files):
                print(
                    f"Processed {index}/{len(files)} files"
                )

        except Exception as e:

            print(
                f"ERROR: {file_path.name}: {e}"
            )
            raise

    # --------------------------------------------------------
    # Combine everything
    # --------------------------------------------------------

    all_sales = pd.concat(
        frames,
        ignore_index=True
    )

    print()
    print(f"Rows before deduplication: {len(all_sales):,}")

    # --------------------------------------------------------
    # Remove resent duplicate billing lines
    #
    # A billing line is identified by:
    # store + bill number + line number
    # --------------------------------------------------------

    duplicate_key = [
        "store_id",
        "bill_no",
        "line_no",
    ]

    duplicate_count = all_sales.duplicated(
        subset=duplicate_key
    ).sum()

    print(
        f"Duplicate rows removed: {duplicate_count:,}"
    )

    all_sales = all_sales.drop_duplicates(
        subset=duplicate_key,
        keep="first"
    ).copy()

    # --------------------------------------------------------
    # Sort for deterministic output
    # --------------------------------------------------------

    all_sales = all_sales.sort_values(
        [
            "store_id",
            "business_date",
            "bill_no",
            "line_no",
        ]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Calculate checksum AFTER deduplication
    # --------------------------------------------------------

    checksum = calculate_checksum(all_sales)

    print(
        f"Rows after deduplication: {len(all_sales):,}"
    )

    print(
        f"SHA-256 checksum: {checksum}"
    )

    # --------------------------------------------------------
    # Recreate output directory
    #
    # We overwrite the deterministic partition files rather
    # than appending to them. This is important for
    # idempotency.
    # --------------------------------------------------------

    if OUTPUT_DIR.exists():

        for old_file in OUTPUT_DIR.rglob("*.parquet"):
            old_file.unlink()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Write partitioned Parquet
    # --------------------------------------------------------

    print()
    print("Writing partitioned Parquet files...")

    partition_count = 0

    for (year, month, store_id), group in all_sales.groupby(
        [
            all_sales["business_date"].dt.year,
            all_sales["business_date"].dt.month,
            "store_id",
        ]
    ):

        partition_dir = (
            OUTPUT_DIR
            / f"year={year}"
            / f"month={month:02d}"
            / f"store={store_id}"
        )

        partition_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            partition_dir
            / "sales.parquet"
        )

        group.to_parquet(
            output_file,
            index=False,
            engine="pyarrow"
        )

        partition_count += 1

    print(
        f"Partitions written: {partition_count}"
    )

    print()
    print("=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)

    print(f"Final row count: {len(all_sales):,}")
    print(f"Final checksum: {checksum}")
    print(f"Output: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()