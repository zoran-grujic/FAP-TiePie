
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running theWorker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
