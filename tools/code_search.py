from tools.file_reader import list_files, read_file


def search_code(query: str) -> list[str]:
    results = []

    for file in list_files():
        content = read_file(file)

        if query.lower() in content.lower():
            results.append(file)

    return results
