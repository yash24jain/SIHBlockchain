from graph.traversal import find_paths


def expand_path(graph, selected_path, additional_hops=1):
    """
    Expand investigation from the final wallet of a selected path.

    selected_path:
        Existing investigator-selected path.

    additional_hops:
        Number of additional hops to investigate.
    """

    if not selected_path:
        return []

    path = selected_path.get("path", [])

    if not path:
        return []

    last_wallet = path[-1]

    new_paths = find_paths(
        graph,
        last_wallet,
        additional_hops
    )

    expanded_paths = []

    for new_path in new_paths:

        # Prevent returning the starting wallet
        # as a separate meaningless path.
        if len(new_path) < 2:
            continue

        expanded_paths.append({
            "path": new_path,
            "hops": len(new_path) - 1
        })

    return expanded_paths