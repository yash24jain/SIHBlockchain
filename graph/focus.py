import networkx as nx


def create_focused_graph(
    graph,
    wallet_depths,
    suspect_wallet
):

    suspect_wallet = suspect_wallet.lower()

    # Create a new graph for visualization
    focused_graph = nx.MultiDiGraph()

    # Only include wallets discovered by our
    # controlled multi-hop investigation
    selected_wallets = set(wallet_depths.keys())

    for wallet in selected_wallets:

        if wallet in graph:

            focused_graph.add_node(
                wallet,
                hop=wallet_depths[wallet]
            )

    # Add only transactions between selected wallets
    for sender, receiver, data in graph.edges(data=True):

        if (
            sender in selected_wallets
            and receiver in selected_wallets
        ):

            focused_graph.add_edge(
                sender,
                receiver,
                **data
            )

    # Mark the reported wallet
    if suspect_wallet in focused_graph:

        focused_graph.nodes[suspect_wallet]["suspect"] = True

    return focused_graph