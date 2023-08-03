from provLogParser import spade_json_load_graphs
from provLogParser import ProvG_get_pathnames
from provLogParser import ProvG_get_relations

import argparse
import difflib
import os

# Get and compare vertices pathname nodes and counts 
def getAllPathnamesAndCounts(vertices1, vertices2):
    ProvG_get_pathnames(vertices1, 1)
    ProvG_get_pathnames(vertices2, 2)

    # compare the diff of two files
    with open('pathnames1.txt', 'r') as file1, open('pathnames2.txt', 'r') as file2:
        lines1 = sorted(file1.readlines())
        lines2 = sorted(file2.readlines())

    diff = difflib.unified_diff(lines1, lines2)

    # write diff to a file
    with open('pathname-diff.txt', 'w') as outfile:
        outfile.write(''.join(diff))

    # delete intermediate files
    os.remove("pathnames1.txt")
    os.remove("pathnames2.txt")


# Get and compare edges relation types and counts - print diff to terminal
def getRelationTypesAndCounts(edges1, edges2):
    relation_types_1 = ProvG_get_relations(edges1)
    relation_types_2 = ProvG_get_relations(edges2)

    def write_relation_types_to_file(relation_types, filename):
        with open(filename, 'w') as file:
            for key, count in relation_types.items():
                file.write(f"{key}: {count}\n")

    def get_relation_type(line):
        return line.split(":")[0]

    write_relation_types_to_file(relation_types_1, 'relation_types_1.txt')
    write_relation_types_to_file(relation_types_2, 'relation_types_2.txt')

    with open('relation_types_1.txt', 'r') as file1, open('relation_types_2.txt', 'r') as file2:
        lines1 = sorted(file1.readlines(), key=get_relation_type)
        lines2 = sorted(file2.readlines(), key=get_relation_type)

    diff = difflib.unified_diff(lines1, lines2)
    diff = sorted(diff, key=get_relation_type)
    print(''.join(diff))

    os.remove("relation_types_1.txt")
    os.remove("relation_types_2.txt")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path1", type=str, required=True,
                        help="Absolute path to the log file 1")
    parser.add_argument("--path2", type=str, required=True,
                        help="Absolute path to the log file 2")
    parser.add_argument("--relation", type=bool, required=False,
                        help="Get diffs in relation types and counts")
    args = parser.parse_args()

    log_file_path_1 = args.path1
    log_file_path_2 = args.path2
    get_relation_bool = args.relation

    # Generate Camflow Provenance Graph
    vertices1, edges1 = spade_json_load_graphs(log_file_path_1)
    vertices2, edges2 = spade_json_load_graphs(log_file_path_2)

    # Compare the pathname node path differences - generate an pathnameDiff.txt file
    getAllPathnamesAndCounts(vertices1, vertices2)

    # Get relation type and count diff if specified
    if (get_relation_bool):
        getRelationTypesAndCounts(edges1, edges2)

if __name__ == "__main__":
    main()

# baseLineApp = "/Users/michaelxi/Desktop/parser/logs/audit7.log" # no  jni + node filter + relation filter + do absolute nothing

# helloworld1 = "/Users/michaelxi/Desktop/parser/logs/audit1.log" # no  jni + node filter + relation filter
# helloworld2 = "/Users/michaelxi/Desktop/parser/logs/audit2.log" # no  jni + node filter
# helloworld3 = "/Users/michaelxi/Desktop/parser/logs/audit3.log" # has jni + node filter
# getUserLoc1 = "/Users/michaelxi/Desktop/parser/logs/audit4.log" # no  jni + node filter + relation filter

# writeFileExe = "/Users/michaelxi/Desktop/parser/camflow-examples/example-write-file.log" # executable + node filter + relation filter
# writeFileApp = "/Users/michaelxi/Desktop/parser/logs/audit5.log"                         # has jni    + node filter + relation filter + write to external storage
# readFileApp1 = "/Users/michaelxi/Desktop/parser/logs/audit6.log"                         # has jni    + node filter + relation filter + read /data/local/tmp file
# readFileApp2 = "/Users/michaelxi/Desktop/parser/logs/audit8.log"                         # no  jni    + node filter + relation filter + read /data/local/tmp file
# pinduoduoApp = "/Users/michaelxi/Desktop/parser/logs/audit-pdd.log"                      # ?   jni    + node filter + relation filter

# python3 provGraphDiff.py --path1 ./logs/audit7.log --path2 ./logs/audit1.log --relation true