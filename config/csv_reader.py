import csv


def read_sources_csv(filepath: str) -> list[dict]:
    sources = []
    with open(filepath) as f:
        sources_csv = csv.reader(f)
        next(f)  # skip the csv headers
        for row in sources_csv:
            sources.append({
                "category": row[0],
                "url": row[1],
                "linkClass": row[2],
                "articleTag": row[3],
                "articleClass": row[4],
                "maxDepth": int(row[5])
            })
    return sources
