'''
This script is designed to simulate the demodulation of modulated fields
as the individual frequency components interact with an absorptive and
dispersive medium. The general application for these techniques are for 
precision spectroscopy and can be used to investigate theoretical
lineshapes for common spectroscopic features. 

In particular, this script attempts to tie together the multiple and 
complex representations of optical fields. Three forms of modulation are
introduced: amplitude modulation, phase modulation, and frequency modulation.

The three types of modulation are typically present in all physical
scenarios. 

In particular, the interplay between various sidebands and the square-law
dependence of intensity detectors produce beatnotes between the spectral
components as they interact with a complex absorption profile. 

To calculate the demodulated signal the following scheme is followed:

1)  input  parameters dictating the absorption lineshape and amplitude
	input  parameters dictating the modulated laser 

2)	calculate the sideband frequency shifts relative to line center and 
	they accompanying amplitudes

3)	interact the field amplitude with the absorption line producing
	the products Sum[T(omega+n*omega_mod(i))*J(n,mod_index)] over a finite
	range of n (computed to a certain threshold in the finite sideband
	approximation)

4)	convert to the time domain and take the output field and take its 
	absolute value squared to determine the intensity

5)	convert the intensity to the frequency domain and measure the amplitude
	at the desired demodulation frequency.

6)	repeat for various detunings to calculate the total error signal

This approach is desireable because it functionally allows the extension
to arbitrary waveform modulation. Ultimately, an arbitrary waveform
may be mixed onto a laser which is then demodulated with the original signal.
This may potentially be capable of new spectroscopic insight due to the
large parameter space it can sketch out.

Additionally, it allows for calculations which may be limited by a small (<5)
finite sideband approximation or cascaded modulation which can produce
a large number of analytical cross terms which contribute to the various
beatnotes.
'''

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, \
    QVBoxLayout, QWidget, QComboBox, QPushButton, QGridLayout, QSpinBox

import pyqtgraph as pg
import numpy as np

from scipy.fftpack import fft

Description ="""This script is designed to simulate the demodulation of modulated fields
as the individual frequency components interact with an absorptive and
dispersive medium. The general application for these techniques are for 
precision spectroscopy and can be used to investigate theoretical
lineshapes for common spectroscopic features. 

In particular, this script attempts to tie together the multiple and 
complex representations of optical fields. Three forms of modulation are
introduced: amplitude modulation, phase modulation, and frequency modulation.

The three types of modulation are typically present in all physical
scenarios. 

In particular, the interplay between various sidebands and the square-law
dependence of intensity detectors produce beatnotes between the spectral
components as they interact with a complex absorption profile. 

To calculate the demodulated signal the following scheme is followed:

1)  input  parameters dictating the absorption lineshape and amplitude
    input  parameters dictating the modulated laser 

2)  calculate the sideband frequency shifts relative to line center and 
    they accompanying amplitudes

3)  interact the field amplitude with the absorption line producing
    the products Sum[T(omega+n*omega_mod(i))*J(n,mod_index)] over a finite
    range of n (computed to a certain threshold in the finite sideband
    approximation)

4)  convert to the time domain and take the output field and take its 
    absolute value squared to determine the intensity

5)  convert the intensity to the frequency domain and measure the amplitude
    at the desired demodulation frequency.

6)  repeat for various detunings to calculate the total error signal

This approach is desireable because it functionally allows the extension
to arbitrary waveform modulation. Ultimately, an arbitrary waveform
may be mixed onto a laser which is then demodulated with the original signal.
This may potentially be capable of new spectroscopic insight due to the
large parameter space it can sketch out.

Additionally, it allows for calculations which may be limited by a small (<5)
finite sideband approximation or cascaded modulation which can produce
a large number of analytical cross terms which contribute to the various
beatnotes.
"""

class Slider(QWidget):
    def __init__(self, minimum, maximum, name, parent=None):
        super(Slider, self).__init__(parent=parent)
        self.name = name
        self.verticalLayout = QVBoxLayout(self)
        self.horizontalLayout = QHBoxLayout()

        spacerItem2 = QSpacerItem(10,20)
        self.horizontalLayout.addItem(spacerItem2)

        self.label = QLabel(self)
        self.verticalLayout.addWidget(self.label)
        self.box = QSpinBox(self)
        self.verticalLayout.addWidget(self.box)
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Vertical)
        self.horizontalLayout.addWidget(self.slider)
        spacerItem1 = QSpacerItem(20, 20, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.resize(self.sizeHint())

        self.minimum = minimum
        self.maximum = maximum
        self.slider.valueChanged.connect(self.setLabelValue)

        self.x = None
        self.setLabelValue(self.slider.value())

        self.box.valueChanged.connect(self.setLabelValue)
        self.x = None
        self.setLabelValue(self.box.value())

    def setLabelValue(self, value):
        self.x = self.minimum + (float(value) / (self.slider.maximum() - self.slider.minimum())) * (
        self.maximum - self.minimum)
        self.label.setText(self.name + " \n {0:.4g}".format(self.x))

class Widget(QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent=parent)

        self.setWindowTitle("Modulation Spectroscopy")

        self.horizontalLayout = QHBoxLayout(self)
        self.verticalLayout = QVBoxLayout(self)

        self.grid=QGridLayout(self)

        #self.s1 	= pg.SpinBox(value = 1.05, dec =True, step = 0.5, minStep = 0.01)
        #self.horizontalLayout.addWidget(self.s1)

        self.c1=QComboBox(self)
        self.c1.addItem("Frequency Modulation")
        self.c1.addItem("Two Tone Frequency Modulation")
        self.c1.addItem("FM and TTFMS")

        self.t1		= QLabel(Description)
        self.horizontalLayout.addWidget(self.t1)

        self.w1 	= Slider(0.01, 1000, "Gamma")
        self.horizontalLayout.addWidget(self.w1)

        self.w2 	= Slider(0.01, 100, "Mod Freq 1")
        self.horizontalLayout.addWidget(self.w2)

        self.w3     = Slider(0.01, 100, "Mod Freq 2")
        self.horizontalLayout.addWidget(self.w3)

        self.w4 	= Slider(50, 100, "Laser Freq")
        self.horizontalLayout.addWidget(self.w4)

        self.w5 	= Slider(0.01, 10, "Mod Index 1")
        self.horizontalLayout.addWidget(self.w5)

        self.w6     = Slider(0.01, 10, "Mod Index 2")
        self.horizontalLayout.addWidget(self.w6)

        self.win 	= pg.GraphicsWindow(title="Basic plotting examples")
        self.horizontalLayout.addWidget(self.win)

        self.p1 	= self.win.addPlot(title="Absorption Line",row=1,col=1)
        self.p2 	= self.win.addPlot(title="Error Signal",row=2,col=1)
        self.p3 	= self.win.addPlot(title="Laser in Frequency Domain", row=1, col=2)
        self.p4 	= self.win.addPlot(title="Laser in Time Domain",row=2,col=2)

        self.curve1 = self.p1.plot(pen='r',width='10')
        #self.curveA = self.p1.plot(pen='b',width='100')
        self.curve2 = self.p2.plot(pen='b')
        self.curve2b= self.p2.plot(pen='c')
        self.curve3 = self.p3.plot(pen='g')
        self.curve4 = self.p4.plot(pen='c')
        self.update()

        self.w1.slider.valueChanged.connect(self.update)
        self.w1.box.valueChanged.connect(self.update)
        self.w2.slider.valueChanged.connect(self.update)
        self.w2.box.valueChanged.connect(self.update)
        self.w3.slider.valueChanged.connect(self.update)
        self.w3.box.valueChanged.connect(self.update)
        self.w4.slider.valueChanged.connect(self.update)
        self.w4.box.valueChanged.connect(self.update)
        self.w5.slider.valueChanged.connect(self.update)
        self.w5.box.valueChanged.connect(self.update)
        self.w6.slider.valueChanged.connect(self.update)
        self.w6.box.valueChanged.connect(self.update)

        self.c1.activated.connect(self.update)

    def update(self):
        gamma 		= self.w1.x
        fmfmod      = self.w2.x
        fmod1 		= self.w2.x
        fmod2       = self.w3.x
        flaser 		= self.w4.x
        M1 			= self.w5.x
        M2          = self.w6.x
        x 			= np.linspace(-10000, 10000, 1000)
        t 			= np.linspace(0,1000,1000)
        x1			= np.linspace(0,10000,1000)
        absorption 	= lambda val: 1-0.5*np.exp(-(flaser+val)**2/(2*gamma**2))
        laser      	= lambda val:(np.cos(flaser*t*np.pi/180)*np.cos(M1*np.sin(fmod1*t*np.pi/180))*np.cos(M2*np.sin(fmod2*t*np.pi/180)))
        FMerrorsig  = lambda val:(M1/2)*absorption(val)*(absorption(val-fmfmod)-absorption(val+fmfmod))
        TTFMS       = lambda val:(M1/2)*(M2/2)*(absorption(val-fmod1)*absorption(val-fmod2)+absorption(val+fmod1)*absorption(val+fmod2)-2*absorption(val)**2)
        self.curve1.setData(x1,absorption(x))
        if self.c1.currentText() == "Frequency Modulation":
            self.curve2.setData(x1,FMerrorsig(x))
            self.curve2b.setData([0])
        elif self.c1.currentText() == "Two Tone Frequency Modulation":
            self.curve2.setData(x1,TTFMS(x))
            self.curve2b.setData([0])
        elif self.c1.currentText() == "FM and TTFMS":
            fmfmod=fmod1-fmod2
            self.curve2.setData(x1,FMerrorsig(x))
            self.curve2b.setData(x1,TTFMS(x))
        self.curve3.setData(abs(fft(laser(x))))
        self.curve4.setData(laser(x))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())