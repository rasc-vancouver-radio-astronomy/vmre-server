from datetime import datetime
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

    index_template = Template(filename="templates/index.html")
    html_index = open("site/index.html", "w")
    html_index.write(index_template.render(db=db))

def create_plot_pages(db):

    plot_template = Template(filename="templates/plot.html")

    prev_event = None

    event_id = 0
    while event_id < len(db["events"]):

        event = db["events"][event_id]

        if event["interference"]:
            event_id += 1
            continue

        next_event_id = event_id + 1
        next_event = None

        while next_event_id < len(db["events"]) and db["events"][next_event_id]["interference"]:
            next_event_id += 1

        if next_event_id < len(db["events"]):
            next_event = db["events"][next_event_id]

        html_plot = open(f"site/event{event['id']}_{event['datetime_str']}.html", "w")
        html_plot.write(plot_template.render(
            db=db,
            event=event,
            prev_event=prev_event,
            next_event=next_event,
            config=config
        ))

        prev_event = event
        event_id += 1

