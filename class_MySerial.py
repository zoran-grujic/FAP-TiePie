#  Copyright (c) 2019.
#  This code has been produced by Dr Zoran D. Grujic and by the knowledge found on The Internet.
#  Please feel free to ask me for permission to use my code in your own projects. It is for your own well fare!

import serial
# import class_signal
import sys
import glob
import logging
import time


class MySerial:
    # define start values, constants
    baud = 115200 #115200
    time_out = 0.2
    port = ""
    boxNamePrefix = "PIXI click driver"
    name = ""
    boxSettings = False  # have settings from box
    box = False  # serial port object
    status = ""
    connected = False

    # sig = class_signal.signal()

    def __init__(self):
        pass

    def connect(self):
        """Connect to the driver"""
        print("connecting...")
        if self.connected:
            print("Already connected")
            return

        ports = self.serial_ports()
        print(ports)

        for port in ports:
            try:
                # dsrdtr=True  # no auto reset of the controller!!! - Ok for MEGA, bad for ESP32
                # use default or set : dsrdtr = False, rtscts = False, in serial.Serial
                self.box = serial.Serial(port, self.baud, timeout=self.time_out, dsrdtr=False, rtscts=False,
                                         parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)  # connect to port
                time.sleep(.1)
                if not self.box.writable():
                    print(self.box.port + " is NOT writable")
                # print("Port name:", port)
                #self.sendToBox("")  # prvi mačići se u vodu bacaju. Prva komanda "nestane", ne bude primljena.
                time.sleep(.01)
                self.box.flushInput()
                self.box.flushOutput()
                self.sendToBox("whois?")  # Pitamo COM port ko je tamo
                for i in range(10):
                    if i % 5 == 0 and i > 0:
                        self.sendToBox("whois?")
                    #time.sleep(.02)
                    while self.box.in_waiting == 0:
                        pass

                    line = self.readLine()

                    logging.info('%i: PORT: %s : %s', i, port, line)
                    print(i, ": PORT: ", port, ": ", line)
                    # print(line[:len(self.boxName)])
                    if line[:len(self.boxNamePrefix)] == self.boxNamePrefix:
                        self.name = line
                        # print("Yes, connected to the Pixi driver!")
                        self.port = port

                        self.status = "connected"
                        self.connected = True
                        return True


                #print(f"closing port {self.box.port}")
                self.box.flushInput()  # need to flush in/out before closing the port
                self.box.flushOutput()
                #tic = time.perf_counter()
                self.box.close()
                #toc = time.perf_counter()
                #print(f"Port closed in in {toc - tic:0.4f} seconds")
                print(f"Port closed")
            except Exception as e:
                logging.error(str(e))
                print(str(e))

        return False
        # end findAndConnect

    def readLine(self):
        """Remove \r\n from the end of line """
        #print("reading a line")
        line = self.box.readline()
        #print(f"{line=}")
        try:
            line = line.decode("ascii")[:-2]
        except Exception as e:
            print(str(e))
        return line  # "utf-8"

    def sendToBox(self, stri):
        """Prepare string to be sent to the box,
           add \n at the end or box will wait 1s to get it before continuing...
        """
        # print("sendToBox")
        stri = (stri+"\n").encode('utf-8')  # "utf-8"
        #print("Send to box: ", stri)
        return self.box.write(stri)  # + b'\r'

    @staticmethod
    def serial_ports():
        """ Lists serial port names

        :raises: EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port, dsrdtr=True)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    # end serial_ports()