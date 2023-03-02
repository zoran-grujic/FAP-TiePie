#  Copyright (c) 2021.
#  This code has been produced by Zoran D. Grujic and by the knowledge found on The Internet.
#  Please feel free to ask me for permission to use my code in your own projects. It is for your own well fare!
#  pyinstaller --onefile -w app.pyw

# ---------------------------------------------
# to find QtDesigner and pyuic5 files goto
# C:\Users\Zoran\Anaconda3\Library\bin
# C:\Users\Zoran\Anaconda3\Library\bin\pyuic5 gui.ui -o gui.py

# pip install qdarkgraystyle
import qdarkgraystyle  # https://pypi.org/project/qdarkgraystyle/

from PyQt5.QtCore import QThreadPool
from QtWorker import Worker
import sys
import os
import logging
from PyQt5 import QtCore  # conda install pyqt // pip install PyQt5==5.15.0
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QWidget
from PyQt5 import QtGui
# pip install pyqtgraph
import pyqtgraph as pg  # Fast plot package
import numpy as np
from scipy import signal
import time
from datetime import datetime
from scipy.optimize import curve_fit
from arbcalc import arbcalc
from tiepieArb import arbGenerator
from tiepieSCP import oscilloscope
import CrameRaoFunctions as cr
import shutil  # about disk remaining memory

from gui import Ui_MainWindow  # generated by designer, DO NOT EDIT
# pip install python-libtiepie
import libtiepie
from playsound import playsound  # pip install playsound


# extend Ui_MainWindow class
class MyUi(Ui_MainWindow):
    plotWindow = pg.GraphicsLayoutWidget()  # pg.GraphicsWindow() Deprecated
    FITplotWindow_Widget = pg.GraphicsLayoutWidget()  # pg.GraphicsWindow() Deprecated
    monitorPlot_Window = pg.GraphicsLayoutWidget()  # pg.GraphicsWindow()
    timerPlotSCP = QtCore.QTimer()
    timerStart = QtCore.QTimer()
    rePlotInterval_ms = 100
    SCPData = False
    dataFITtab = False

    colorX = (100, 200, 250)
    colorY = (100, 250, 200)
    colorZ = (250, 100, 200)
    penX = pg.mkPen(colorX, width=2, style=QtCore.Qt.SolidLine)
    penY = pg.mkPen(colorY, width=2, style=QtCore.Qt.SolidLine)
    penZ = pg.mkPen(colorZ, width=2, style=QtCore.Qt.SolidLine)
    decimationArr = np.array([5])  # 5,2

    countRemainingToSave = 0

    soundPlayed = False


    """Initialize the app"""

    def __init__(self):
        super(MyUi, self).__init__()

        self.dialogs = list()

        self.gen = arbGenerator()
        self.scp = oscilloscope()

        self.threadpool = QThreadPool()
        self.theWorkerBlocks = Worker(self.getBlocks)  # Any other args, kwargs are passed to the run function
        self.theWorkerSave = Worker(self.SaveData)  # Any other args, kwargs are passed to the run function
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.timerPlotSCP.setInterval(self.rePlotInterval_ms)
        self.timerPlotSCP.timeout.connect(self.plotSCP)

        self.timerStart.setInterval(1000)
        self.timerStart.timeout.connect(self.boot)

    """
    override function of the parent class to connect actions and buttons
    set user interface
    """
    def setupUi(self, MainWindow):
        super(MyUi, self).setupUi(MainWindow)  # call function of the parent class

        self.okButton_GeneratorStart.clicked.connect(self.genStartStop)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        self.doubleSpinBox_RecordsToSave.valueChanged.connect(self.saveRecordsChanged)

        elements = [self.doubleSpinBox_PumpLevel,
                    self.doubleSpinBox_ProbeLevel,
                    self.doubleSpinBox_ZeroLevel,
                    self.doubleSpinBox_Frequency_Hz,
                    self.doubleSpinBox_TotalTime_ms,
                    self.doubleSpinBox_DutyCycle,
                    self.doubleSpinBox_PumpTime_ms,
                    self.doubleSpinBox_Points
                    ]
        for el in elements:
            el.valueChanged.connect(self.arbSet)

        elements = [self.doubleSpinBox_FilterStart_ms,
                    self.doubleSpinBox_FilterStop_ms,
                    self.doubleSpinBox_FIT_f0,
                    self.doubleSpinBox_FIT_A,
                    self.doubleSpinBox_FIT_B,
                    self.doubleSpinBox_FIT_Gamma,
                    self.doubleSpinBox_FIT_DC
                    ]
        for el in elements:
            el.valueChanged.connect(self.fit)
        self.comboBox_FilterType.currentIndexChanged.connect(self.fitUISet)
        self.radioButton_FITSource_CH1.clicked.connect(self.fitUISet)
        self.radioButton_FITSource_CH2.clicked.connect(self.fitUISet)
        self.pushButton_Set_FIT_init.clicked.connect(self.copyFITtoInit)
        self.pushButton_SelectFolder.clicked.connect(self.selectFolder)
        self.lineEdit_FolderName.setText(os.getcwd()+"\\data\\")

        # change CH parameters on the data tab
        elements = [
            self.comboBox_CH1Range,
            self.comboBox_CH2Range,
            self.radioButton_CH1AC,
            self.radioButton_CH2AC
        ]
        for el in elements:
            self.connectElementTo(el, self.setCH_1_2)


        # make plot widget and layout
        containing_layout = self.PlotPlaceholder.parent().layout()
        containing_layout.replaceWidget(self.PlotPlaceholder, self.plotWindow)
        PG_layout = pg.GraphicsLayout()  # make layout for plots

        self.arbPlot = PG_layout.addPlot()
        PG_layout.nextRow()
        self.ch1Plot = PG_layout.addPlot()
        PG_layout.nextRow()
        self.ch2Plot = PG_layout.addPlot()

        self.plotWindow.setCentralItem(PG_layout)  # set layout to the widget
        self.checkBox_SaveData.setStyleSheet("QCheckBox::indicator { width: 70; height: 70;}")

        containing_layout = self.FITPlotPlaceholder.parent().layout()
        containing_layout.replaceWidget(self.FITPlotPlaceholder, self.FITplotWindow_Widget)
        PG_layout_Tab_2 = pg.GraphicsLayout()  # make layout for plots

        self.dataPlotFIT = PG_layout_Tab_2.addPlot()
        PG_layout_Tab_2.nextColumn()
        self.unFilteredDataPlotFIT = PG_layout_Tab_2.addPlot()
        PG_layout_Tab_2.nextRow()
        self.FITdataPlotFIT = PG_layout_Tab_2.addPlot()
        PG_layout_Tab_2.nextColumn()
        self.FFTdataPlotFIT = PG_layout_Tab_2.addPlot()
        self.FFTdataPlotFIT_lr = pg.LinearRegionItem([1500, 3000], hoverBrush=None)
        self.FFTdataPlotFIT_lr.setZValue(10)
        self.FFTdataPlotFIT_lr.sigRegionChanged.connect(self.updateCRRange)


        PG_layout_Tab_2.nextRow()
        self.ResidualsDataPlotFIT = PG_layout_Tab_2.addPlot()
        PG_layout_Tab_2.nextColumn()
        self.FFTFilteredDataPlotFIT = PG_layout_Tab_2.addPlot()
        self.FFTFilteredDataPlotFIT_lr = pg.LinearRegionItem([1500, 3000], hoverBrush=None)
        self.FFTFilteredDataPlotFIT_lr.setZValue(10)
        self.FFTFilteredDataPlotFIT_lr.sigRegionChangeFinished.connect(self.updateCR)

        self.FITplotWindow_Widget.setCentralItem(PG_layout_Tab_2)

        # make Monitor plot widget
        containing_layout = self.CH_MonitorPlotPlaceholder.parent().layout()
        containing_layout.replaceWidget(self.CH_MonitorPlotPlaceholder, self.monitorPlot_Window)
        PG_layout_Tab_Monitor = pg.GraphicsLayout()  # make layout for plots

        self.monitorPlotCH1 = PG_layout_Tab_Monitor.addPlot()
        PG_layout_Tab_Monitor.nextRow()
        self.monitorPlotCH2 = PG_layout_Tab_Monitor.addPlot()
        if(self.scp.channels>2):
            PG_layout_Tab_Monitor.nextRow()
            self.monitorPlotCH3 = PG_layout_Tab_Monitor.addPlot()
            PG_layout_Tab_Monitor.nextRow()
            self.monitorPlotCH4 = PG_layout_Tab_Monitor.addPlot()

        self.monitorPlot_Window.setCentralItem(PG_layout_Tab_Monitor)

        # Set tab index
        self.tabWidget.setCurrentIndex(0)


        # Execute
        self.scpWorkerStart(self.theWorkerBlocks)
        self.timerPlotSCP.start()
        # self.genStartStop()

        self.showDiskSpace()



    def scpWorkerStart(self, worker):

        print("Boot SCP")
        self.scpSet()
        try:
            worker.signals.result.connect(self.res)
            worker.signals.finished.connect(self.fini)
            worker.signals.progress.connect(self.prog)

            # Execute
            self.threadpool.start(worker)
            print("Worker read SCP data Started")
        except Exception as e:
            print("scpWorkerStart exception: ", e)

    def scpWorkerStop(self, worker):
        try:
            self.threadpool.stop(worker)
        except Exception as e:
            print("scpWorkerStop exception: ", e)

    def SaveData(self, progress_callback):
        pass

    def saveData(self, data):
        try:
            self.showDiskSpace()
            now = datetime.now()  # current date and time
            date_time = now.strftime("%Y%m%d_%H-%M-%S-%f")
            print("date and time:", date_time)
            fn = self.lineEdit_FolderName.text() + self.lineEdit_FileNamePrefix.text() + date_time
            decimated = data
            if self.comboBox_decimate.currentText() != "None":
                decFactor = int(self.comboBox_decimate.currentText())
                if decFactor <= 10:
                    decimationArr = [decFactor]
                else:
                    if decFactor <= 100:
                        decimationArr = [10, int(decFactor/10)]
                    else:  # up to 1000
                        decimationArr = [10, 10, int(decFactor / 100)]

                for d in decimationArr:
                    decimated = signal.decimate(decimated, d, ftype='fir')
            np.save(fn, decimated)
            print("File: ", fn)
            return True
        except Exception as e:
            print("Save data Exception:", e)

            # stop saving?
            try:
                playsound('Sounds/retro-game-over-213.wav')
            except:
                pass
            self.checkBox_SaveData.setChecked(False)
            self.countRemainingToSave = 0

        return False

    def getBlocks(self, progress_callback):
        print("Worker here")

        scp = self.scp.scp
        while True:
            if self.radioButton_modeBlock.isChecked():
                # block mode
                if scp.is_running and scp.measure_mode == libtiepie.MM_STREAM:
                    # change from STREAM to BLOCK
                    scp.stop()
                    self.scpSet()
                    scp.start()
                else:
                    self.scpSet()  # set SCP parameters
                    scp.start()
                # Wait for measurement to complete:
                while not scp.is_data_ready:
                    time.sleep(0.01)  # 10 ms delay, to save CPU time

                # Get data:
                self.SCPData = scp.get_data()
                # print("Got SCP data!")
            else:
                # stream mode
                # print("Stream mode")
                if scp.measure_mode == libtiepie.MM_BLOCK:
                    # change from BLOCK to STREAM
                    self.scpSet()
                    scp.start()
                else:
                    if not scp.is_running:
                        scp.start()

                while not scp.is_data_ready:
                    time.sleep(0.01)  # 10 ms delay, to save CPU time

                # Get data:
                self.SCPData = scp.get_data()
                # print("Got SCP data!")
            # print(scp.measure_mode)
            if self.checkBox_SaveData.isChecked():
                self.doubleSpinBox_RecordsToSave.setDisabled(True)
                self.saveData(self.SCPData)

                #count remaining to save
                n = int(self.doubleSpinBox_RecordsToSave.value())
                if self.countRemainingToSave == n: #first file
                    self.soundPlayed = False
                if n != 0:
                    self.countRemainingToSave -= 1
                    self.label_RemainingToSave.setText("Remaining: " + str(self.countRemainingToSave))
                    if self.countRemainingToSave <= 0:
                        self.countRemainingToSave = n
                        self.checkBox_SaveData.setChecked(False)
            else:
                self.doubleSpinBox_RecordsToSave.setDisabled(False)
                self.label_RemainingToSave.setText("Finished")
                if not self.soundPlayed:
                    playsound('Sounds/retro-game-notifi.wav')
                    self.soundPlayed = True


    def plotArb(self, t, y):

        self.arbPlot.clear()
        self.arbPlot.plot(1000 * t, y)
        self.arbPlot.setLabel('bottom', "time (ms)")
        self.arbPlot.setLabel('left', "S (V)")

        scp = self.scp.scp
        if scp is None or (scp.is_running and scp.measure_mode == libtiepie.MM_STREAM):
            # not controlable
            self.statusbar.showMessage("Oscilloscope and Arb. signal Generator are not controllable in STREAM mode!",
                                       2000)
            return False

        if not self.timerPlotSCP.isActive():
            self.timerPlotSCP.start()

    # not in use?
    def getOscData(self):
        self.scpSet()
        self.SCPData = self.scp.getBlock()

        print("Current tab index: " + str(self.tabWidget.currentIndex()))
        self.plotSCPMonitor()
        self.plotSCP()

    def plotSCP(self):

        if self.tabWidget.currentIndex() == 2: # Monitor tab
            return self.plotSCPMonitor()
        if self.tabWidget.currentIndex() != 0:  # Data tab
            return

        if isinstance(self.SCPData, bool):
            return
        samples = len(self.SCPData[0])
        if samples < 10:
            return

        sr = self.scp.scp.sample_frequency
        t = np.linspace(0, 1000 * samples / sr, samples, endpoint=False)

        self.ch1Plot.clear()
        self.ch2Plot.clear()

        self.ch1Plot.setLabel('bottom', "time (ms)")
        self.ch1Plot.setLabel('left', "CH1 (V)")
        self.ch1Plot.plot(t, self.SCPData[0])

        self.ch2Plot.setLabel('bottom', "time (ms)")
        self.ch2Plot.setLabel('left', "CH2 (V)")
        self.ch2Plot.plot(t, self.SCPData[1])

    def plotSCPMonitor(self):

        if isinstance(self.SCPData, bool):
            return
        samples = len(self.SCPData[0])
        if samples < 10:
            return
        sr = self.scp.scp.sample_frequency
        t = np.linspace(0, 1000 * samples / sr, samples, endpoint=False)
        # print(self.__dict__.get("monitorPlotCH1"))

        plots = [self.__dict__.get("monitorPlotCH"+str(i+1)) for i in range(self.scp.channels)]
        """plots = [self.monitorPlotCH1,
                 self.monitorPlotCH2,
                 self.monitorPlotCH3,
                 self.monitorPlotCH4]"""
        for i in range(self.scp.channels):
            plots[i].clear()
            plots[i].setLabel('bottom', "time (ms)")
            plots[i].setLabel('left', f"CH{i+1} (V)")
            plots[i].plot(t, self.SCPData[i])

    def scpSet(self):

        self.comboBox_CH1Range.setCurrentIndex(self.comboBox_M_CH1Range.currentIndex())
        self.comboBox_CH2Range.setCurrentIndex(self.comboBox_M_CH2Range.currentIndex())
        if self.radioButton_M_CH1AC.isChecked() != self.radioButton_CH1AC.isChecked():
            self.radioButton_CH1AC.toggle()
        if self.radioButton_M_CH2AC.isChecked() != self.radioButton_CH2AC.isChecked():
            self.radioButton_CH2AC.toggle()

        if not self.scp.set(mode=self.getSCPmode(),
                            sample_frequency=self.getSampleRate(),
                            record_length=int(self.doubleSpinBox_Samples.value()),
                            CH_ranges=[
                                float(self.comboBox_M_CH1Range.currentText()),
                                float(self.comboBox_M_CH2Range.currentText()),
                                float(self.comboBox_M_CH3Range.currentText()),
                                float(self.comboBox_M_CH4Range.currentText())
                            ],
                            CH_couplings=[
                                self.getCH1coupling(),
                                self.getCH2coupling(),
                                self.getCH3coupling(),
                                self.getCH4coupling()
                            ],
                            ):
            self.statusbar.showMessage("The oscilloscope is not controllable!", 2000)
            print("The oscilloscope is not controllable!")

    def getCH1coupling(self):
        if self.radioButton_M_CH1DC.isChecked():
            return "dc"
        else:
            return "ac"

    def getCH2coupling(self):
        if self.radioButton_M_CH2DC.isChecked():
            return "dc"
        else:
            return "ac"

    def getCH3coupling(self):
        if self.radioButton_M_CH3DC.isChecked():
            return "dc"
        else:
            return "ac"

    def getCH4coupling(self):
        if self.radioButton_M_CH4DC.isChecked():
            return "dc"
        else:
            return "ac"

    def getSCPmode(self):
        if self.radioButton_modeBlock.isChecked():
            return "block"
        else:
            return "stream"

    def getSampleRate(self):
        return self.scp.srs.get(self.comboBox_SampleRate.currentText(), 3125000)

    """ Worker signal functions """

    def res(self, res):
        pass

    def fini(self):
        pass

    def prog(self, n):
        pass

    def boot(self):
        # Execute
        print("Boot SCP")
        self.threadpool.start(self.theWorkerBlocks)

    def setCH_1_2(self):
        # print("setCH_1_2")
        self.comboBox_M_CH1Range.setCurrentIndex(self.comboBox_CH1Range.currentIndex())
        self.comboBox_M_CH2Range.setCurrentIndex(self.comboBox_CH2Range.currentIndex())
        if self.radioButton_CH1AC.isChecked() != self.radioButton_M_CH1AC.isChecked():
            self.radioButton_M_CH1AC.toggle()
        if self.radioButton_CH2AC.isChecked() != self.radioButton_M_CH2AC.isChecked():
            self.radioButton_M_CH2AC.toggle()

    def connectElementTo(self, el, function):
        try:  # dropbox
            el.currentIndexChanged.connect(function)
            return
        except:
            pass
        try:  # input text
            el.valueChanged.connect(function)
            return
        except:
            pass
        try:  # radio buttons
            el.toggled.connect(function)
            return
        except:
            pass
        raise Exception(f"Sorry, {el} not connected with {function}")

    def tabChanged(self):
        if self.tabWidget.currentIndex() == 1:
            print("FIT data set!")
            if self.scp.scp is None:
                n = cr.white_noise(.01, 3125000, 312500, mu=0)
                self.dataSCPtoFITtab = [n, n]
            else:
                self.dataSCPtoFITtab = self.SCPData
            self.fitUISet()

    def fitUISet(self):
        if self.tabWidget.currentIndex() == 1:
            print("FIT time!")
            # set initial parameters

            self.doubleSpinBox_FilterStart_ms.setValue(self.doubleSpinBox_PumpTime_ms.value())
            self.doubleSpinBox_FilterStop_ms.setValue(self.doubleSpinBox_TotalTime_ms.value())
            fitStart = float(self.doubleSpinBox_FilterStart_ms.value()) + 5
            self.doubleSpinBox_FITStart_ms.setValue(fitStart)
            fitStop = float(self.doubleSpinBox_FilterStop_ms.value()) - 5
            self.doubleSpinBox_FITStop_ms.setValue(fitStop)
            self.doubleSpinBox_FIT_f0.setValue(self.doubleSpinBox_Frequency_Hz.value())
            if self.scp.scp is None:
                self.FITSampleRate = 3125000
            else:
                self.FITSampleRate = self.scp.scp.sample_frequency

            r = (self.doubleSpinBox_FIT_f0.value() + 500, self.doubleSpinBox_FIT_f0.value() + 1500)
            self.FFTdataPlotFIT_lr.setRegion(r)
            self.FFTFilteredDataPlotFIT_lr.setRegion(r)

            self.fit()

    # The fit function must be static
    @staticmethod
    def FITfunc(x, freq, a, b, gamma, dc):
        return (a * np.sin(2 * np.pi * freq * x) + b * np.cos(2 * np.pi * freq * x)) * np.exp(-gamma * x) + dc

    """Plot, fit, filter, analyse..."""

    def fit(self):

        if self.radioButton_FITSource_CH1.isChecked():
            self.dataFIT = self.dataSCPtoFITtab[0]
        else:
            self.dataFIT = self.dataSCPtoFITtab[1]
        totalTime_ms = float(self.doubleSpinBox_FITStop_ms.value())
        t = np.linspace(0, totalTime_ms, len(self.dataFIT), endpoint=False)

        self.dataPlotFIT.clear()
        self.dataPlotFIT.plot(t/1000, self.dataFIT)
        self.dataPlotFIT.setLabel('bottom', "time", units='s')
        self.dataPlotFIT.setLabel('left', "S", units='V')

        # cut the data
        nStartUnfiltered = int((self.doubleSpinBox_FilterStart_ms.value() * self.FITSampleRate) / 1000)
        nStopUnfiltered = int((self.doubleSpinBox_FilterStop_ms.value() * self.FITSampleRate) / 1000)
        self.unFilteredDataFit = self.dataFIT[nStartUnfiltered: nStopUnfiltered]

        self.unFilteredDataPlotFIT.clear()
        self.unFilteredDataPlotFIT.plot(t[nStartUnfiltered:nStopUnfiltered]/1000, self.unFilteredDataFit)
        self.unFilteredDataPlotFIT.setLabel('bottom', "time", units="s")
        self.unFilteredDataPlotFIT.setLabel('left', "UnFiltered", units='V')


        # filter the data
        detrend = signal.detrend(self.unFilteredDataFit, type='constant')
        decimated = detrend
        for d in self.decimationArr:
            decimated = signal.decimate(decimated, d, ftype='fir')
        """
        decimated = signal.decimate(detrend, 5, ftype='fir')  # reduce sample rate 5x
        # print(len(self.unFilteredDataFit))
        # print(len(decimated), len(self.unFilteredDataFit)/len(decimated))
        decimated = signal.decimate(decimated, 4, ftype='fir')  # reduce sample rate 4x
        # print(len(decimated), len(self.unFilteredDataFit) / len(decimated))
        """

        # filter the data
        ciFilter = self.comboBox_FilterType.currentIndex()
        filRange = 1e3
        filterLength = 601  # must be odd number!!!!!!!!!!!!!!!!!!!!
        pass_zero = False
        if ciFilter == 0:  # High pass from 1k
            filRange = 10e3
            pass_zero = False
        elif ciFilter == 1:  # Band pass 1-12k
            filRange = 1e3, 12e3
            pass_zero = False
        elif ciFilter == 2:  # Band pass 8-22k
            filRange = 8e3, 22e3
            pass_zero = False
        elif ciFilter == 3:  # Band pass 18-32k
            filRange = 18e3, 32e3
            pass_zero = False
        elif ciFilter == 4:  # Low pass up to 12k
            filRange = 12e3
            pass_zero = True

        # drop = int((filterLength - 1) / 2)
        fltr = signal.firwin(filterLength, filRange, pass_zero=pass_zero, fs=self.FITSampleRate / np.prod(self.decimationArr))

        filtered = signal.convolve(decimated - np.mean(decimated), fltr, mode='valid')
        self.filteredDataFIT = signal.detrend(filtered, type='constant')
        n = len(self.filteredDataFIT)
        tf = np.linspace(0, (n * np.prod(self.decimationArr)) / self.FITSampleRate, n, endpoint=False)

        # fit of the data
        # curve_fit

        p0 = [self.doubleSpinBox_FIT_f0.value(),
              self.doubleSpinBox_FIT_A.value(),
              self.doubleSpinBox_FIT_B.value(),
              2 * np.pi * self.doubleSpinBox_FIT_Gamma.value(),  # from Hz to rad^-1
              self.doubleSpinBox_FIT_DC.value()]
        popt, pcov = curve_fit(self.FITfunc, tf, self.filteredDataFIT, p0=p0)
        self.lastFIT = [popt, pcov]
        print("popt = ", popt)
        plainText = "f = {:.4f} Hz\n".format(popt[0])  # +str(popt[0]) + "\n"
        plainText += "A = {:.2e} V\n".format(popt[1])
        plainText += "B = {:.2e} V\n".format(popt[2])
        plainText += "gamma = {:.2e} Hz\n".format(popt[3]/(2 * np.pi))
        plainText += "dc = {:.2e} V\n".format(popt[4])
        plainText += "mean = {:.2e} V\n".format(
            np.mean(self.unFilteredDataFit))
        self.plainTextEdit_FITResults.setPlainText(plainText)

        fitCurve = self.FITfunc(tf, *popt)
        self.FITdataPlotFIT.clear()
        self.FITdataPlotFIT.plot(tf, self.filteredDataFIT, pen=self.penX)
        self.FITdataPlotFIT.plot(tf, fitCurve, pen=self.penZ)
        self.FITdataPlotFIT.setLabel('bottom', "time", units="s")
        self.FITdataPlotFIT.setLabel('left', "FIT", units='V')

        self.ResidualsDataPlotFIT.clear()
        self.ResidualsDataPlotFIT.plot(tf, self.filteredDataFIT - fitCurve, pen=self.penY)
        self.ResidualsDataPlotFIT.setLabel('bottom', "time", units="s")
        self.ResidualsDataPlotFIT.setLabel('left', "Residuals", units="V")

        """ scipy.signal.periodogram(x, fs=1.0, window='boxcar', nfft=None,
         detrend='constant', return_onesided=True, 
         scaling='density', axis=- 1)
        """
        vsqrtHztext = "V/&radic;<span style='text-decoration:overline;'>&nbsp;Hz&nbsp;</span>"
        f, pxx = signal.periodogram(self.unFilteredDataFit, self.FITSampleRate, window='hann')
        self.FITlastFFT = f, pxx
        self.FFTdataPlotFIT.clear()
        self.FFTdataPlotFIT.setLogMode(y=True)
        self.FFTdataPlotFIT.plot(f, np.sqrt(pxx))
        self.FFTdataPlotFIT.addItem(self.FFTdataPlotFIT_lr)
        self.FFTdataPlotFIT.setLabel('bottom', "Frequency", units="Hz")
        self.FFTdataPlotFIT.setLabel('left', "PSD", units=vsqrtHztext)

        f, pxx = signal.periodogram(self.filteredDataFIT, self.FITSampleRate/ np.prod(self.decimationArr), window='hann')

        self.FFTFilteredDataPlotFIT.clear()
        self.FFTFilteredDataPlotFIT.setLogMode(y=True)
        self.FFTFilteredDataPlotFIT.plot(f, np.sqrt(pxx))
        self.FFTFilteredDataPlotFIT.setLabel('bottom', "Frequency", units="Hz")
        self.FFTFilteredDataPlotFIT.setLabel('left', "PSD filtered", units=vsqrtHztext)
        self.FFTFilteredDataPlotFIT.addItem(self.FFTFilteredDataPlotFIT_lr)

        self.updateCR()  # update also error estimate calc

    def updateCRRange(self):
        r = self.FFTdataPlotFIT_lr.getRegion()
        self.FFTFilteredDataPlotFIT_lr.setRegion(r)

    def copyFITtoInit(self):
        toBlock = [self.doubleSpinBox_FIT_f0,
                   self.doubleSpinBox_FIT_A,
                   self.doubleSpinBox_FIT_B,
                   self.doubleSpinBox_FIT_Gamma
                   ]
        for o in toBlock:
            o.blockSignals(True)
        popt = self.lastFIT[0]
        self.doubleSpinBox_FIT_f0.setValue(popt[0])
        self.doubleSpinBox_FIT_A.setValue(popt[1])
        self.doubleSpinBox_FIT_B.setValue(popt[2])
        self.doubleSpinBox_FIT_Gamma.setValue(popt[3])
        self.doubleSpinBox_FIT_DC.setValue(popt[4])

        self.doubleSpinBox_Frequency_Hz.setValue(popt[0])

        for o in toBlock:
            o.blockSignals(False)

    # set save records number
    def saveRecordsChanged(self):
        self.countRemainingToSave = int(self.doubleSpinBox_RecordsToSave.value())


    def updateCR(self):
        start, stop = self.FFTFilteredDataPlotFIT_lr.getRegion()
        self.FFTdataPlotFIT_lr.setRegion([start, stop])
        print(start, stop)
        f, pxx = self.FITlastFFT
        fSel = (f > start) & (f < stop)
        pxxSelVals = pxx[fSel]
        NSD = np.sqrt(np.mean(pxxSelVals))
        print("Noise:", NSD, " V/sqrt(Hz)")
        popt, pcov = self.lastFIT
        A = np.sqrt(popt[1]**2 + popt[2]**2)
        T2 = 1./popt[3]

        T = (self.doubleSpinBox_FilterStop_ms.value() - self.doubleSpinBox_FilterStart_ms.value())/1e3
        N = T * self.FITSampleRate
        CramerRao, C = cr.cr(A, NSD, T, N, T2=T2)
        print("cr = {:.2e}".format(CramerRao))
        text = "Freq. range = [{:.2f}, {:.2f}] Hz\n".format(start, stop)
        text += "R = {:.2e} V\n".format(A)
        text += "NSD = {:.3e} V/sqrt(Hz)\n".format(NSD)
        text += "C = {:.3e}\n".format(C)
        text += "cr = {:.1e} Hz\n".format(CramerRao)
        text += "dB(FSP) = {:.1f} fT\n".format(CramerRao * 1e6/3.5)
        text += "dB(FAP) = {:.1f} fT\n".format(CramerRao * 1e6/7.0)

        self.plainTextEdit_SensitivityFFT.setPlainText(text)

    def selectFolder(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Folder')
        self.lineEdit_FolderName.setText(folderpath+"\\")

    """
    import shutil

    total, used, free = shutil.disk_usage("/")
    
    print("Total: %d GiB" % (total // (2**30)))
    print("Used: %d GiB" % (used // (2**30)))
    print("Free: %d GiB" % (free // (2**30)))
"""
    def showDiskSpace(self):
        GB = 2**30
        total, used, free = shutil.disk_usage(self.lineEdit_FolderName.text())
        self.label_DiskSpace.setText(f"Free space: {free/GB:.2f} GB")

        # msg.buttonClicked.connect(self.popup_button)
    def genStartStop(self):
        # self.okButton_GeneratorStart.clicked.connect(self.genStartStop)
        if self.gen.gen.output_on:
            self.gen.stop()
        else:
            self.arbSet()

    def arbSet(self):
        arbObj = arbcalc(totalTime=float(self.doubleSpinBox_TotalTime_ms.value()) / 1000,
                         pumpTime=float(self.doubleSpinBox_PumpTime_ms.value()) / 1000,
                         dutyCycle=float(self.doubleSpinBox_DutyCycle.value()),
                         probeLevel=float(self.doubleSpinBox_ProbeLevel.value()),
                         pumpLevel=float(self.doubleSpinBox_PumpLevel.value()),
                         zeroLevel=float(self.doubleSpinBox_ZeroLevel.value()),
                         pumpFrequency=float(self.doubleSpinBox_Frequency_Hz.value()),
                         noPoints=int(self.doubleSpinBox_Points.value())
                         )
        arb = arbObj.arb()
        t, y = arb
        if not self.gen.arbLoad(y,
                                amplitude=max(y),
                                frequency=1000 / float(self.doubleSpinBox_TotalTime_ms.value())):
            self.statusbar.showMessage("The Generator is not accesible.", 2000)

        self.plotArb(t, y)
        self.gen.start()


##############################################################################################
#
#                    Start the app
#
##############################################################################################

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())

    # not working, icon set in te Qt Designer
    # app_icon = QtGui.QIcon()
    # app_icon.addFile('images/ZG-Speach-Bubble-16x16-icon.png', QtCore.QSize(16, 16))
    # app_icon.addFile('images/ZG-Speach-Bubble-24x24-icon.png', QtCore.QSize(24, 24))
    # app_icon.addFile('images/ZG-Speach-Bubble-32x32-icon.png', QtCore.QSize(32, 32))
    # app_icon.addFile('images/ZG-Speach-Bubble-48x48-icon.png', QtCore.QSize(48, 48))
    # app_icon.addFile('images/ZG-Speach-Bubble-256x256-icon.png', QtCore.QSize(256, 256))
    # app.setWindowIcon(app_icon)

    MainWindow = QtWidgets.QMainWindow()
    ui = MyUi()
    ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())
    # del MainWindow


if __name__.endswith('__main__'):
    main()