#  Copyright (c) 2021.
#  This code has been produced by Zoran D. Grujic and by the knowledge found on The Internet.
#  Please feel free to ask me for permission to use my code in your own projects. It is for your own well fare!

import sys
# pip install python-libtiepie
import libtiepie
from array import array


class arbGenerator:

    def __init__(self):
        # Enable network search:
        libtiepie.network.auto_detect_enabled = True

        # Search for devices:
        libtiepie.device_list.update()

        # Try to open a generator with arbitrary support:
        self.gen = None
        for item in libtiepie.device_list:
            print(item)
            if item.can_open(libtiepie.DEVICETYPE_GENERATOR):
                self.gen = item.open_generator()
                if self.gen.signal_types & libtiepie.ST_ARBITRARY:
                    break
                else:
                    self.gen = None
        if self.gen is None:
            print("No generator detected! Connect the USB device!")

    def arbLoad(self, arb, amplitude=1, frequency=10, offset=0.0):
        if self.gen is None:
            return False
        try:
            arb = array('f', arb)
            # Set signal type:
            self.gen.signal_type = libtiepie.ST_ARBITRARY

            # Select frequency mode:
            self.gen.frequency_mode = libtiepie.FM_SIGNALFREQUENCY  # libtiepie.FM_SAMPLEFREQUENCY  FM_SIGNALFREQUENCY
            #print(f" gen {frequency=}")

            # Set sample frequency:
            self.gen.frequency = frequency  # 100 kHz

            # Set amplitude:
            self.gen.amplitude = amplitude  # 2 V

            # Set offset:
            self.gen.offset = offset  # 0 V

            self.gen.set_data(arb)

        except Exception as e:
            print('Exception: ' + e.message)
            # sys.exit(1)
        return True

    def start(self):
        if self.gen is None:
            print("Gen is none TiePieArb.py")
            return

        # Enable output:
        self.gen.output_enable = True
        # Start signal generation:
        self.gen.start()
        print("Generator started")

    def stop(self):
        if self.gen is None:
            return
        # Stop generator:
        self.gen.stop()

        # Disable output:
        self.gen.output_enable = False
        print("Generator STOP")

