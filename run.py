#!/usr/bin/env python3

from datetime import datetime
import json
from multiprocessing import set_start_method
import os
import sqlite3
import time

from power import power
from events import events
from plot import plot
from pages import pages

import config

def print_box(s):

    print("#" * (len(s) + 4))
    print(f"# {s} #")
    print("#" * (len(s) + 4))

def main():

    set_start_method("spawn") # Fix multiprocessing library causing hangs

    start_time = time.time()

    print_box(f"VMRE run started. Time is {datetime.now()}.")
    print()

    db = {
        "events": [],
        "files": {}
    }

    os.makedirs("html", exist_ok=True)
    os.makedirs("events", exist_ok=True)
    os.makedirs("power", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    print(f"Calculating power series. Time is {time.time() - start_time}.")
    power(db)
    print()


    print(f"Finding events. Time is {time.time() - start_time}.")
    events(db)
    print()


    print(f"Writing database. Time is {time.time() - start_time}.")
    json.dump(db, open("vmre_db.json", "w"), indent=4, sort_keys=True)
    print()


    print(f"Plotting data. Time is {time.time() - start_time}.")
    plot(db)
    print()

    print(f"Writing database. Time is {time.time() - start_time}.")
    db["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json.dump(db, open("vmre_db.json", "w"), indent=4, sort_keys=True)
    print()

    print(f"Generating pages. Time is {time.time() - start_time}.")
    pages(db)
    print()

    print(f"VMRE run completed. Time is {time.time() - start_time}.")

if __name__ == "__main__":
    main()
