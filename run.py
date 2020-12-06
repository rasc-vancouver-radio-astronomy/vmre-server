#!/usr/bin/env python3

from datetime import datetime
import json
import os
import sqlite3
import time

from analyze import analyze
from fetch import fetch
from plot import plot
from pages import pages

import config

def print_box(s):

    print("#" * (len(s) + 4))
    print(f"# {s} #")
    print("#" * (len(s) + 4))

def scrub(db):

    events_to_delete = []

    for event_id, event in enumerate(db["events"]):

        datetime_event = datetime.strptime(event["datetime_str"], "%Y-%m-%d_%H-%M-%S")
        today = datetime.now()
        td = today - datetime_event
        if td.days > config.analyze_days:
            events_to_delete.append(event_id)

    for event_id in events_to_delete:

        print(f"Deleting event ID {event_id}.")
        del db["events"][event_id]

def main():

    start_time = time.time()

    print_box(f"VMRE run started. Time is {datetime.now()}.")
    print()

    if not os.path.exists("vmre_db.json"):
        print(f"VMRE database not found. Creating database.")
        db = {
            "events": [],
            "files": {}
        }
        json.dump(db, open("vmre_db.json", "w"))
    else:
        print(f"VMRE database found. Loading database.")
        db = json.load(open("vmre_db.json", "r"))
    print()

    os.makedirs("site", exist_ok=True)

    print(f"Scrubbing database. Time is {time.time() - start_time}.")
    scrub(db)
    print()

    print(f"Analyzing data. Time is {time.time() - start_time}.")
    analyze(db)
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
