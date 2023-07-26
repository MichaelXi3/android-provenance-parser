import csv
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
import datetime
import json
import time

def main():
    # camflow provenance log path links - SPADE JSON format
    path1 = "/Users/michaelxi/Desktop/parser/helloworld-app.log"
    path2 = "/Users/michaelxi/Desktop/parser/camflow-examples/example-write-file-noprop.log"
    path3 = "/Users/michaelxi/Desktop/parser/helloworld-with-jni-filters.log"
    path4 = "/Users/michaelxi/Desktop/parser/example-cp-filter-applied.log"
    path5 = "/Users/michaelxi/Desktop/parser/logs/audit1.log"
    path6 = "/Users/michaelxi/Desktop/parser/logs/audit5.log"

    # Get all types of pathname and counts in provenance log
    vertices, edges = spade_json_load_graphs(path2)
    provG = CamFlow_gen_ProvG(vertices, edges)

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
    sizes = [500 + 50 * G.degree(node) for node in provG.nodes]

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

if __name__ == "__main__":
    main()


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


# Camflow Provenance Graph Parser
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

    # for element in object_types:
    #     print(element)

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

# Camflow Provenance Relation types and counts
def ProvG_get_relations(edges):
    relation_types = dict()
    for edge in edges:
        relation_type=edge["relation_type"] if "relation_type" in edge.keys() else edge["type"]
        if relation_type in relation_types:
            relation_types[relation_type] += 1
        else:
            relation_types[relation_type] = 1
    return relation_types
