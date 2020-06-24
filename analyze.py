import datetime
import json
import os

import numpy as np

import config

def analyze(db):

    for receiver in config.receivers:

        for filename in sorted(os.listdir(f"data/{receiver['ip']}")):

            if os.path.splitext(filename)[1] != ".json":
                continue

            base_filename = os.path.splitext(f"data/{receiver['ip']}/{filename}")[0]
            json_filename = base_filename + ".json"
            iq_filename = base_filename + ".dat"

            if not os.path.exists(iq_filename):
                print(f"{iq_filename} is missing!")
                continue

            if iq_filename in db["files"] and os.path.getmtime(json_filename) < os.path.getmtime("vmre_db.json"):
                continue

            if iq_filename not in db["files"]:
                db["files"][iq_filename] = {}

            print(f"Analyzing {iq_filename} from {receiver['ip']}.")

            params = json.load(open(json_filename, "r"))
            db["files"][iq_filename]["params"] = params

            # Extract parameters.
            bw = params["bandwidth"]
            datetime_started = datetime.datetime.strptime(params["datetime_started"], "%Y-%m-%d_%H-%M-%S.%f")

            notch_bw = config.notch_bw
            dt = config.dt
            n = config.n

            index_dt = int(dt*bw)
            iq_len = os.path.getsize(iq_filename) // 8
            power = np.zeros(int(iq_len // index_dt))
            f = open(iq_filename, "rb")

            for i in range(int(iq_len//index_dt)):

                f.seek(i*index_dt*8)

                # Load a chunk of the data for processing.
                iq_slice = np.fromfile(f, np.complex64, count=index_dt)
                iq_slice = iq_slice - np.mean(iq_slice)

                # Find the spectrum of the chunk.
                fft = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq_slice, n=n))))

                trim = n // 16
                fft = fft[trim:len(fft)-trim]

                # Notch out the center frequency.
                blank = notch_bw/bw*len(fft)
                for j in range(int(len(fft)/2-blank/2), int(len(fft)/2+blank/2)):
                    fft[j] = -np.Inf

                power[i] = (max(fft) - np.median(fft))

            #ind = np.argpartition(power, -5)[-5:]
            ind = []
            for p in range(len(power)):
                if power[p] > config.power_threshold:
                    ind.append(p)
            #ind = np.argwhere(power > 20)

            spec_width = 30
            spec_start = 5

            # Get rid of events that are within 30 seconds of each other.
            i = 1
            while True:
                if i >= len(ind):
                    break
                if (ind[i] - ind[i-1])*dt < 30:
                    del ind[i]
                else:
                    i += 1

            print(f"Found {len(ind)} events.")

            for i in ind:
                datetime_event = datetime_started + datetime.timedelta(seconds=i*dt)

                db["events"].append({
                    "file_path": iq_filename,
                    "file_index": i,
                    "id": len(db['events']),
                    "power": power[i],
                    "datetime_readable": datetime_event.strftime("%Y-%m-%d %H:%M:%S"),
                    "datetime_str": datetime_event.strftime('%Y-%m-%d_%H-%M-%S')
                })
