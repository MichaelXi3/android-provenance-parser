import os
from provLogParser import CamFlow_gen_ProvG
from provLogParser import spade_json_load_graphs

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def main():
    # user inputs
    # 1. camflow provenance log
    log_path = "/Users/michaelxi/Desktop/parser/logs/audit-pdd.log"
    # 2. start node id - root of subgraph bfs
    start_node_id = "AABAAAAAACTL5NZvLDkY0wEAAABaiSBMAAAAAAAAAAA="
    # 3. max-depth of bfs traversal
    max_depth = 3

    # graph storage file
    graph_file = "provG-cache.graphml"

    if os.path.exists(graph_file):
        # load the graph if it already exists
        provG = nx.read_graphml(graph_file)
    else:
        # construct the graph if it does not exist
        vertices, edges = spade_json_load_graphs(log_path)               # group vertices and edges
        provG = CamFlow_gen_ProvG(vertices, edges)                       # build camflow dependency graph
        nx.write_graphml(provG, graph_file)    

    undirected_provG = provG.to_undirected()                             # transform directed graph to undirected graph
    subgraph = BFS_subgraph(undirected_provG, start_node_id, max_depth)  # generate subgraph with specified max-depth

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



def BFS_subgraph(provG, start_node_id, max_depth):
    neighbors = list(provG.neighbors(start_node_id))
    print(neighbors)

    bfs_edges = nx.bfs_edges(provG, start_node_id, depth_limit=max_depth)
    nodes = {start_node_id} | {v for u, v in bfs_edges}
    return provG.subgraph(nodes)

if __name__ == "__main__":
    main()