#!/usr/bin/env python3

import datetime as dt
import json
from multiprocessing import set_start_method
import os
import sqlite3
import time

from detect import detect
from plot import plot
from pages import pages

import config as cfg

def print_box(s):

    print("#" * (len(s) + 4))
    print(f"# {s} #")
    print("#" * (len(s) + 4))

def write_database(db):

    print(f"Writing database.")
    db["last_updated"] = dt.datetime.now().strftime(cfg.time_format)
    json.dump(db, open("vmre_db.json", "w"), indent=4, sort_keys=True)

def find_files(db):

    # Find the start and end datetimes for each file
    for station in cfg.stations.values():
        for filename in os.listdir(station["data_path"]):

            if os.path.splitext(filename)[1] != ".json":
                continue

            base_filename = os.path.splitext(f"{station['data_path']}/{filename}")[0]
            json_filename = base_filename + ".json"
            iq_filename = base_filename + ".dat"

            if not os.path.exists(iq_filename):
                print(f"{iq_filename} is missing!")
                continue
            
            file_size = os.path.getsize(iq_filename)

            if file_size == 0:
                print(f"{iq_filename} has size 0!")
                continue

            if file_size < 400000:
                print(f"{iq_filename} is too small! size {file_size}")
                continue

            try:
                params = json.load(open(json_filename, "r"))
            except:
                print(f"{json_filename} has JSON parse error!")
                continue

            if "bandwidth" not in params or "datetime_started" not in params or "center_frequency" not in params:
                print(f"{json_filename} is missing parameters!")
                continue

            datetime_started = dt.datetime.strptime(params["datetime_started"], cfg.time_format_data)

            today = dt.datetime.now()
            td = today - datetime_started
            if td.days > cfg.analyze_days:
                continue

            datetime_ended = datetime_started + dt.timedelta(seconds=(file_size//8)/params["bandwidth"])

            if iq_filename not in db["files"]:
            
                db["files"][iq_filename] = {
                    "filename": iq_filename,
                    "start": datetime_started.strftime(cfg.time_format),
                    "end": datetime_ended.strftime(cfg.time_format),
                    "bandwidth": params["bandwidth"],
                    "frequency": params["center_frequency"],
                    "station_id": params["station_id"],
                    "params": params,
                    "size": file_size
                }
            
            if iq_filename not in db["files"] or db["files"][iq_filename]["size"] != file_size:

                for tstr in db["analyzed"]:
                    t = dt.datetime.strptime(tstr, cfg.time_format)
                    if t >= datetime_started and t <= datetime_ended:
                        db["analyzed"][tstr] = False
                
                events_to_delete = []
                for event_id, event in enumerate(db["events"]):
                    t = dt.datetime.strptime(event["datetime_str"], cfg.time_format)
                    if t >= datetime_started and t <= datetime_ended:
                        events_to_delete.append(event_id)
                for event_id in reversed(events_to_delete):
                    del db["events"][event_id]

def main():

    set_start_method("spawn") # Fix multiprocessing library causing hangs

    start_time = time.time()

    print_box(f"VMRE run started. Time is {dt.datetime.now()}.")

    if os.path.exists("vmre_db.json"):
        print("Database found. Loading...")
        db = json.load(open("vmre_db.json", "r"))
    else:
        print("No database found. Creating a new one...")
        db = {
            "events": [],
            "files": {},
            "analyzed": {},
        }

    print("Updating analyzed array.")
    today = dt.datetime.strptime(dt.datetime.now().strftime("%Y%m%d"), "%Y%m%d")
    t0 = today - dt.timedelta(days=cfg.analyze_days) + dt.timedelta(days=1)
    for i in range(cfg.analyze_days*24*60*60 // cfg.dt):
        t = t0 + dt.timedelta(seconds=i*cfg.dt)
        if t.strftime(cfg.time_format) not in db["analyzed"]:
            db["analyzed"][t.strftime(cfg.time_format)] = False

    os.makedirs("html", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    print(f"Finding files. Time is {time.time() - start_time}.")
    find_files(db)

    print(f"Detecting events. Time is {time.time() - start_time}.")
    detect(db)

    write_database(db)

    print(f"Plotting data. Time is {time.time() - start_time}.")
    plot(db)

    print(f"Generating pages. Time is {time.time() - start_time}.")
    pages(db)

    print(f"VMRE run completed. Time is {time.time() - start_time}.")

if __name__ == "__main__":
    main()
