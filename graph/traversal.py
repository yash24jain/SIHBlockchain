from collections import deque


def find_paths(graph, start_wallet, max_hops=5):

    start_wallet = start_wallet.lower()

    # Check that starting wallet exists
    if start_wallet not in graph:
        print(f"Wallet {start_wallet} is not present in graph")
        return []

    queue = deque([
        (start_wallet, [start_wallet])
    ])

    paths = []

    while queue:

        current_wallet, path = queue.popleft()

        current_hops = len(path) - 1

        # Maximum hop reached
        if current_hops >= max_hops:
            continue

        # Safety check
        if current_wallet not in graph:
            print(
                f"Skipping wallet not present in graph: "
                f"{current_wallet}"
            )
            continue

        for next_wallet in graph.successors(current_wallet):

            if next_wallet in path:
                continue

            new_path = path + [next_wallet]

            paths.append(new_path)

            queue.append(
                (next_wallet, new_path)
            )

    return paths