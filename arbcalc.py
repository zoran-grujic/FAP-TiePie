#  Copyright (c) 2021.
#  This code has been produced by Zoran D. Grujic and by the knowledge found on The Internet.
#  Please feel free to ask me for permission to use my code in your own projects. It is for your own well fare!

import numpy as np
from scipy import signal


class arbcalc():
    t = np.array(0)
    data = np.array(0)

    def __init__(self,
                 totalTime=0.1,
                 pumpTime=0.3,
                 zeroLevel=0,
                 pumpLevel=5,
                 probeLevel=1,
                 noPoints=10000,
                 pumpFrequency=300,
                 dutyCycle=0.5):

        self.totalTime = totalTime
        self.pumpTime = pumpTime
        self.zeroLevel = zeroLevel
        self.pumpLevel = pumpLevel
        self.probeLevel = probeLevel
        self.pumpFrequency = pumpFrequency
        self.noPoints = noPoints
        self.dutyCycle = dutyCycle

    def arb(self):
        # data = np.zeros(self.noPoints)+self.probeLevel
        self.t = np.linspace(0, self.totalTime, self.noPoints, endpoint=False)
        onePumpPeriod = 1.0 / self.pumpFrequency
        nPumpPeriods = int(self.pumpTime / onePumpPeriod)

        self.data = (1 + signal.square(2 * np.pi * self.pumpFrequency * self.t, duty=self.dutyCycle))/2
        self.data = self.data * (self.pumpLevel - self.zeroLevel) + self.zeroLevel

        nProbe = nPumpPeriods + self.dutyCycle - 1
        nProbe = int(self.noPoints * nProbe * onePumpPeriod/self.totalTime)
        for n in range(nProbe, self.noPoints):
            self.data[n] = self.probeLevel

        return self.t, self.data




