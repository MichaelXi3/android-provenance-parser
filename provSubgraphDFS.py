from provLogParser import CamFlow_gen_ProvG
from provLogParser import spade_json_load_graphs

import networkx as nx
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

# user inputs
# 1. camflow provenance log
log_path = "/Users/michaelxi/Desktop/parser/logs/audit8.log"
# 2. start node id
start_node_id = "AABAAAAAACR5YRbQPVi6jQEAAAB5kZYJAAAAAAAAAAA="
# 3. end node id
end_node_id = "AABAAAAAACRM20QdYilYJwEAAAB5kZYJAAAAAAAAAAA="


# generate the provenance graph
vertices, edges = spade_json_load_graphs(log_path)
provG = CamFlow_gen_ProvG(vertices, edges)

# check if the start node and end node are in the graph
if start_node_id not in provG.nodes or end_node_id not in provG.nodes:
    print(f"One or both of the nodes {start_node_id} and {end_node_id} are not in the graph.")
    exit(1)

# use NetworkX's shortest path function to find a path from the start node to the end node
undirected_provG = provG.to_undirected()
try:
    path_nodes = nx.shortest_path(undirected_provG, source=start_node_id, target=end_node_id)
    print(f"The shortest path from node start to node end is: {path_nodes}")

    # Extract edges from the path
    path_edges = [(path_nodes[i], path_nodes[i+1]) for i in range(len(path_nodes) - 1)]
    print(f"The edges in this path are: {path_edges}")

    # Create a subgraph from the nodes in the path
    subgraph = provG.subgraph(path_nodes)

    # draw the subgraph
    G_sub = nx.DiGraph()
    for u, v, data in subgraph.edges(data=True):
        if G_sub.has_edge(u, v):
            G_sub[u][v]['label'] = G_sub[u][v]['label'] + ', ' + data['label']
        else:
            G_sub.add_edge(u, v, label=data['label'])

    labels = nx.get_node_attributes(subgraph, 'label')
    edge_labels = nx.get_edge_attributes(G_sub, 'label')

    colors = []
    light_red = (1, 0.6, 0.6)
    for node, data in subgraph.nodes(data=True):
        if data['prov_type'] == 'process_memory':
            colors.append(light_red)
        elif data['prov_type'] == 'file':
            colors.append("skyblue")
        elif data['prov_type'] == 'path':
            colors.append("grey")
        elif data['prov_type'] == 'machine':
            colors.append("orange")
        elif data['prov_type'] == 'task':
            colors.append("lightgreen")
        else:
            colors.append("purple")

    sizes = [500 + 50 * G_sub.degree(node) for node in subgraph.nodes]
    pos = nx.spring_layout(subgraph, k=0.5, iterations=50)

    # Draw the graph using node and edge labels
    nx.draw(subgraph, pos, labels=labels, with_labels=True, node_size=sizes, node_color=colors, font_size=8)
    nx.draw_networkx_edge_labels(G_sub, pos, edge_labels=edge_labels, font_color='red', font_size=8)

    # Create patches for the legend
    red_patch = mpatches.Patch(color=light_red, label='process_memory')
    skyblue_patch = mpatches.Patch(color='skyblue', label='file')
    grey_patch = mpatches.Patch(color='grey', label='path')
    orange_patch = mpatches.Patch(color='orange', label='machine')
    lightgreen_patch = mpatches.Patch(color='lightgreen', label='task')
    purple_patch = mpatches.Patch(color='purple', label='Other')

    plt.legend(handles=[red_patch, skyblue_patch, grey_patch, orange_patch, lightgreen_patch, purple_patch])
    plt.show()

except nx.NetworkXNoPath:
    print(f"No path found from node {start_node_id} to node {end_node_id}.")
