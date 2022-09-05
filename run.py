#!/usr/bin/env python3

import datetime as dt
import json
from multiprocessing import set_start_method
import os
import time

from detect import detect
from plot import plot

import config as cfg

def print_box(s):

    print("#" * (len(s) + 4))
    print(f"# {s} #")
    print("#" * (len(s) + 4))

def write_database(db):

    print(f"Writing database.")
    now = dt.datetime.now()
    db["last_updated"] = now.strftime(cfg.time_format)
    db["last_updated_readable"] = now.strftime(cfg.time_format_readable)
    json.dump(db, open(f"{cfg.site_path}/db.json", "w"), indent=4, sort_keys=True)

def find_files():

    files = []

    # Find the start and end datetimes for each file
    for station in cfg.stations:
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

            params_list = ("bandwidth", "datetime_started", "center_frequency")
            missing = False
            for param in params_list:
                if param not in params:
                    print(f"{json_filename} is missing parameter {param}!")
                    missing = True
            if missing:
                continue

            if "station_id" not in params:
                params["station_id"] = station["station_id"]

            datetime_started = dt.datetime.strptime(params["datetime_started"], cfg.time_format_data)
            datetime_ended = datetime_started + dt.timedelta(seconds=(file_size//8)/params["bandwidth"])

            if (dt.datetime.now()-datetime_ended).days > cfg.days:
                continue

            files.append({
                "filename": iq_filename,
                "start": datetime_started,
                "end": datetime_ended,
                "bandwidth": params["bandwidth"],
                "frequency": params["center_frequency"],
                "station_id": params["station_id"],
                "params": params,
                "size": file_size,
            })

    return files

def scrub_events(db):

    t_start = (dt.datetime.now() - dt.timedelta(days=cfg.days)).replace(hour=0,minute=0,second=0,microsecond=0)

    delete_events = []

    for id,event in enumerate(db["events"]):
        event_datetime = dt.datetime.strptime(event["datetime_str"], cfg.time_format)
        if event_datetime >= t_start:
            delete_events.append(id)

    for id in reversed(delete_events):
        del db["events"][id]

def main():

    set_start_method("spawn") # Fix multiprocessing library causing hangs

    start_time = time.time()

    print_box(f"VMRE run started. Time is {dt.datetime.now()}.")

    if os.path.exists(f"{cfg.site_path}/db.json"):
        print("Database found. Loading...")
        db = json.load(open(f"{cfg.site_path}/db.json", "r"))
        print("Scrubbing database...")
        scrub_events(db)
    else:
        print("No database found. Creating a new one...")
        db = {
            "events": [],
        }

    os.makedirs(f"{cfg.site_path}/plots", exist_ok=True)

    print(f"Finding files. Time is {time.time() - start_time}.")
    files = find_files()

    print(f"Detecting events. Time is {time.time() - start_time}.")
    detect(db, files)

    write_database(db)

    print(f"Plotting data. Time is {time.time() - start_time}.")
    plot(db, files)

    print(f"VMRE run completed. Time is {time.time() - start_time}.")

if __name__ == "__main__":
    main()
