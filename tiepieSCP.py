#  Copyright (c) 2021.
#  This code has been produced by Zoran D. Grujic and by the knowledge found on The Internet.
#  Please feel free to ask me for permission to use my code in your own projects. It is for your own well fare!


import time
import os
import sys
import libtiepie


class oscilloscope:
    srs = {  # list of available sample rates @ 16 bit resolution
        "6.25 M": 6250000,
        "3.125 M": 3125000,
        "1.25 M": 1250000,
        "625 k": 625000
    }

    def __init__(self):
        # Search for devices:
        libtiepie.device_list.update()

        # Try to open an oscilloscope with block measurement support:
        self.scp = None
        for item in libtiepie.device_list:
            if item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE):
                self.scp = item.open_oscilloscope()
                if self.scp.measure_modes & libtiepie.MM_BLOCK:
                    break
                else:
                    scp = None
        if self.scp is None:
            print("No oscilloscpe found! Please connect the USB device!")
            return
        # available vertical resolutions
        print(self.scp.resolutions)

    def set(self,
            mode="block",
            sample_frequency=1e6,
            record_length=1e5,
            CH1_range=8,
            CH2_range=2,
            CH1_coupling="dc",
            CH2_coupling="dc"):
        if self.scp is None:
            return False
        if self.scp.is_running and self.scp.measure_mode == libtiepie.MM_STREAM:
            # not controlable
            return False
        try:
            # Set measure mode:
            if mode == "block":
                self.scp.measure_mode = libtiepie.MM_BLOCK
                # print("set measure_mode BLOCK")
                # Locate trigger input:
                trigger_input = self.scp.trigger_inputs.get_by_id(
                    libtiepie.TIID_GENERATOR_NEW_PERIOD)  # or TIID_GENERATOR_START or TIID_GENERATOR_STOP

                if trigger_input is None:
                    raise Exception('Unknown trigger input!')

                # Enable trigger input:
                trigger_input.enabled = True
            else:
                # print("set measure_mode STREAM")
                self.scp.measure_mode = libtiepie.MM_STREAM


            # Set sample frequency:
            self.scp.sample_frequency = sample_frequency  # 1 MHz

            # set vertical resolution
            self.scp.resolution = 16  # set 16 bit vertical resolution
            # print("Sample frequency SET to:", self.scp.sample_frequency)

            # Set record length:
            self.scp.record_length = int(record_length)  # 10000 samples

            # Set pre sample ratio:
            self.scp.pre_sample_ratio = 0  # 0 %

            # For all channels:
            for ch in self.scp.channels:
                # Enable channel to measure it:
                ch.enabled = True
            CH1 = self.scp.channels[0]
            CH2 = self.scp.channels[1]

            # Set range:
            CH1.range = CH1_range
            CH2.range = CH2_range

            # Set coupling:
            if CH1_coupling == 'dc':
                CH1.coupling = libtiepie.CK_DCV  # DC Volt
            else:
                CH1.coupling = libtiepie.CK_ACV  # AC Volt
            if CH2_coupling == 'dc':
                CH2.coupling = libtiepie.CK_DCV  # DC Volt
            else:
                CH2.coupling = libtiepie.CK_ACV  # AC Volt

            # Set trigger timeout:
            self.scp.trigger_time_out = 1000e-3  # 100 ms

            # Disable all channel trigger sources:
            for ch in self.scp.channels:
                ch.trigger.enabled = False

            if mode != "block":
                # Setup channel trigger:
                ch = self.scp.channels[0]  # Ch 1

                # Enable trigger source:
                ch.trigger.enabled = True

                # Kind:
                ch.trigger.kind = libtiepie.TK_RISINGEDGE  # Rising edge

                # Level:
                ch.trigger.levels[0] = 0.5  # 50 %

                # Hysteresis:
                ch.trigger.hystereses[0] = 0.05  # 5 %

            return True

        except Exception as e:
            print('Exception: ' + str(e))
            return False
            # sys.exit(1)

    def getBlock(self):
        # Start measurement:
        self.scp.start()

        # Wait for measurement to complete:
        while not self.scp.is_data_ready:
            time.sleep(0.01)  # 10 ms delay, to save CPU time

        # Get data:
        data = self.scp.get_data()
        try:
            self.scp.stop()
        except Exception as e:
            pass
        return data

    def getBlockS(self):
        # Start measurement:
        if self.scp.is_running:
            self.scp.stop()

        self.scp.start()
        while True:
            # Wait for measurement to complete:
            while not self.scp.is_data_ready:
                time.sleep(0.01)  # 10 ms delay, to save CPU time

            # Get data:
            data = self.scp.get_data()

        try:
            self.scp.stop()
        except Exception as e:
            pass
        return data
