receivers = [
    {
        "data_path": "/rvra/vmre/data/jansky",
    },
    {
        "data_path": "/rvra/vmre/data/ken-surrey",
    },
    {
        "data_path": "/rvra/vmre/data/rasc-macbook",
    },
]

stations = {
    0: {
        "grid": "",
        "operator": "Unknown",
        "description": "",
    },
    1: {
        "grid": "CN89og",
        "operator": "Preston Thompson",
    },
    2: {
        "grid": "",
        "operator": "Ken Arthurs",
    },
    3: {
        "grid": "",
        "operator": "Ken Arthurs",
    },
}

# Analysis
power_threshold = 5
dt = 10
n = 1024

spec_width = 40
spec_start = 10

NFFTs = [256, 512, 1024]
default_fft = 512

analyze_days = 20
