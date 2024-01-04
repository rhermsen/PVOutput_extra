# PVOutput_extra.py

## Description

Python script to upload voltage (v6) and and consumption (v3, v4) data, obtained from a HomeWizard P1 meter, to PVOutput.org.

The script makes use of modules provided by:
https://pypi.org/project/python-homewizard-energy/
https://github.com/homewizard/python-homewizard-energy

Tested with version python-homewizard-energy-2.0.1


## Python Preparation

Requires the following modules to be installed.
```
pip install python-homewizard-energy

or

python3 -m pip install python-homewizard-energy
```


## Environment Preparation
Create a pvoutput.env file with your System ID and API Key.
The file can be located in your user directory (e.g. cd ~), and have your user ownership.

```
cd ~
echo export PVO_SYSTEMID=<systemid> > pvoutput.env
echo export PVO_APIKEY=<apikey> >> pvoutput.env
```


## Startup (BASH) script
Create a shell or bash script to export the System ID and API Key as environment variables and start the Python script.
This script can be used at system startup (rc.local) or referenced in a Systemd configuration file.

Example start_PVOE.sh file.
```
#!/usr/bin/bash

# Script to set the required environment variables, and start the 
# Python script /home/<user>/pvoutput/PVOutput_extra.py

# This script should be executable, and owned by root.
#
# Ron Hermsen
# 2023-12-19
#
# If this script is stared via ssh use:  sudo ./start_PVOE.sh &
# If started from another script or rc.local use: /home/<user>/pvoutput/PVOutput_extra.py >> /var/log/pvoutpute.log

source /home/<user>/pvoutput.env

cd /home/<user>/pvoutput
python3 /home/<user>/pvoutput/PVOutput_extra.py 
```

## Systemd configuration file
Ref:
https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#Command%20lines

```
sudo vi /etc/systemd/system/pvoutput_extra.service
```

```
[Unit]
Description=PVOutput extra data uploader

[Service]
Type=simple
ExecStart=/home/<user>/pvoutput/start_PVOE.sh

[Install]
WantedBy=multi-user.target
```

To have the service started at bootup.
```
sudo systemctl enable pvoutput_extra.service
```

start the PVOutput Extra service.
systemctl status pvoutput_extra.service
sudo systemctl start pvoutput_extra.service

other useful commands:
sudo systemctl stop pvoutput_extra.service
sudo systemctl restart pvoutput_extra.service


## Logging
Use Journalctl to obtain log details of the PVOutput_extra script.

```
journalctl --unit=pvoutput_extra.service -S "2024-01-01 01:00"
journalctl --unit=pvoutput_extra.service -f
```