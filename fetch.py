import config
import os
import subprocess

def rsync(src, dst, port=22):

    args = ["rsync", "-av", "--size-only", "-e", f"ssh -p {port}", src, dst]
    rv = subprocess.call(args)
    return rv

def fetch():

    for receiver in config.receivers:

        print(f"Fetching from {receiver['ip']}.")

        data_path = f"data/{receiver['ip']}/"
        os.makedirs(data_path, exist_ok=True)
        rsync(f"{receiver['ip']}:{receiver['data_path']}", data_path, port=receiver["ssh_port"])
