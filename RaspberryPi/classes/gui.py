'''
@file gui.py
@brief Classes to manage the control parameters and user interface.
'''

from enum import Enum
import numpy

_class_debug = False

class PiSynthStatus(Enum):
    '''
    Defines the various status of the application.
    '''

    # Ready to accept commands, initialization complete
    # MIDI is working on current bank
    STANDBY = 1
    # The application is loading a new bank of samples
    LOADING = 2
    # The application is recording a sample
    RECORDING = 3
    # The application is set to record samples.
    # Any not button start recording a new sample, according
    # to the sampling parameters.
    SAMPLEMODE = 4

