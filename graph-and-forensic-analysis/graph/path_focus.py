import networkx as nx


def create_path_graph(graph, selected_path):
    """
    Create a graph containing only the selected investigation path.

    The original graph is not modified.
    Transaction data is preserved on the edges.
    """

    path = selected_path.get("path", [])

    path_graph = nx.MultiDiGraph()

    if not path:
        return path_graph

    # --------------------------------------------------
    # Add wallets belonging to the selected path
    # --------------------------------------------------

    for wallet in path:

        if wallet in graph.nodes:

            path_graph.add_node(
                wallet,
                **graph.nodes[wallet]
            )

        else:

            path_graph.add_node(wallet)

    # --------------------------------------------------
    # Add transactions between consecutive wallets
    # --------------------------------------------------

    for i in range(len(path) - 1):

        sender = path[i]
        receiver = path[i + 1]

        edge_data = graph.get_edge_data(
            sender,
            receiver
        )

        if not edge_data:
            continue

        # MultiDiGraph
        for _, data in edge_data.items():

            if isinstance(data, dict):

                path_graph.add_edge(
                    sender,
                    receiver,
                    **data
                )

    return path_graph