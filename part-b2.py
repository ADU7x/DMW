from pathlib import Path
import pandas as pd


SALES_DIR = Path(
    r"C:\Users\ub02-glab-005\Downloads\data_2\data\sales"
)

files = list(SALES_DIR.glob("*.csv"))

print(f"Total CSV files: {len(files)}")

total_rows = 0
line_type_counts = {}
errors = []

for file in files:
    try:
        # Detect delimiter from the first line
        with open(file, "r", encoding="utf-8-sig") as f:
            header = f.readline()

        if ";" in header:
            delimiter = ";"
        else:
            delimiter = ","

        df = pd.read_csv(
            file,
            sep=delimiter,
            encoding="utf-8-sig"
        )

        total_rows += len(df)

        if "line_type" not in df.columns:
            errors.append(
                f"{file.name}: missing line_type column"
            )
            continue

        for line_type, count in df["line_type"].value_counts().items():
            line_type_counts[line_type] = (
                line_type_counts.get(line_type, 0)
                + int(count)
            )

    except Exception as e:
        errors.append(
            f"{file.name}: {e}"
        )


print(f"\nTotal rows: {total_rows}")

print("\nLine type counts:")
for line_type, count in sorted(line_type_counts.items()):
    print(f"{line_type}: {count}")

print(f"\nFiles with errors: {len(errors)}")

if errors:
    print("\nErrors:")
    for error in errors[:20]:
        print(error)