import duckdb

con = duckdb.connect("analytics/annapurna.duckdb")

# ============================================================
# DUCKDB + MINIO
# ============================================================

con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

con.execute("SET s3_endpoint='localhost:9000';")
con.execute("SET s3_access_key_id='minioadmin';")
con.execute("SET s3_secret_access_key='minioadmin123';")
con.execute("SET s3_use_ssl=false;")
con.execute("SET s3_url_style='path';")

# ============================================================
# SOURCE FINANCE FILE
# ============================================================

finance_file = r"C:\Users\ub02-glab-005\Downloads\data_2\data\finance_monthly.csv"

# ============================================================
# PART F - RECONCILIATION
# ============================================================

query = f"""
WITH sales AS (

    SELECT
        strftime(business_date, '%Y-%m') AS month,

        ROUND(
            SUM(
                CASE
                    WHEN UPPER(line_type) IN ('SALE', 'RETURN')
                        THEN qty * unit_price

                    WHEN UPPER(line_type) = 'DISCOUNT'
                        THEN -(ABS(qty * unit_price))

                    ELSE 0
                END
            ),
            2
        ) AS calculated_revenue

    FROM read_parquet(
        's3://annapurna-sales/year=*/month=*/store=*/sales.parquet',
        hive_partitioning=true
    )

    GROUP BY 1
),

finance AS (

    SELECT
        month,
        ROUND(revenue_inr, 2) AS finance_revenue
    FROM read_csv_auto(
        '{finance_file}',
        header=true
    )
)

SELECT
    f.month,
    f.finance_revenue,
    s.calculated_revenue,

    ROUND(
        s.calculated_revenue - f.finance_revenue,
        2
    ) AS difference,

    CASE
        WHEN ABS(
            s.calculated_revenue - f.finance_revenue
        ) < 0.01
        THEN 'MATCH'
        ELSE 'MISMATCH'
    END AS status

FROM finance f

LEFT JOIN sales s
    ON f.month = s.month

ORDER BY f.month;
"""

print("=" * 85)
print("PART F - FINANCE RECONCILIATION")
print("=" * 85)

result = con.execute(query).fetchall()

print(
    f"{'Month':<10}"
    f"{'Finance':>20}"
    f"{'Calculated':>22}"
    f"{'Difference':>18}"
    f"{'Status':>12}"
)

print("-" * 85)

for month, finance, calculated, difference, status in result:

    print(
        f"{month:<10}"
        f"₹{finance:>18,.2f}"
        f"₹{calculated:>20,.2f}"
        f"₹{difference:>16,.2f}"
        f"{status:>12}"
    )

matches = sum(
    1 for row in result
    if row[4] == "MATCH"
)

mismatches = sum(
    1 for row in result
    if row[4] == "MISMATCH"
)

print("\n" + "=" * 85)
print(f"Months checked : {len(result)}")
print(f"Matches        : {matches}")
print(f"Mismatches     : {mismatches}")
print("=" * 85)

con.close()