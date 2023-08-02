import csv
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
import datetime
import json
import time
import argparse
import numpy as np


# Camflow Provenance Graph Loader
def spade_json_load_graphs(path):
    vertices = []
    edges = []
    with open(path, 'r', encoding="utf-8") as log:
        for line in log:
            if "[" in line or "]" in line:
                continue
            if line[0] == ",":
                line = line[1:]
            try:
                data = json.loads(line)
                if "from" not in data.keys():
                    vertices.append(data)
                else:
                    edges.append(spade_json_load_edges(data))
            except json.JSONDecodeError:
                print(f"Couldn't parse line: {line}")
                continue
    return vertices, edges

def spade_json_load_edges(data):
    edge = {}
    edge["from"] = data["from"]
    edge["to"] = data["to"]
    edge["type"] = data["type"]

    edge_attrs = data["annotations"]
    for attr in edge_attrs.keys():
        edge[attr] = edge_attrs[attr]
    return edge


# Camflow Provenance Graph Parser, return provG
def CamFlow_gen_ProvG(vertices, edges):
    provG = nx.MultiDiGraph()
    object_types = set()
    for vertex in vertices:
        vid = vertex["id"]
        label_dict = vertex["annotations"]
        node_type = label_dict["object_type"]
        object_types.add(node_type)

        if node_type == "unknown":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "string":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + label_dict["log"])
        elif node_type == "task":
            # TODO: check the name of the task "cf:name"
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "inode_unknown":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "file":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + str(label_dict["version"]))
        elif node_type in ["link", "directory", "char", "block", "pipe", "socket"]:
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + label_dict["secctx"] + ":" + str(
                               label_dict["mode"]))
        elif node_type == "msg":
            # TODO: need to decide the attributes
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "shm":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + str(label_dict["mode"]))
        elif node_type == "address":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "sb":
            # TODO: need to decide the attributes
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type in ["disc_entity", "disc_activity", "disc_agent"]:
            # TODO: need to decide the attributes
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "packet":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + label_dict["sender"] + ":" + label_dict[
                               "receiver"])
        elif node_type == "iattr":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + str(label_dict["mode"]))
        elif node_type == "xattr":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + label_dict["name"])
        elif node_type == "packet_content":
            # TODO: need to decide the attributes
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "argv":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"])
        elif node_type == "envp":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + label_dict["envp"])
        elif node_type == "process_memory":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                           label=label_dict["object_type"] + ":" + str(label_dict["version"]) + ":" + label_dict["secctx"])
        # elif node_type == "process_memory":
        #     provG.add_node(vid, prov_type=label_dict["object_type"],
        #                    label=label_dict["object_type"] + ":" + str(label_dict["uid"]) + ":" + str(
        #                        label_dict["gid"]) + ":" + label_dict["secctx"])
        elif node_type == "path": # Modified
            provG.add_node(vid, prov_type=label_dict["object_type"],
                        label=label_dict["object_type"] + ":" + str(label_dict["pathname"]))
        elif node_type == "machine":
            provG.add_node(vid, prov_type=label_dict["object_type"],
                        label=label_dict["object_type"])
        provG.nodes[vid]["anomalous"] = 0
        provG.nodes[vid]["time"] = cfdate_to_second(label_dict["cf:date"])

    for i in range(len(edges)):
        edge_time = edges[i]["cf:date"]
        dt_obj = cfdate_to_second(edge_time)
        edges[i]["cf:date"] = dt_obj

    for edge in sorted(edges, key=lambda a: int(a["cf:date"])):
        provG.add_edge(
            edge["from"],
            edge["to"],
            relation_type=edge["relation_type"] if "relation_type" in edge.keys() else edge["type"],
            # here I use jiffies to identify the recorded time of the edge
            time=int(edge["cf:date"]),
            epoch=int(edge["epoch"]),
            label=edge["relation_type"] if "relation_type" in edge.keys() else edge["type"],
            anomalous=0
        )

    print(provG)

    # remove bad edges without src or dst nodes
    remove_bad_edges = []
    for edge in provG.edges.data():
        src, dst, attr = edge
        if provG.nodes[src] == {}:
            remove_bad_edges.append(src)
        elif provG.nodes[dst] == {}:
            remove_bad_edges.append(dst)
    provG.remove_nodes_from(remove_bad_edges)

    print("After remove bad edges: ", provG)

    # remove isolated nodes
    remove_bad_nodes = []
    for nid in provG.nodes:
        if list(provG.successors(nid)) == [] and list(provG.predecessors(nid)) == []:
            remove_bad_nodes.append(nid)
    provG.remove_nodes_from(remove_bad_nodes)

    print("After remove isolated nodes: ", provG)

    return provG

def cfdate_to_second(cf_date):
    return time.mktime(datetime.datetime.strptime(cf_date, "%Y:%m:%dT%H:%M:%S").timetuple())


# Camflow Provenance Relation Path Name Collector
def ProvG_get_pathnames(vertices, id):
    pathname_dict = {}
    for vertex in vertices:
        label_dict = vertex["annotations"]
        node_type = label_dict["object_type"]

        if node_type == "path": 
            pathname = label_dict["pathname"]
            if pathname not in pathname_dict:
                pathname_dict[pathname] = 1
            else:
                pathname_dict[pathname] += 1

    # Use string formatting to include the id in the filename        
    with open(f'pathnames{id}.txt', 'w') as f:
        for key, value in pathname_dict.items():
            print(f"Pathname is: {key}, and its count is {value}", file=f)
    return

# Camflow Provenance Relation types and counts, return relation_types dict
def ProvG_get_relations(edges):
    relation_types = dict()
    for edge in edges:
        relation_type=edge["relation_type"] if "relation_type" in edge.keys() else edge["type"]
        if relation_type in relation_types:
            relation_types[relation_type] += 1
        else:
            relation_types[relation_type] = 1
    return relation_types


# Collapse version_activity edges of nodes with same type, return collapsed provG
def ProvG_collapse_version_edges(provG):
    # Get a set of unique node types in provG, b/c we want to collapse nodes one type at a time
    node_types = set(nx.get_node_attributes(provG, 'prov_type').values())
    print(node_types)

    # collapse nodes one type at a time
    for node_type in node_types:
        # Find pairs of nodes connected by "version_activity" edges and are of the same node type
        to_collapse = []
        for edge in provG.edges.data():
            src, dst, attr = edge
            if attr['relation_type'] == 'version_activity' or attr['relation_type'] == 'version_entity':
                if provG.nodes[src]['prov_type'] == node_type and provG.nodes[dst]['prov_type'] == node_type:
                    to_collapse.append((src, dst))

        # Group nodes connected by same 'version_activity' edge into one set -> as single new node after collapse
        connected_nodes = []
        while to_collapse:
            group = set(to_collapse.pop(0))
            for pair in to_collapse:
                if pair[0] in group or pair[1] in group:
                    group.update(pair)
                    to_collapse.remove(pair)
            connected_nodes.append(group)

        # Replace each group of connected nodes with a single node
        for group in connected_nodes:
            # The new node's label will be the concatenation of original nodes' labels
            new_label = ':'.join(provG.nodes[n]['label'] for n in group if n in provG.nodes)
            # The new node's id will be the minimum id from the group, i.e. first version of this type of node
            new_node = min(group)
            # Add the new node to the graph
            provG.add_node(new_node, label=new_label, prov_type=node_type)  # Set the node type of the new node as the same as the original nodes

            # Connect the new node with nodes which were connected to the original nodes, including prev and succ nodes
            new_edges = []
            for n in group:
                for pred, _, attr in provG.in_edges(n, data=True):
                    if pred not in group:  # Avoid self-loop
                        if not any(d['relation_type'] == attr['relation_type'] for _, _, d in provG.edges(pred, data=True) if _ == new_node): # Avoid adding same relation_type edges
                            new_edges.append((pred, new_node, attr))
                for _, succ, attr in provG.out_edges(n, data=True):
                    if succ not in group:  # Avoid self-loop
                        if not any(d['relation_type'] == attr['relation_type'] for _, _, d in provG.edges(new_node, data=True) if _ == succ): # Avoid adding same relation_type edges
                            new_edges.append((new_node, succ, attr))
            
            for edge in new_edges:
                u, v, attrs = edge
                # print(str(edge) + "\n")
                provG.add_edge(u, v, **attrs)

            # Remove original nodes from the graph -> except the first version node!
            to_remove = group - {new_node}
            provG.remove_nodes_from(to_remove)
    return provG

# Draw provG using Digraph
def digraph_code(provG):
    # Create a DiGraph graph, since multigraph does not support draw_networkx_edge_labels
    G = nx.DiGraph()

    # Iterate through the edges and add them to the new graph
    for u, v, data in provG.edges(data=True):
        if G.has_edge(u, v):
            # if the edge already exists, append the new label to the existing one
            G[u][v]['label'] = G[u][v]['label'] + ', ' + data['label']
        else:
            # else, create a new edge
            G.add_edge(u, v, label=data['label'])

    # Get node and edge labels
    labels = nx.get_node_attributes(provG, 'label')
    edge_labels = nx.get_edge_attributes(G, 'label')

    # Define node colors based on 'prov_type'
    colors = []
    light_red = (1, 0.6, 0.6)
    for node, data in provG.nodes(data=True):
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
            colors.append("orange")

    # Define the size of each node based on the number of edges connected to it
    sizes = [500 + 50 * provG.degree(node) for node in provG.nodes]

    # Create position layout
    pos = nx.spring_layout(provG, k=1, scale=2)

    # Draw the graph using node and edge labels
    nx.draw(provG, pos, labels=labels, with_labels=True, node_size=sizes, node_color=colors, font_size=8)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)

    # Create patches for the legend
    red_patch = mpatches.Patch(color=light_red, label='process_memory')
    skyblue_patch = mpatches.Patch(color='skyblue', label='file')
    grey_patch = mpatches.Patch(color='grey', label='path')
    orange_patch = mpatches.Patch(color='orange', label='machine')
    lightgreen_patch = mpatches.Patch(color='lightgreen', label='task')
    purple_patch = mpatches.Patch(color='purple', label='Other')

    # Add legend
    plt.legend(handles=[red_patch, skyblue_patch, grey_patch, orange_patch, lightgreen_patch, purple_patch])
    plt.show()

# Draw provG using Multigraph, so that multiple edges between two nodes are allowed
def multigraph_code(provG):
    G = nx.MultiDiGraph()

    # Iterate through the edges and add them to the new graph
    for u, v, data in provG.edges(data=True):
        G.add_edge(u, v, label=data['label'])

    # Get node and edge labels
    labels = nx.get_node_attributes(provG, 'label')

    # Define node colors based on 'prov_type'
    colors = []
    light_red = (1, 0.6, 0.6)
    for node, data in provG.nodes(data=True):
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
            colors.append("orange")

    # Define the size of each node based on the number of edges connected to it
    sizes = [500 + 50 * provG.degree(node) for node in provG.nodes]

    # Create position layout
    pos = nx.spring_layout(provG, k=1, scale=2)

    # Draw the graph using node and edge labels
    nx.draw(provG, pos, labels=labels, with_labels=True, node_size=sizes, node_color=colors, font_size=8)

    # Define edge labels positions and draw them
    for u, v, data in G.edges(data=True):
        label = data['label']
        x = (pos[u][0] + pos[v][0]) / 2
        y = (pos[u][1] + pos[v][1]) / 2
        dx = np.sign(pos[v][0] - pos[u][0]) * 0.1 + np.random.uniform(-0.05, 0.05)
        dy = np.sign(pos[v][1] - pos[u][1]) * 0.1 + np.random.uniform(-0.05, 0.05)
        plt.annotate(text=label, xy=(x, y), xytext=(x + dx, y + dy), color='red', fontsize=9)

    # Create patches for the legend
    red_patch = mpatches.Patch(color=light_red, label='process_memory')
    skyblue_patch = mpatches.Patch(color='skyblue', label='file')
    grey_patch = mpatches.Patch(color='grey', label='path')
    orange_patch = mpatches.Patch(color='orange', label='machine')
    lightgreen_patch = mpatches.Patch(color='lightgreen', label='task')
    purple_patch = mpatches.Patch(color='purple', label='Other')

    # Add legend
    plt.legend(handles=[red_patch, skyblue_patch, grey_patch, orange_patch, lightgreen_patch, purple_patch])
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph_type", type=str, default="digraph",
                        help="Type of graph to draw: 'digraph' or 'multigraph'")
    parser.add_argument("--log_file", type=str, required=True,
                        help="Absolute path to the log file")
    parser.add_argument("--collapse", type=bool, required=True,
                        help="Collapse provG by version_activity")
    args = parser.parse_args()

    log_file_path = args.log_file
    collapse_graph = args.collapse

    # Generate Camflow Provenance Graph
    vertices, edges = spade_json_load_graphs(log_file_path)
    provG = CamFlow_gen_ProvG(vertices, edges)

    # Collapse version_activity nodes
    if (collapse_graph):
        provG = ProvG_collapse_version_edges(provG=provG)

    # Visualize Provenace Graph
    if args.graph_type.lower() == "digraph":
        digraph_code(provG)
    elif args.graph_type.lower() == "multigraph":
        multigraph_code(provG)
    else:
        print("Invalid graph type! Please specify either 'digraph' or 'multigraph'.")


if __name__ == "__main__":
    main()

# camflow provenance log path links - SPADE JSON format
    # path1 = "/Users/michaelxi/Desktop/parser/ProvG-Executable/example-write-file.log"
    # path2 = "/Users/michaelxi/Desktop/parser/camflow-examples/example-write-file-noprop.log"
    # path3 = "/Users/michaelxi/Desktop/parser/helloworld-with-jni-filters.log"
    # path4 = "/Users/michaelxi/Desktop/parser/example-cp-filter-applied.log"
    # path5 = "/Users/michaelxi/Desktop/parser/logs/audit1.log"
    # path6 = "/Users/michaelxi/Desktop/parser/logs/audit5.log"

# python3 provLogParser.py --graph_type multigraph --log_file /Users/michaelxi/Desktop/parser/ProvG-Executable/example-write-file.log --collapse true
# python3 provLogParser.py --graph_type multigraph --log_file /Users/michaelxi/Desktop/parser/logs/audit8.log --collapse true