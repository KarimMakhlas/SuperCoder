from tools.file_reader import list_files, read_file


def search_code(query: str) -> list[dict]:
    results = []
    query_lower = query.lower()

    for file in list_files():
        content = read_file(file)
        matches = [
            {"line": line_number, "text": line.strip()}
            for line_number, line in enumerate(content.splitlines(), start=1)
            if query_lower in line.lower()
        ]

        if matches:
            results.append({"file": file, "matches": matches})

    return results
