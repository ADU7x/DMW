import duckdb

con = duckdb.connect("analytics/annapurna.duckdb")

# ============================================================
# LOAD DUCKDB EXTENSIONS
# ============================================================

con.execute("INSTALL postgres;")
con.execute("LOAD postgres;")

con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

# ============================================================
# CONNECT DUCKDB TO MINIO
# ============================================================

con.execute("SET s3_endpoint='localhost:9000';")
con.execute("SET s3_access_key_id='minioadmin';")
con.execute("SET s3_secret_access_key='minioadmin123';")
con.execute("SET s3_use_ssl=false;")
con.execute("SET s3_url_style='path';")

# ============================================================
# CONNECT DUCKDB TO POSTGRESQL
# ============================================================

con.execute("""
ATTACH 'dbname=annapurna host=localhost port=5432 user=annapurna password=annapurna'
AS pg (TYPE POSTGRES, READ_ONLY);
""")

# ============================================================
# FEDERATED QUERY
# MinIO Parquet + PostgreSQL master tables
# ============================================================

query = """
SELECT
    s.store_id,
    s.store_name,
    pc.category_name,
    ROUND(SUM(fs.qty * fs.unit_price), 2) AS revenue

FROM read_parquet(
    's3://annapurna-sales/year=*/month=*/store=*/sales.parquet',
    hive_partitioning=true
) fs

JOIN pg.public.stores s
    ON fs.store_id = s.store_id

JOIN pg.public.products p
    ON fs.product_code = p.product_code
   AND fs.business_date::DATE >= p.valid_from
   AND fs.business_date::DATE < p.valid_to

JOIN pg.public.product_categories pc
    ON p.category_id = pc.category_id

WHERE fs.business_date::DATE >= '2024-10-01'
  AND fs.business_date::DATE < '2024-11-01'

GROUP BY
    s.store_id,
    s.store_name,
    pc.category_name

ORDER BY
    s.store_id,
    pc.category_name;
"""

# ============================================================
# RUN QUERY
# ============================================================

print("=" * 75)
print("PART E - CROSS-SYSTEM QUERY")
print("=" * 75)

result = con.execute(query).fetchall()

print("\nOctober 2024 Revenue by Store and Category")
print("-" * 75)

for store_id, store_name, category, revenue in result:
    print(
        f"{store_id} | {store_name} | "
        f"{category} | ₹{revenue:,.2f}"
    )

print("\nRows returned:", len(result))

con.close()