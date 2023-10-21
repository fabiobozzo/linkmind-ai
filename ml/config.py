import csv


def read_categories_csv(filepath: str) -> list[dict]:
    categories = []
    with open(filepath) as f:
        categories_csv = csv.reader(f, escapechar='\\')
        next(f)  # skip the csv headers
        for row in categories_csv:
            categories.append({
                "label": row[0],
                "name": row[1],
                "description": row[2]
            })
    return categories
