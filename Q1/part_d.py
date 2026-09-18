import duckdb

con = duckdb.connect("analytics/annapurna.duckdb")

con.execute("INSTALL postgres;")
con.execute("LOAD postgres;")

con.execute("""
    ATTACH 'dbname=annapurna host=localhost port=5432 user=annapurna password=annapurna'
    AS postgres_db (TYPE POSTGRES, READ_ONLY);
""")

query = """
SELECT
    ROUND(SUM(fs.qty * pr.selling_price), 2) AS revenue_at_historical_price
FROM fact_sales fs
JOIN postgres_db.public.products p
    ON fs.product_code = p.product_code
   AND fs.business_date::DATE >= p.valid_from
   AND fs.business_date::DATE < p.valid_to
JOIN postgres_db.public.price_revisions pr
    ON p.product_sk = pr.product_sk
   AND fs.business_date::DATE >= pr.effective_from
   AND fs.business_date::DATE < pr.effective_to
WHERE fs.business_date::DATE >= ?
  AND fs.business_date::DATE < ?;
"""

print("=" * 65)
print("PART D - EFFECTIVE-DATED PRICE EVIDENCE")
print("=" * 65)

for label, start, end in [
    ("MARCH 2024", "2024-03-01", "2024-04-01"),
    ("NOVEMBER 2024", "2024-11-01", "2024-12-01")
]:
    result = con.execute(query, [start, end]).fetchone()[0]

    print(f"\n{label}")
    print("-" * 40)
    print(f"Revenue at applicable historical prices: {result}")

con.close()