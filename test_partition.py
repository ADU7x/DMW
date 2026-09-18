import duckdb

con = duckdb.connect()

query = """
SELECT COUNT(*)
FROM read_parquet(
    'staging/sales/year=2024/month=10/store=S01/sales.parquet'
)
"""

result = con.execute(query).fetchone()[0]

print("Partition: year=2024/month=10/store=S01")
print("Files accessed: 1")
print("Rows in partition:", result)