import datetime
import json
import os

import numpy as np

import config

def analyze(db):

    highest_event_id = -1
    for e in db["events"]:
        if e["id"] > highest_event_id:
            highest_event_id = e["id"]

    for receiver in config.receivers:

        print(f"Analyzing files for receiver {receiver}")

        for filename in sorted(os.listdir(receiver["data_path"])):

            if os.path.splitext(filename)[1] != ".json":
                continue

            base_filename = os.path.splitext(f"{receiver['data_path']}/{filename}")[0]
            json_filename = base_filename + ".json"
            iq_filename = base_filename + ".dat"
            csv_filename = "site/" + os.path.split(base_filename)[1] + ".csv"

            if not os.path.exists(iq_filename):
                print(f"{iq_filename} is missing!")
                continue

            if iq_filename in db["files"] and os.path.getsize(iq_filename) == db["files"][iq_filename]["size"]:
                print(f"Skipping {iq_filename} because file size matches database.")
                continue

            print(f"Reading {json_filename}...")
            try:
                params = json.load(open(json_filename, "r"))
            except:
                print(f"Skipping {json_filename} due to JSON parse error.")
                continue
            datetime_started = datetime.datetime.strptime(params["datetime_started"], "%Y-%m-%d_%H-%M-%S.%f")
            today = datetime.datetime.now()
            td = today - datetime_started
            if td.days > config.analyze_days:
                print(f"Skipping {iq_filename} because it's older than {config.analyze_days} days.")
                continue

            if iq_filename not in db["files"]:
                print(f"Creating new DB entry for {iq_filename}.")
                db["files"][iq_filename] = {"size": 0}

            db["files"][iq_filename]["params"] = params

            if "station_id" not in db["files"][iq_filename]["params"]:
                db["files"][iq_filename]["params"]["station_id"] = 0

            # Extract parameters.
            bw = params["bandwidth"]


            print(f"Analyzing {iq_filename}.")

            notch_bw = config.notch_bw
            dt = config.dt
            n = config.n

            index_dt = int(dt*bw)
            iq_len = os.path.getsize(iq_filename) // 8
            start_index = db["files"][iq_filename]["size"] // 8
            db["files"][iq_filename]["size"] = os.path.getsize(iq_filename)
            power = np.zeros(int(iq_len // index_dt))
            f = open(iq_filename, "rb")

            for i in range(start_index, int(iq_len//index_dt)):

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

            if "power_csv" not in db:
                db["power_csv"] = []
            db["power_csv"].append(csv_filename)
            with open(csv_filename, "w") as f:
                for p in power:
                    f.write(f"{p}\n")

            #ind = np.argpartition(power, -5)[-5:]
            # ind = []
            # for p in range(len(power)):
            #     if power[p] > config.power_threshold:
            #         ind.append(p)
            #ind = np.argwhere(power > 20)

            # Author: William Wall

            wrsig = 100
            sn_thr = 8

            rmean = power - power
            rsig = power - power
            rmed = power - power

            for ii in range(len(power)):
                bi = ii-wrsig
                if bi < 0:
                    bi = 0
                ei = ii+wrsig+1
                if ei > len(power):
                    ei = len(power)
                rmean[ii] = np.mean(power[bi:ei])
                rsig[ii] = np.std(power[bi:ei])
                rmed[ii] = np.median(power[bi:ei])

            thresh = rmean + sn_thr*rsig
            rdat = 1.*power
            loc_thr = power > thresh
            rdat[loc_thr] = rmed[loc_thr]
            num_pk = len(np.where(loc_thr)[0])
            num_pks = 1*num_pk

            counter = 0
            while num_pks != 0:
                counter = counter + 1
                for ii in range(len(rdat)):
                    bi = ii-wrsig
                    if bi < 0:
                        bi = 0
                    ei = ii+wrsig+1
                    if ei > len(rdat):
                        ei = len(rdat)
                    rmean[ii] = np.mean(rdat[bi:ei])
                    rsig[ii] = np.std(rdat[bi:ei])
                    rmed[ii] = np.median(rdat[bi:ei])
                thresh = rmean + sn_thr*rsig
                loc_thr = rdat > thresh
                rdat[loc_thr] = rmed[loc_thr]
                num_pks = len(np.where(loc_thr)[0])

            ind = np.where(power > thresh)[0].tolist()

            # End of William's code.

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

                highest_event_id += 1

                db["events"].append({
                    "file_path": iq_filename,
                    "file_index": i,
                    "id": highest_event_id,
                    "power": power[i],
                    "datetime_readable": datetime_event.strftime("%Y-%m-%d %H:%M:%S"),
                    "datetime_str": datetime_event.strftime('%Y-%m-%d_%H-%M-%S'),
                    "interference": False,
                })
