import duckdb

con = duckdb.connect()

result = con.execute("""
    SELECT COUNT(*)
    FROM read_parquet(
        'staging/sales/year=*/month=*/store=*/sales.parquet',
        hive_partitioning = true
    );
""").fetchone()

print("=" * 60)
print("PART B - DUCKDB CHECK")
print("=" * 60)
print(f"Final row count: {result[0]}")