# PVOutput_extra.py

## Description

Python script to upload voltage (v6) and and consumption (v3, v4) data, obtained from a HomeWizard P1 meter, to PVOutput.org.
Gas is uploaded as extended data (v7). Use of extended data requires some additional configuration in the PVOutput.org web-interface. 

The script makes use of modules provided by:<br>
https://pypi.org/project/python-homewizard-energy/<br>
https://github.com/homewizard/python-homewizard-energy

Tested with version python-homewizard-energy-2.0.1
Tested on 2024-06-27 with version python-homewizard-energy-6.0.0

Update (2024-06-27):
python-homewizard-energy-3.0.0 introduces a (easy to resolve but) breaking change.
with commit https://github.com/homewizard/python-homewizard-energy/pull/276/commits/197bbf0ff7a8809026eb57bbcd50cf0a12851d59

## Python Preparation

Requires the following modules to be installed.
```
pip install python-homewizard-energy

or

python3 -m pip install python-homewizard-energy
```


## Environment Preparation
Create a pvoutput.env file with your System ID, API Key and line (phase) used for the solar installation.<br>
You can If more than one line (phase) is used, you can give a all used lines. The highest voltage will be used.<br>
E.g. possible options:<br>
1 2 3 12 23 13 123
The file can be located in your user directory (e.g. cd ~), and have your user ownership.


```
cd ~
echo export PVO_SYSTEMID=<systemid> > pvoutput.env
echo export PVO_APIKEY=<apikey> >> pvoutput.env
echo export SOLAR_LINE=3 >> pvoutput.env
```


## Startup (BASH) script
Create a shell or bash script to export the System ID and API Key as environment variables and start the Python script.
This script can be used at system startup (rc.local) or referenced in a Systemd configuration file.

Example start_PVOE.sh file.

```
mkdir ~/pvoutput
cd ~/pvoutput
sudo vi ~/pvoutput/start_PVOE.sh
```

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

Make the shell script executable and, if not already, owned by root:
```
sudo chown root:root ~/pvoutput/start_PVOE.sh
sudo chmod +x ~/pvoutput/start_PVOE.sh
```

## Systemd configuration file
Ref:<br>
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

Verify and start the PVOutput Extra service.
```
systemctl status pvoutput_extra.service
sudo systemctl start pvoutput_extra.service
```

other useful commands:
sudo systemctl stop pvoutput_extra.service
sudo systemctl restart pvoutput_extra.service


## Logging
Use Journalctl to obtain log details of the PVOutput_extra script.

```
journalctl --unit=pvoutput_extra.service -S "2024-01-01 01:00"
journalctl --unit=pvoutput_extra.service -f
```

## Extended data configuration

Configure Extended data via:<br>
https://pvoutput.org/ > System Editor (Edit system) > Extended Data > v7:<br>
You can use the following example configuration.<br>
* Color: #fe0071<br>
* select Line<br>
* Label: Gas<br>
* Unit: m3<br>
* Axis: 0<br>
* Summary: Change<br>
* Credit/Debit: Debit<br>
* \+ > Calculate as: Uncumulate

