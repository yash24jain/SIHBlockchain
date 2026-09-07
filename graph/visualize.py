from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def _short_address(address):
    address = str(address)
    return f"{address[:6]}...{address[-4:]}"


def _is_vasp(node_data):
    entity_type = str(node_data.get("entity_type", "")).upper()
    label = str(node_data.get("label", "")).upper()
    return (
        "EXCHANGE" in entity_type
        or "VASP" in entity_type
        or "DEPOSIT" in entity_type
        or "BINANCE" in label
        or "COINBASE" in label
    )


def visualize_graph(graph, suspect_wallet=None):
    if graph is None or len(graph.nodes) == 0:
        print("No graph data available for visualization.")
        return

    # Determine suspect wallet
    if suspect_wallet is None:
        for node, data in graph.nodes(data=True):
            if data.get("hop") == 0:
                suspect_wallet = node
                break

    if suspect_wallet is None:
        suspect_wallet = list(graph.nodes)[0]

    suspect_wallet = str(suspect_wallet).lower().strip()

    # Clean display graph
    display_graph = graph.copy()
    display_graph.remove_edges_from(list(nx.selfloop_edges(display_graph)))

    zero_value_edges = [
        (u, v) for u, v, d in display_graph.edges(data=True)
        if float(d.get("amount", 0.0) or 0.0) <= 0.0
    ]
    display_graph.remove_edges_from(zero_value_edges)

    isolated_nodes = [
        node for node in display_graph.nodes
        if display_graph.degree(node) == 0 and str(node).lower().strip() != suspect_wallet
    ]
    display_graph.remove_nodes_from(isolated_nodes)

    if len(display_graph.nodes) == 0:
        print("Nothing to visualize.")
        return

    fig, ax = plt.subplots(figsize=(16, 10))
    plt.subplots_adjust(top=0.90, bottom=0.08, left=0.05, right=0.95)

    pos = nx.spring_layout(display_graph, seed=42, k=2.2, iterations=100)

    # Multi-token edge labels
    edge_labels = {}
    for sender, receiver, data in display_graph.edges(data=True):
        amt = float(data.get("amount", 0.0))
        token = data.get("token_symbol", data.get("token", data.get("amount_unit", "ETH")))
        edge_labels[(sender, receiver)] = f"{amt:.2f} {token}"

    # Summary aggregations with wrapping to avoid horizontal run-off
    outgoing_by_token = defaultdict(float)
    incoming_by_token = defaultdict(float)

    for sender, receiver, data in display_graph.edges(data=True):
        amt = float(data.get("amount", 0.0) or 0.0)
        token = data.get("token_symbol", data.get("token", data.get("amount_unit", "ETH")))
        if str(sender).lower().strip() == suspect_wallet:
            outgoing_by_token[token] += amt
        if str(receiver).lower().strip() == suspect_wallet:
            incoming_by_token[token] += amt

    def _format_token_list(token_dict):
        if not token_dict:
            return "0.00 ETH"
        items = [f"{v:.2f} {k}" for k, v in token_dict.items()]
        # Group into lines of 3 tokens max
        chunked = [", ".join(items[i:i + 3]) for i in range(0, len(items), 3)]
        return "\n    ".join(chunked)

    summary_text = (
        f"Wallets analyzed: {len(display_graph.nodes)}\n"
        f"Transactions shown: {len(display_graph.edges)}\n"
        f"Outgoing from suspect: {_format_token_list(outgoing_by_token)}\n"
        f"Incoming to suspect: {_format_token_list(incoming_by_token)}"
    )

    legend_elements = [
        Line2D([0], [0], marker="o", color="w", label="Suspect Wallet", markerfacecolor="red", markeredgecolor="black", markersize=10),
        Line2D([0], [0], marker="o", color="w", label="Hop 1 Wallet", markerfacecolor="skyblue", markeredgecolor="black", markersize=10),
        Line2D([0], [0], marker="o", color="w", label="Hop 2+ Wallet", markerfacecolor="plum", markeredgecolor="black", markersize=10),
        Line2D([0], [0], marker="o", color="w", label="VASP / Exchange Deposit", markerfacecolor="gold", markeredgecolor="black", markersize=10)
    ]

    # Movable Box Positions (in data coordinates)
    x_coords = [p[0] for p in pos.values()]
    y_coords = [p[1] for p in pos.values()]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    span_x = (x_max - x_min) or 1.0
    span_y = (y_max - y_min) or 1.0

    box_positions = {
        "info": [x_min - 0.15 * span_x, y_max + 0.1 * span_y],
        "summary": [x_min - 0.15 * span_x, y_min - 0.15 * span_y]
    }

    drag_state = {
        "mode": None,  # "node", "box_info", or "box_summary"
        "target_node": None,
        "offset": (0.0, 0.0)
    }

    current_info_text = ["Click a wallet or drag boxes"]

    def redraw():
        ax.clear()
        ax.set_title("Blockchain Money Flow Investigation", fontsize=20, fontweight="bold", pad=15, y=0.96)

        current_colors = []
        current_sizes = []
        for node in display_graph.nodes:
            nl = str(node).lower().strip()
            nd = display_graph.nodes[node]
            if nl == suspect_wallet:
                current_colors.append("red")
                current_sizes.append(900)
            elif _is_vasp(nd):
                current_colors.append("gold")
                current_sizes.append(750)
            else:
                current_colors.append("skyblue" if nd.get("hop") == 1 else "plum")
                current_sizes.append(650 if nd.get("hop") == 1 else 600)

        # Draw Graph
        nx.draw_networkx_edges(
            display_graph, pos, ax=ax, edge_color="black", width=1.5,
            arrows=True, arrowsize=18, arrowstyle="-|>",
            connectionstyle="arc3,rad=0.08", node_size=current_sizes
        )
        nx.draw_networkx_nodes(
            display_graph, pos, ax=ax, node_color=current_colors,
            node_size=current_sizes, edgecolors="black", linewidths=1.5
        )
        nx.draw_networkx_labels(
            display_graph, pos, labels={n: _short_address(n) for n in display_graph.nodes},
            ax=ax, font_size=8, font_weight="bold"
        )
        if edge_labels:
            nx.draw_networkx_edge_labels(
                display_graph, pos, edge_labels=edge_labels, ax=ax,
                font_size=8, font_weight="bold", label_pos=0.5,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1)
            )

        ax.legend(handles=legend_elements, loc="upper right", fontsize=10, frameon=True)

        # Movable Info Box (Drag by clicking near its top-left)
        ax.text(
            box_positions["info"][0], box_positions["info"][1],
            current_info_text[0],
            fontsize=10, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="black", alpha=0.9)
        )

        # Movable Summary Box (Drag anywhere inside)
        ax.text(
            box_positions["summary"][0], box_positions["summary"][1],
            summary_text,
            fontsize=9, verticalalignment="bottom",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="black", alpha=0.9)
        )

        # Add visual margins so dragging boxes outward doesn't clip
        all_xs = [p[0] for p in pos.values()] + [box_positions["info"][0], box_positions["summary"][0]]
        all_ys = [p[1] for p in pos.values()] + [box_positions["info"][1], box_positions["summary"][1]]
        ax.set_xlim(min(all_xs) - 0.2 * span_x, max(all_xs) + 0.2 * span_x)
        ax.set_ylim(min(all_ys) - 0.2 * span_y, max(all_ys) + 0.2 * span_y)
        ax.set_axis_off()

    # Event handlers for dragging nodes and boxes
    def on_press(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        # 1. Check Info Box hit
        bx_info, by_info = box_positions["info"]
        if (bx_info - 0.1 * span_x <= event.xdata <= bx_info + 0.3 * span_x) and (by_info - 0.2 * span_y <= event.ydata <= by_info + 0.05 * span_y):
            drag_state["mode"] = "box_info"
            drag_state["offset"] = (bx_info - event.xdata, by_info - event.ydata)
            return

        # 2. Check Summary Box hit
        bx_sum, by_sum = box_positions["summary"]
        if (bx_sum - 0.1 * span_x <= event.xdata <= bx_sum + 0.4 * span_x) and (by_sum - 0.05 * span_y <= event.ydata <= by_sum + 0.3 * span_y):
            drag_state["mode"] = "box_summary"
            drag_state["offset"] = (bx_sum - event.xdata, by_sum - event.ydata)
            return

        # 3. Check Nodes
        clicked_node = None
        min_dist = float("inf")
        for node, (x, y) in pos.items():
            dist = (x - event.xdata) ** 2 + (y - event.ydata) ** 2
            if dist < min_dist:
                min_dist = dist
                clicked_node = node

        if min_dist <= 0.08 * (span_x ** 2 + span_y ** 2):
            drag_state["mode"] = "node"
            drag_state["target_node"] = clicked_node

            node_data = display_graph.nodes[clicked_node]
            hop = node_data.get("hop", "Unknown")
            entity_type = node_data.get("entity_type", "EOA")
            label = node_data.get("label", "Unlabeled")

            node_role = "Suspect Wallet" if str(clicked_node).lower().strip() == suspect_wallet else f"{entity_type} ({label})"
            current_info_text[0] = (
                f"Type: {node_role}\n"
                f"Address: {clicked_node}\n"
                f"Hop: {hop}\n"
                f"Incoming: {display_graph.in_degree(clicked_node)} | "
                f"Outgoing: {display_graph.out_degree(clicked_node)}"
            )
            redraw()
            fig.canvas.draw_idle()

    def on_motion(event):
        if drag_state["mode"] is None or event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        if drag_state["mode"] == "node":
            pos[drag_state["target_node"]] = (event.xdata, event.ydata)
        elif drag_state["mode"] == "box_info":
            box_positions["info"] = [event.xdata + drag_state["offset"][0], event.ydata + drag_state["offset"][1]]
        elif drag_state["mode"] == "box_summary":
            box_positions["summary"] = [event.xdata + drag_state["offset"][0], event.ydata + drag_state["offset"][1]]

        redraw()
        fig.canvas.draw_idle()

    def on_release(event):
        drag_state["mode"] = None
        drag_state["target_node"] = None

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    redraw()
    plt.show()