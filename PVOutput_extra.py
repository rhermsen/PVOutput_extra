#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 25 23:30:15 2023

@author: rhermsen

ToDo:
    - Verify if HomeWizard support mDNS (it should), and look to support this.
    - Obtain voltage line via os environment variable. If more than one is provided use the highest voltage value.
    -  I.s.o. asyncio.sleep(300) calculate the required delay to execute every 5min at xx min, 30 sec (where xx is 04, 09, 14, 19...)

"""

from homewizard_energy import HomeWizardEnergy
from homewizard_energy.models import Device, Data
import asyncio
import aiohttp
from datetime import datetime
import os


PVOUTPUT_URL = 'http://pvoutput.org/service/r2/addstatus.jsp'
HOMEWIZARD_IP = '192.168.188.102'


class PVOutput(object):
    """
    Send the following information to PVOutput.org every send_interval (5 min).
    v6 = Voltage (Line3)
    v3 = Energy [Wh] Consumption, a cumulative value in Wh
    v4 = Power [W] Consumption, current power consumption in W
    
    Ref:
        https://pvoutput.org/help/api_specification.html#add-status-service

    c1 = 3 (need to omit this flag becasue n=1.)
    n = 1
    """
    def __init__(self, timestamp, voltage, energy, power):
        """
        Read the required data from HomeWizard and send it to PVOutput.
        """
        self.pvoutput_systemid = os.environ['PVO_SYSTEMID']
        self.pvoutput_apikey = os.environ['PVO_APIKEY']
        self.timestamp = timestamp
        self.voltage = voltage
        self.energy = energy
        self.power = power

    async def uploadData(self):
        pvoutputdata = {
        'd': self.timestamp.strftime("%Y%m%d"),
        't': self.timestamp.strftime("%H:%M"),
        'v3': str(self.energy),
        'v4': str(self.power),
        'v6': str(self.voltage),
        'n': '1'
        }

        headerspv = {
            'X-Pvoutput-SystemId': self.pvoutput_systemid,
            'X-Pvoutput-Apikey': self.pvoutput_apikey
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(PVOUTPUT_URL, headers=headerspv, data=pvoutputdata) as response:
                response_string = await response.text()
                if str(response.status) != "200":
                    print("Response error: ", response_string)
                # print("Response status:", response.status, "Response reason:", response.reason)
                # print("Response: " + str(response.status) + " updated: " + str(self.timestamp) + " voltage: " + str(self.voltage))


class HomeEnergy(object):
    def __init__(self):
        self.device = None
        self.data = None
        self.last_data = None
    
    # Make contact with a energy device
    async def contactHW(self, host):
        async with HomeWizardEnergy(host) as api:
            # Obtain device details and current data
            self.device = await api.device()
            self.data = await api.data()
            self.last_data = datetime.now()
    
    def get_pv_line_voltage(self):
        return self.data.active_voltage_l3_v
    
    def get_energy_consumption(self):
        """
        V3, Total cumulative [Wh] imported energy from the net.
        Imported = Consumption - Generation
        """
        return int(self.data.total_power_import_kwh * 1000)
    
    def get_energy_generation(self):
        """
        V1, Total cumulative [Wh] exported energy back into the net.
        Exported = Generation - Consumption
        """
        return int(self.data.total_power_export_kwh * 1000)
    
    def get_power_consumption(self):
        """
        v4, Current [W] consumption.
        Positive = consumption
        Negative = generation
        """
        return self.data.active_power_w
    
    def get_collection_timestamp(self):
        return self.last_data
    
    def set_collection_timestamp_none(self):
        self.last_data = None


async def main():
    print(f'PVOutput.py has started at {datetime.now().strftime("%Y%m%d %H:%M")}, and should run infinity.')
    while True:
        try:
            getData = HomeEnergy()
            await asyncio.gather(getData.contactHW(HOMEWIZARD_IP))
            print("Data obtained at:", getData.get_collection_timestamp(), "V6_Voltage:", getData.get_pv_line_voltage(),"V1_Energy_gen:", getData.get_energy_generation(), "V3_Energy:", getData.get_energy_consumption(), "V4_Power:", getData.get_power_consumption() )
        except:
            print(f'Failed reading HomeEnergy at {datetime.now().strftime("%Y%m%d %H:%M")}.')
        else:
            try:
                sendData = PVOutput(getData.get_collection_timestamp(), 
                                    getData.get_pv_line_voltage(),
                                    getData.get_energy_consumption(),
                                    getData.get_power_consumption())
                await asyncio.gather(sendData.uploadData())
            except:
                print(f'Failed to send data at {datetime.now().strftime("%Y%m%d %H:%M")}')
        await asyncio.sleep(300)
    print("Done")

asyncio.run(main())



