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
                 pumpTime=0.05,
                 zeroLevel=0,
                 pumpLevel=5,
                 probeLevel=1,
                 noPoints=50000,
                 pumpFrequency=100,
                 dutyCycle=0.5,
                 expAmplitude=0.1,
                 expRelaxation=1e3):

        self.totalTime = totalTime
        self.pumpTime = pumpTime
        self.zeroLevel = zeroLevel
        self.pumpLevel = pumpLevel
        self.probeLevel = probeLevel
        self.pumpFrequency = pumpFrequency
        self.noPoints = noPoints
        self.dutyCycle = dutyCycle
        self.expAmplitude = expAmplitude
        self.expRelaxation = expRelaxation*1e3

    def arb_old(self):
        # data = np.zeros(self.noPoints)+self.probeLevel
        self.t = np.linspace(0, self.totalTime, self.noPoints, endpoint=False)
        onePumpPeriod = 1.0 / self.pumpFrequency
        nPumpPeriods = int(self.pumpTime / onePumpPeriod)

        self.data = (1 + signal.square(2 * np.pi * self.pumpFrequency * self.t, duty=self.dutyCycle)) / 2
        self.data = self.data * (self.pumpLevel - self.zeroLevel) + self.zeroLevel

        nProbe = nPumpPeriods + self.dutyCycle - 1
        nProbe = int(self.noPoints * nProbe * onePumpPeriod / self.totalTime)
        for n in range(nProbe, self.noPoints):
            if self.totalTime <= self.pumpTime:
                self.data[n] = self.zeroLevel
            else:
                self.data[n] = self.probeLevel

        return self.t, self.data

    def arb(self):
        # data = np.zeros(self.noPoints)+self.probeLevel
        #print(f"arbcalc {self.totalTime=}")
        self.t = np.linspace(0, self.totalTime, self.noPoints, endpoint=False)
        sr = self.noPoints/self.totalTime
        onePumpPeriod = 1.0 / self.pumpFrequency
        nPumpPeriods = int(self.pumpTime / onePumpPeriod)

        if self.expAmplitude == 0:
            self.data = (1 + signal.square(2 * np.pi * self.pumpFrequency * self.t, duty=self.dutyCycle)) / 2
            self.data = self.data * (self.pumpLevel - self.zeroLevel) + self.zeroLevel
            nProbe = nPumpPeriods + self.dutyCycle - 1
            nProbe = int(self.noPoints * nProbe * onePumpPeriod / self.totalTime)
            for n in range(nProbe, self.noPoints):
                if self.totalTime <= self.pumpTime:
                    self.data[n] = self.zeroLevel
                else:
                    self.data[n] = self.probeLevel

        else:
            upTime = onePumpPeriod * self.dutyCycle
            downTime= onePumpPeriod * (1.0-self.dutyCycle)
            tUp = np.linspace(0, upTime, int(upTime*sr), endpoint=False)
            tDown = np.linspace(0, downTime, int(downTime*sr), endpoint=False)

            upData = self.pumpLevel - self.expAmplitude*(1-np.exp(-self.expRelaxation * tUp))
            downData = self.zeroLevel + self.expAmplitude*(1-np.exp(-self.expRelaxation * tDown))
            cycleData = np.concatenate((upData, downData))
            pumpData = np.tile(cycleData, nPumpPeriods-1)
            pumpData = np.concatenate((pumpData, upData)) #add one more Pump level
            probeData = np.zeros(self.noPoints-len(pumpData)) + self.probeLevel

            self.data = np.concatenate((pumpData, probeData))



        return self.t, self.data