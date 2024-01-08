#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 25 23:30:15 2023

@author: rhermsen

ToDo:
    - Verify if HomeWizard support mDNS (it should), and look to support this.
    - Include livingroom temperature, obtained external (AirGradient) in the extended data (v9).

Done:
    2024-01-08:
    - Allow a flexible use of parameters to be send to PVOutput, omid parameters with a none-type.
    2024-01-07:
    - Upload delta gas consumption as v8 (extended data).
    2024-01-06:
    - Upload gas consumtion as v7 (extended data).
    2024-01-05:
    - Obtain voltage line via os environment variable. If more than one is provided use the highest voltage value.
    2024-01-04: 
    -  I.s.o. asyncio.sleep(300) calculate the required delay to execute every 5min at xx min, 30 sec (where xx is 04, 09, 14, 19...)

"""

from homewizard_energy import HomeWizardEnergy
from homewizard_energy.models import Device, Data
import asyncio
import aiohttp
import json
from datetime import datetime
import os


PVOUTPUT_URL = 'http://pvoutput.org/service/r2/addstatus.jsp'
HOMEWIZARD_IP = '192.168.188.102'


class PVOutput(object):
    """
    Send the following information to PVOutput.org.
    
    v3 = Energy [Wh] Consumption, a cumulative value in Wh
    v4 = Power [W] Consumption, current power consumption in W
    v6 = Voltage (os.environ['SOLAR_LINE']), highest voltage if multiple lines are in us
    v7 = Gas [m3] Consumption, a cumulative value in m3
    v8 = Gas [m3] Consumption, increase from previous measurement in m3
    
    Ref:
        https://pvoutput.org/help/api_specification.html#add-status-service

    c1 = 3 (need to omit this flag becasue n=1.)
    n = 1
    """
    def __init__(self, timestamp, voltage=None, energy=None, power=None, gas=None, delta_gas=None):
        """
        Paramters to send to PVOutput.
        """
        self.pvoutput_systemid = os.environ['PVO_SYSTEMID']
        self.pvoutput_apikey = os.environ['PVO_APIKEY']
        self.timestamp = timestamp
        self.voltage = voltage
        self.energy = energy
        self.power = power
        self.gas = gas
        self.delta_gas = delta_gas

    async def uploadData(self):
        """
        Upload the measurement paramters.
        """
        # pvoutputdata = {
        # 'd': self.timestamp.strftime("%Y%m%d"),
        # 't': self.timestamp.strftime("%H:%M"),
        # 'v3': str(self.energy),
        # 'v4': str(self.power),
        # 'v6': str(self.voltage),
        # 'v7': str(self.gas),
        # 'v8': str(self.delta_gas),
        # 'n': '1'
        # }

        pvoutputdata = {
                'd': self.timestamp.strftime("%Y%m%d"),
                't': self.timestamp.strftime("%H:%M")
        }
        if self.voltage != None:
            pvoutputdata['v6'] = self.voltage
        if self.energy != None:
            pvoutputdata['v3'] = self.energy
        if self.power != None:
            pvoutputdata['v4'] = self.power
        if self.gas != None:
            pvoutputdata['v7'] = self.gas
        if self.delta_gas != None:
            pvoutputdata['v8'] = self.delta_gas
        pvoutputdata['n'] = '1'

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
    """
    Obtain measurement values from the P1 smartmeter using HomeWizard P1 meter.
    All device information and measurement data is requested.
    """
    def __init__(self, old_gas):
        self.device = None
        self.data = None
        self.last_data = None
        self.old_gas = old_gas
        self.line = os.environ['SOLAR_LINE']
        #self.line = '123'
    
    # Make contact with a energy device
    async def contactHW(self, host):
        async with HomeWizardEnergy(host) as api:
            # Obtain device details and current data
            self.device = await api.device()
            self.data = await api.data()
            self.last_data = datetime.now()
    
    def get_pv_line_voltage(self):
        """
        V6, Voltage of the line (phase) with the solar installation.
        If multiple lines are configured, the highest voltage is returned.
        """
        voltage = []
        for l in self.line:
            if l == '1':
                voltage.append(self.data.active_voltage_l1_v)
            elif l == '2':
                voltage.append(self.data.active_voltage_l2_v)
            elif l == '3':
                voltage.append(self.data.active_voltage_l3_v)
        #print("Voltage list =", voltage, "max = ", max(voltage))
        return max(voltage)
    
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

    def get_gas_consumption(self):
        """
        v7, Total cumulative [m3] imported gas.
        Extended data which needs configured via Web-GUI e.g.:
        Extended Data > v7: 
            color : #c9244d, Area
            Label: Gas, Unit: m3, 
            Axis: 0, Summary: Change
            Credit/Debit: Debit
            + > Calculate as: Uncumulate
        """
        return self.data.total_gas_m3
    
    def get_delta_gas_consumption(self):
        """
        v8, Gas usage in the last 5 minutes.
        Extended data which needs configured via Web-GUI e.g.:
        Extended Data > v8: 
            color : #fe0071, Line
            Label: Gas, Unit: m3, 
            Axis: 0, Summary: Change
            Credit/Debit: Debit
        """
        if self.old_gas == None:
            return 0
        else:
           return self.data.total_gas_m3 - self.old_gas


class AirGradient(object):
    """
    """
    def __init__(self):
        self.url = "http://192.168.188.100:8080/metricsjson"
    
    async def get_temp(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                json_data = await response.text()
                data_dict = json.loads(json_data)
                return data_dict["temp"]


async def main():
    print(f'PVOutput.py has started at {datetime.now().strftime("%Y%m%d %H:%M:%S")}, and should run infinity.')
    old_gas = None
    while True:
        now = datetime.now()
        delay = (4 - (now.minute % 5)) * 60 + (30 - now.second)
        if delay < 0:
            delay = 300 + delay
        #print("Delay =", delay, "Time now =", now.strftime("%Y%m%d %H:%M:%S"))
        await asyncio.sleep(delay)        
        try:
            getData = HomeEnergy(old_gas)
            await asyncio.gather(getData.contactHW(HOMEWIZARD_IP))
            print("Data obtained at:", getData.get_collection_timestamp(), 
                  "V6_Voltage:", getData.get_pv_line_voltage(),
                  "V1_Energy_gen:", getData.get_energy_generation(), 
                  "V3_Energy:", getData.get_energy_consumption(), 
                  "V4_Power:", getData.get_power_consumption(), 
                  "V7_Gas:", getData.get_gas_consumption(),
                  "v8_Gas delta", getData.get_delta_gas_consumption())
            # getTemp = AirGradient()
            # await asyncio.gather(getTemp.get_temp())
        except Exception as e:
            exception_time = datetime.now().strftime("%Y%m%d %H:%M:%S")
            print(f"Failed reading HomeEnergy at {exception_time} - ErrorType : {type(e).__name__}, Error : {e}")
        else:
            try:
                sendData = PVOutput(getData.get_collection_timestamp(), 
                                    getData.get_pv_line_voltage(),
                                    getData.get_energy_consumption(),
                                    getData.get_power_consumption(),
                                    getData.get_gas_consumption(),
                                    getData.get_delta_gas_consumption())
                await asyncio.gather(sendData.uploadData())
                old_gas = getData.get_gas_consumption()
            except Exception as e:
                exception_time = datetime.now().strftime("%Y%m%d %H:%M:%S")
                print(f"Failed to send data at {exception_time} - ErrorType : {type(e).__name__}, Error : {e}")
        await asyncio.sleep(5)
    print("Done")

asyncio.run(main())



