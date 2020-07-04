#!/usr/bin/env python3

import json
import sys

db = json.load(open("vmre_db.json", "r"))

for i in range(len(sys.argv)-1):
    
    db["events"][int(sys.argv[i+1])]["interference"] = True

json.dump(db, open("vmre_db.json", "w"), indent=4, sort_keys=True)

