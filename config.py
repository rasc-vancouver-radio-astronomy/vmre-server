receivers = [
    {
        "data_path": "/mnt/str/pri/vmre/data/jansky/",
    },
    {
        "data_path": "/mnt/str/pri/vmre/data/ken-surrey/",
    }
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
        "description": "Airspy R2 using VMRE antenna",
    },
    2: {
        "grid": "",
        "operator": "Ken Arthurs",
        "description": "Airspy R2 using VMRE antenna",
    },
    3: {
        "grid": "",
        "operator": "Ken Arthurs",
        "description": "RTL-SDR using VMRE antenna",
    },
}

# Analysis
power_threshold = 25
notch_bw = 20
dt = 5
n = 4096
#dt = 5
#n = 1024

spec_width = 40
spec_start = 10

NFFTs = [256, 512, 1024]
default_fft = 512

analyze_days = 14

