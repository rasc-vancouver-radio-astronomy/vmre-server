import datetime
import os
from shutil import copyfile

from mako.template import Template

import config

def pages(db):

    os.makedirs("site", exist_ok=True)
    copyfile("templates/style.css", "site/style.css")
    create_index_page(db)
    create_plot_pages(db)

def create_index_page(db):

    availability = {}
    for station_id in config.stations:
        if station_id == 0:
            continue
        availability[station_id] = [False]*config.analyze_days

    today = datetime.datetime.now()
    for file_path in db["files"]:
        f = db["files"][file_path]
        datetime_started = datetime.datetime.strptime(f["params"]["datetime_started"], "%Y-%m-%d_%H-%M-%S.%f")
        station_id = f["params"]["station_id"]
        td = today - datetime_started
        if td.days < config.analyze_days:
            availability[f["params"]["station_id"]][td.days] = True
    
    for s in availability:
        availability[s].reverse()

    availability_dates = []
    for i in range(config.analyze_days):
        availability_dates.append((datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%m-%d"))
    availability_dates.reverse()

    near_events = []
    events_ordered = sorted(db['events'], key=lambda k: k['datetime_str'])
    for idx in range(1, len(events_ordered)):
        e2 = events_ordered[idx]
        e1 = events_ordered[idx-1]
        if db["files"][e2["file_path"]]["params"]["station_id"] == db["files"][e1["file_path"]]["params"]["station_id"]:
            continue
        t2 = datetime.datetime.strptime(e2['datetime_str'], "%Y-%m-%d_%H-%M-%S")
        t1 = datetime.datetime.strptime(e1['datetime_str'], "%Y-%m-%d_%H-%M-%S")
        dt = t2-t1
        if dt.days<1 and dt.seconds<(5*60):
            near_events.append(events_ordered[idx-1])
            near_events.append(events_ordered[idx])

    index_template = Template(filename="templates/index.html")
    html_index = open("site/index.html", "w")
    html_index.write(index_template.render(db=db, config=config, availability=availability, availability_dates=availability_dates, near_events=near_events))

def create_plot_pages(db):

    plot_template = Template(filename="templates/plot.html")

    prev_event = None

    events_to_plot = []

    for event in sorted(db["events"], key=lambda item: item["datetime_str"]):

        if event["interference"]:
            continue

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

        html_plot = open(f"site/event{event['id']}_{event['datetime_str']}.html", "w")
        html_plot.write(plot_template.render(
            db=db,
            event=event,
            prev_event=prev_event,
            next_event=next_event,
            config=config
        ))

