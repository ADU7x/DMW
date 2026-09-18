import duckdb

con = duckdb.connect("analytics/annapurna.duckdb")

# Connect DuckDB to PostgreSQL
con.execute("INSTALL postgres;")
con.execute("LOAD postgres;")

con.execute("""
    ATTACH 'dbname=annapurna host=localhost port=5432 user=annapurna password=annapurna'
    AS postgres_db (TYPE POSTGRES, READ_ONLY);
""")

# Run Part C schema
with open("sql/part_c_schema.sql", "r") as f:
    sql = f.read()

con.execute(sql)

print("=" * 60)
print("PART C - ANALYTICAL TABLES")
print("=" * 60)

for table in [
    "dim_store",
    "dim_product",
    "dim_category",
    "dim_date",
    "fact_sales"
]:
    count = con.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {count:,} rows")

con.close()