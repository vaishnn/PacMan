import pprint

def search_and_rank_list_of_dicts(data_list, query):
    """
    Searches a list of dictionaries and sorts the results based on the
    starting index of the query within the 'name' field.
    """
    lower_query = query.lower()

    # 1. Filter the list to find dictionaries where the name contains the query
    matches = [
        item for item in data_list
        if lower_query in item['name'].lower()
    ]

    # 2. Sort the filtered results using your original positional logic
    sorted_matches = sorted(
        matches,
        key=lambda item: item['name'].lower().find(lower_query)
    )

    return sorted_matches

# --- Example Usage ---

data = [
    {'name': 'Zebra', 'id': 3},
    {'name': 'Apple', 'id': 1},
    {'name': 'Mango', 'id': 4}, # "an" is at index 1
    {'name': 'Banana', 'id': 2} # "an" is at index 2
]

# Search for "an"
search_term = "e"
results = search_and_rank_list_of_dicts(data, search_term)

print(f"--- Searching for '{search_term}' and ranking by index ---")
pprint.pprint(results)
