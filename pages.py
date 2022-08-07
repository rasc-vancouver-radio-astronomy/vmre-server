import datetime
import os
from shutil import copyfile

from mako.template import Template

import config

def pages(db):

    create_index_page(db)
    create_plot_pages(db)
    files_to_copy = (
        "manual.html",
        "rasc-new-banner.png",
        "style.css",
    )
    for f in files_to_copy:
        copyfile(f"static/{f}", f"{config.html_path}/{f}")

def create_index_page(db):

    stations_last_seen = {}
    stations_ok = {}

    for datafile in db["files"].values():
        station_id = datafile["params"]["station_id"]
        datafile_start_time = datetime.datetime.strptime(datafile["params"]["datetime_started"], config.time_format_data)
        datafile_end_time = datafile_start_time + datetime.timedelta(seconds=datafile["size"]/8/datafile["params"]["bandwidth"])
        if station_id not in stations_last_seen:
            stations_last_seen[station_id] = datafile_end_time
        elif stations_last_seen[station_id] < datafile_end_time:
            stations_last_seen[station_id] = datafile_end_time

    for station_id in stations_last_seen:
        if (datetime.datetime.now() - stations_last_seen[station_id]).total_seconds() > (2*60*60):
            stations_ok[station_id] = False
        else:
            stations_ok[station_id] = True

    for station_id in stations_last_seen:
        stations_last_seen[station_id] = datetime.datetime.strftime(stations_last_seen[station_id], config.time_format_readable)

    index_template = Template(filename="templates/index.html")
    html_index = open(f"{config.html_path}/index.html", "w")
    html_index.write(index_template.render(db=db, config=config, stations_last_seen=stations_last_seen, stations_ok=stations_ok))

def create_plot_pages(db):

    plot_template = Template(filename="templates/plot.html")

    prev_event = None

    events_to_plot = []

    for event in sorted(db["events"].values(), key=lambda item: item["datetime_str"]):

        events_to_plot.append(event)

    for i in range(len(events_to_plot)):

        event = events_to_plot[i]

        if i > 0:
            prev_event = events_to_plot[i-1]
        else:
            prev_event = None

        if i < len(events_to_plot)-1:
            next_event = events_to_plot[i+1]
        else:
            next_event = None

        html_plot = open(f"{config.html_path}/{event['datetime_str']}.html", "w")
        html_plot.write(plot_template.render(
            db=db,
            event=event,
            prev_event=prev_event,
            next_event=next_event,
            config=config
        ))

