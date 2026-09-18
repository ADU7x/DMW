from pathlib import Path

sales_dir = Path("staging/sales")

# All Parquet files
all_files = list(sales_dir.rglob("*.parquet"))

# October 2024, Store S01
target_dir = sales_dir / "year=2024" / "month=10" / "store=S01"
target_files = list(target_dir.glob("*.parquet"))

all_bytes = sum(f.stat().st_size for f in all_files)
target_bytes = sum(f.stat().st_size for f in target_files)

print("=" * 70)
print("PART A - PARTITIONING EVIDENCE")
print("=" * 70)

print(f"Total Parquet files: {len(all_files)}")
print(f"Total Parquet bytes: {all_bytes:,}")

print()
print("Query: Store S01, October 2024")
print(f"Relevant files: {len(target_files)}")
print(f"Relevant bytes: {target_bytes:,}")

print()
print("Comparison")
print(f"Partitioned layout: {len(target_files)} file(s), {target_bytes:,} bytes")
print(f"Single-folder layout: potentially {len(all_files)} files, {all_bytes:,} bytes")

print()
print(f"Bytes avoided: {all_bytes - target_bytes:,}")
print("=" * 70)