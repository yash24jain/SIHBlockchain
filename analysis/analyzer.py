from graph.traversal import find_paths
from graph.features import analyze_path
from analysis.splitting import detect_fund_splitting
from analysis.consolidation import detect_fund_consolidation
from analysis.velocity import calculate_path_velocity


def analyze_wallet(graph, wallet, max_hops=3):

    results = {
        "wallet": wallet,
        "paths": [],
        "splitting": None,
        "consolidation": None
    }

    # Find paths
    paths = find_paths(
        graph,
        wallet,
        max_hops
    )

    # Analyze paths
    for path in paths:

        path_details = analyze_path(
            graph,
            path
        )

        velocity = calculate_path_velocity(
            graph,
            path
        )

        path_result = {
            "path": path,
            "hops": path_details["hops"],
            "transactions": path_details["transactions"],
            "rapid_movement": (
                velocity["rapid_movement"]
                if velocity else False
            ),
            "duration_seconds": (
                velocity["duration_seconds"]
                if velocity else None
            )
        }

        results["paths"].append(path_result)

    # Splitting
    results["splitting"] = detect_fund_splitting(
        graph,
        wallet
    )

    # Consolidation
    results["consolidation"] = detect_fund_consolidation(
        graph,
        wallet
    )

    return results