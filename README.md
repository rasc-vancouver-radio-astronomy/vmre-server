# Vancouver Meteor Radar Experiment Server

This is the server side software for the Vancouver Meteor Radar Experiment (VMRE). The project homepage is at [https://vmre.ca](https://vmre.ca). You can find the source code for the VMRE receiver software [here](https://github.com/preston-thompson/vmre-receiver).

This software runs on the VMRE server using an hourly cron job that executes `run.py && rsync.sh`. The VMRE receiver stations upload their data via rsync every hour.

