#  Copyright (c) 2021.
#  This code has been produced by Zoran D. Grujic and by the knowledge found on The Internet.
#  Please feel free to ask me for permission to use my code in your own projects. It is for your own well fare!


import time
import os
import sys
# pip install python-libtiepie
import libtiepie
from sympy.strategies.core import switch


class oscilloscope:
    srs = {  # list of available sample rates @ 16 bit resolution
        "6.25 M": 6250000,
        "3.125 M": 3125000,
        "1.25 M": 1250000,
        "625 k": 625000
    }
    trigger_name = "Generator new period"
    channels = 0
    status_settings_changed= False  # flag to indicate if settings were changed

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
            CH_ranges=None,
            CH_couplings=None,
            trigger_source="Generator",
            ):
        if CH_couplings is None:
            CH_couplings = ["dc", "dc", "dc", "dc"]
        if CH_ranges is None:
            CH_ranges = [8, 2, 2, 2]
        changed = False
        if self.scp is None:
            return False
        #if self.scp.is_running and self.scp.measure_mode == libtiepie.MM_STREAM:
            # not controllable
            #return False

        # set scp parameters
        try:
            # Set measure mode:
            if mode == "block":
                if self.scp.measure_mode != libtiepie.MM_BLOCK:
                    self.scp.measure_mode = libtiepie.MM_BLOCK
                    # print("set measure_mode BLOCK")
                    if self.scp.measure_mode == libtiepie.MM_BLOCK:
                        changed = True
                    else:
                        print("Failed to set measure mode to BLOCK")
                        #self.scp.measure_mode = libtiepie.MM_STREAM
                        changed = True
            else:
                # print("set measure_mode STREAM")
                if self.scp.measure_mode != libtiepie.MM_STREAM:
                    # print("set measure_mode STREAM")
                    # print("set trigger source: " + str(trigger_source))
                    self.scp.measure_mode = libtiepie.MM_STREAM
                    if self.scp.measure_mode == libtiepie.MM_STREAM:
                        changed = True
                    else:
                        print("Failed to set measure mode to STREAM")
                        #self.scp.measure_mode = libtiepie.MM_BLOCK
                        changed = True



            # set vertical resolution
            self.scp.resolution = 16  # set 16 bit vertical resolution
            # print("Sample frequency SET to:", self.scp.sample_rate)

            # Set record length:
            if self.scp.record_length != int(record_length):
                changed = True
                # print("set record length: " + str(int(record_length)))
                self.scp.record_length = int(record_length)  # 10000 samples

            # Set pre sample ratio:
            self.scp.pre_sample_ratio = 0  # 0 %

            # Set sample frequency:
            if self.scp.sample_rate != sample_rate:
                changed = True
                # print("set sample frequency: " + str(sample_rate))
                self.scp.sample_rate = sample_rate  # 1 MHz

            # For all channels:
            for i, ch in enumerate(self.scp.channels):
                # Enable channel to measure it:
                if not ch.enabled:
                    changed = True
                    # print("Enable channel: " + str(i))
                    ch.enabled = True
                # Set range
                if ch.range != CH_ranges[i]:
                    changed = True
                    ch.range = CH_ranges[i]
                # Set coupling
                if CH_couplings[i] == 'dc':
                    if ch.coupling != libtiepie.CK_DCV:
                        changed = True
                        ch.coupling = libtiepie.CK_DCV # DC Volt
                else:
                    if ch.coupling != libtiepie.CK_ACV:
                        changed = True
                        ch.coupling = libtiepie.CK_ACV  # AC Volt


            #self.set_trigger(trigger_source=trigger_source)
            # Set trigger timeout:
            self.scp.trigger.timeout = 1000e-3  # 100 ms

            # find generator trigger input
            try:
                # Locate trigger input:
                trigger_input_generator = self.scp.trigger_inputs.get_by_id(
                    libtiepie.TIID_GENERATOR_NEW_PERIOD)  # or TIID_GENERATOR_START or TIID_GENERATOR_STOP
                # Set trigger timeout:
                self.scp.trigger.timeout = 1000e-3  # 100 ms

                if trigger_input_generator is None:
                    raise Exception('Unknown trigger input!')
            except Exception as e:
                # self.trigger_name = "Generator new period"
                for trigger_input_generator in self.scp.trigger_inputs:
                    # print(f"{trigger_input_generator.id=} {trigger_input_generator.name= }")
                    if trigger_input_generator.name.split(".")[-1] == self.trigger_name:
                        break

            if trigger_source == "Generator":
                # Enable trigger input:
                if not trigger_input_generator.enabled:
                    changed = True
                    # print("Enable trigger input: " + str(trigger_input_generator.name))
                    trigger_input_generator.enabled = True
                for ch in self.scp.channels:
                    if ch.trigger.enabled:
                        changed = True
                        # Disable channel trigger source:
                        # print("Disable channel trigger source: " + str(ch.name))
                        ch.trigger.enabled = False
            else:
                # print("Set trigger source: " + str(trigger_source))
                trigger_input_generator.enabled = False
                # Defaults:
                #--------------------------------
                for ch in self.scp.channels:
                    # Kind:
                    ch.trigger.kind = libtiepie.TK_RISINGEDGE  # Rising edge

                    # Trigger mode:
                    ch.trigger.level_mode = libtiepie.TLM_ABSOLUTE
                    # ch.trigger.level_mode = libtiepie.TLM_RELATIVE

                    # Level:
                    ch.trigger.levels[0] = 0  # 50 %

                    # Hysteresis:
                    ch.trigger.hystereses[0] = 0.05  # 5 %

                #Variable parameters:
                #--------------------------------
                i = 0
                match trigger_source:
                    case "CH2":
                        i = 1
                    case "CH3":
                        i = 2
                    case "CH4":
                        i = 3

                for j, ch in enumerate(self.scp.channels):
                    #print(f"{j=}, {i=}, {ch=}")

                    if ch.trigger.enabled and j != i:
                        changed = True
                        # Disable channel trigger source:
                        #print("Disable channel trigger source: " + str(trigger_source))
                        ch.trigger.enabled = False

                    if j == i and not ch.trigger.enabled:
                        changed = True
                        # Enable trigger source:
                        print("Enable channel trigger source: " + str(trigger_source))
                        ch.trigger.enabled = True


            #print("Changed: " + str(changed))
            self.status_settings_changed = False
            self.status_settings_changed = changed
            return changed

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

    def set_trigger(self, trigger_source="Generator"):

        """
        Combined instrument inputs:
        inp.id=19923200 inp.name='HS5-540XM(30553).EXT 1'
        inp.id=19923456 inp.name='HS5-540XM(30553).EXT 2'
        inp.id=19923712 inp.name='HS5-540XM(30553).EXT 3'
        inp.id=18874368 inp.name='HS5-540XM(30553).Generator start'
        inp.id=18874369 inp.name='HS5-540XM(30553).Generator stop'
        inp.id=18874370 inp.name='HS5-540XM(30553).Generator new period'

        """
        #print("set trigger")

        try:
            # Locate trigger input:
            trigger_input_generator = self.scp.trigger_inputs.get_by_id(
                libtiepie.TIID_GENERATOR_NEW_PERIOD)  # or TIID_GENERATOR_START or TIID_GENERATOR_STOP
            # Set trigger timeout:
            self.scp.trigger.timeout = 1000e-3  # 100 ms

            if trigger_input_generator is None:
                raise Exception('Unknown trigger input!')
        except Exception as e:
            # self.trigger_name = "Generator new period"
            for trigger_input_generator in self.scp.trigger_inputs:
                #print(f"{trigger_input_generator.id=} {trigger_input_generator.name= }")
                if trigger_input_generator.name.split(".")[-1] == self.trigger_name:
                    break

        # Disable all channel trigger sources:
        for ch in self.scp.channels:
            ch.trigger.enabled = False
            ch.enabled = True
        trigger_input_generator.enabled = False


        if trigger_source == "Generator":
            # Enable trigger input:
            trigger_input_generator.enabled = True

        else:
            i = 0
            match  trigger_source:
                case "CH2":
                    i = 1
                case "CH3":
                    i = 2
                case "CH4":
                    i = 3
            ch = self.scp.channels[i]
            # Enable trigger source:
            ch.trigger.enabled = True

            # Kind:
            ch.trigger.kind = libtiepie.TK_RISINGEDGE  # Rising edge

            # Trigger mode:
            ch.trigger.level_mode = libtiepie.TLM_ABSOLUTE
            #ch.trigger.level_mode = libtiepie.TLM_RELATIVE

            # Level:
            ch.trigger.levels[0] = 0  # 50 %

            # Hysteresis:
            ch.trigger.hystereses[0] = 0.05  # 5 %

            print("Trigger source: " + str(ch) + " Enabled:  " + str(ch.trigger.enabled))
            print("Trigger kind: " + str(ch.trigger.kind))

            print(self.scp.__getstate__())

            # Must restart the scope to apply the changes
            # problem with QTworker
            # To apply the changes we need to stop and start the scope
            if self.scp.is_running:

                while self.scp.is_running:
                    try:
                        self.scp.stop()
                        time.sleep(0.05)
                    except Exception as e:
                        pass
                while not self.scp.is_running:
                    try:
                        self.scp.start()
                        time.sleep(0.05)
                    except Exception as e:
                        pass
            else:
                print("Scope is not running, no need to stop it.")
                self.scp.start()



        print("End of tiepieSCP.set_trigger trigger source to: " + trigger_source)






