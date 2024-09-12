#  Copyright (c) 2021.
#  This code has been produced by Zoran D. Grujic and by the knowledge found on The Internet.
#  Please feel free to ask me for permission to use my code in your own projects. It is for your own well fare!


import time
import os
import sys
# pip install python-libtiepie
import libtiepie


class oscilloscope:
    srs = {  # list of available sample rates @ 16 bit resolution
        "6.25 M": 6250000,
        "3.125 M": 3125000,
        "1.25 M": 1250000,
        "625 k": 625000
    }
    trigger_name = "Generator new period"
    channels = 0

    def __init__(self):
        # Search for devices:
        libtiepie.device_list.update()

        # Try to open an oscilloscope with block measurement support:
        self.scp = None
        scps = []
        for item in libtiepie.device_list:
            if item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE):
                scp = item.open_oscilloscope()
                if scp.measure_modes & libtiepie.MM_BLOCK:
                    scps.append(scp)
                    print('Found: ' + scp.name + ', s/n: ' + str(scp.serial_number))

        if len(scps) == 0:
            print("Oscilloscpe NOT found! Please connect the USB device!")
            return
        if len(scps) > 1:
            try:
                scp = libtiepie.device_list.create_and_open_combined_device(scps)
                # Remove scp objects, not required anymore:
                del scps
                self.scp = scp

            except Exception as e:
                print('Exception: ' + e.message)
                # try with single device
                self.scp = scps[0]
                print("Failed to combine instruments!")
        else:
            # This is single or combined instrument
            print("Found single oscilloscope.")
            self.scp = scps[0]

        # available vertical resolutions
        print("available resolutions: " + str(self.scp.resolutions))
        # print(self.scp._channels.__dict__)
        # print(self.scp._channels._get_count())
        self.channels = self.scp._channels._get_count()
        print(f"We have {self.channels} channels.")

    def set(self,
            mode="block",
            sample_rate=1e6,
            record_length=1e5,
            CH_ranges=[8, 2, 2, 2],
            CH_couplings=["dc", "dc", "dc", "dc"],
            ):
        if self.scp is None:
            return False
        if self.scp.is_running and self.scp.measure_mode == libtiepie.MM_STREAM:
            # not controllable
            return False
        try:
            # Set measure mode:
            if mode == "block":
                self.scp.measure_mode = libtiepie.MM_BLOCK
                # print("set measure_mode BLOCK")

                self.set_trigger()

            else:
                # print("set measure_mode STREAM")
                self.scp.measure_mode = libtiepie.MM_STREAM

            # set vertical resolution
            self.scp.resolution = 16  # set 16 bit vertical resolution
            # print("Sample frequency SET to:", self.scp.sample_rate)

            # Set record length:
            self.scp.record_length = int(record_length)  # 10000 samples

            # Set pre sample ratio:
            self.scp.pre_sample_ratio = 0  # 0 %

            # Set sample frequency:
            self.scp.sample_rate = sample_rate  # 1 MHz

            # For all channels:
            for i, ch in enumerate(self.scp.channels):
                # Enable channel to measure it:
                ch.enabled = True
                # Set range
                ch.range = CH_ranges[i]
                # Set coupling
                if CH_couplings[i] == 'dc':
                    ch.coupling = libtiepie.CK_DCV # DC Volt
                else:
                    ch.coupling = libtiepie.CK_ACV  # AC Volt
            """   
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
            """
            # Set trigger timeout:
            self.scp.trigger.timeout = 1000e-3  # 100 ms

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

    def set_trigger(self):

        """
        Combined instrument inputs:
        inp.id=19923200 inp.name='HS5-540XM(30553).EXT 1'
        inp.id=19923456 inp.name='HS5-540XM(30553).EXT 2'
        inp.id=19923712 inp.name='HS5-540XM(30553).EXT 3'
        inp.id=18874368 inp.name='HS5-540XM(30553).Generator start'
        inp.id=18874369 inp.name='HS5-540XM(30553).Generator stop'
        inp.id=18874370 inp.name='HS5-540XM(30553).Generator new period'

        """

        try:
            # Locate trigger input:
            trigger_input = self.scp.trigger_inputs.get_by_id(
                libtiepie.TIID_GENERATOR_NEW_PERIOD)  # or TIID_GENERATOR_START or TIID_GENERATOR_STOP
            # Set trigger timeout:
            self.scp.trigger.timeout = 1000e-3  # 100 ms

            if trigger_input is None:
                raise Exception('Unknown trigger input!')
        except Exception as e:
            # self.trigger_name = "Generator new period"
            for trigger_input in self.scp.trigger_inputs:
                #print(f"{trigger_input.id=} {trigger_input.name= }")
                if trigger_input.name.split(".")[-1] == self.trigger_name:
                    break




        # Enable trigger input:
        trigger_input.enabled = True
