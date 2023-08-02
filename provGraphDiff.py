from provLogParser import spade_json_load_graphs
from provLogParser import ProvG_get_pathnames
from provLogParser import ProvG_get_relations

import difflib
import os

baseLineApp = "/Users/michaelxi/Desktop/parser/logs/audit7.log" # no  jni + node filter + relation filter + do absolute nothing

helloworld1 = "/Users/michaelxi/Desktop/parser/logs/audit1.log" # no  jni + node filter + relation filter
helloworld2 = "/Users/michaelxi/Desktop/parser/logs/audit2.log" # no  jni + node filter
helloworld3 = "/Users/michaelxi/Desktop/parser/logs/audit3.log" # has jni + node filter
getUserLoc1 = "/Users/michaelxi/Desktop/parser/logs/audit4.log" # no  jni + node filter + relation filter

writeFileExe = "/Users/michaelxi/Desktop/parser/camflow-examples/example-write-file.log" # executable + node filter + relation filter
writeFileApp = "/Users/michaelxi/Desktop/parser/logs/audit5.log"                         # has jni    + node filter + relation filter + write to external storage
readFileApp1 = "/Users/michaelxi/Desktop/parser/logs/audit6.log"                         # has jni    + node filter + relation filter + read /data/local/tmp file
readFileApp2 = "/Users/michaelxi/Desktop/parser/logs/audit8.log"                         # no  jni    + node filter + relation filter + read /data/local/tmp file
pinduoduoApp = "/Users/michaelxi/Desktop/parser/logs/audit-pdd.log"                      # ?   jni    + node filter + relation filter

############################ Get all pathnames and counts ############################

vertices1, edges1 = spade_json_load_graphs(baseLineApp)
vertices2, edges2 = spade_json_load_graphs(pinduoduoApp)

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


############################ Get relation types and counts ############################

relation_types_1 = ProvG_get_relations(edges1)
relation_types_2 = ProvG_get_relations(edges2)

def write_relation_types_to_file(relation_types, filename):
    with open(filename, 'w') as file:
        for key, count in relation_types.items():
            file.write(f"{key}: {count}\n")

def get_relation_type(line):
    """Helper function to extract relation type from line."""
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
