import os
import json
import gzip
import re
from tqdm import tqdm


fp = "dict-conjugated.json.gz"
with gzip.open(fp, "rt") as f:
    data = json.load(f)

defs = []
# "find words which end in eme or reme or neme"
for row in tqdm(data):
    # "find words which end in eme or reme or neme"
    if data.index(row) >= 4973 and re.search(r"([\wÀ-ÖØ-öø-ÿ'()-\[\]{}\"“”‘’]*?)eme(?=\W|$)" , row["d"]):
        # print the definition with the eme highlighted
        print(re.sub(r"([\wÀ-ÖØ-öø-ÿ'()-\[\]{}\"“”‘’]*?)eme(?=\W|$)", r"\1\033[1;31meme\033[0m", row["d"]))
        print()
        # add definition to the list
        resp = input()
         # if it's a ctrlc, break the loop
        if resp == "c":
            break
        # if resp is not none, add response to the list
        if resp:
            defs.append(resp)
       


print(len(defs))
# save the list to a file, each definition on a new line
with open("reme_defs.txt", "w+") as f:
    f.write("\n".join(defs))