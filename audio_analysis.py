#!/usr/bin/env python
#Author: Shriphani Palakodety
#Environment monitoring for the hearing impaired.

import logging
#import pyaudio
import datetime
import wave
import sys
import numpy
import struct
import os
from gntp import notifier
from matplotlib import pyplot as plot

from VAD import VAD


# VAD constants
INSTANCES_VAD_IS_RUN = 0
AVERAGE_INTENSITY_OF_RUNS = 0
DURATION = 3   # length of 1 recording
OUTPUT_FILE = 'analysis.wav'

# pyaudio constants
#PYAUDIO_INSTANCE = pyaudio.PyAudio()
PYAUDIO_CHANNELS = 1
PYAUDIO_RATE = 44100
PYAUDIO_INPUT = True
PYAUDIO_FRAMES_PER_BUFFER = 1024

# Listener constants
NUM_FRAMES = PYAUDIO_RATE / PYAUDIO_FRAMES_PER_BUFFER
LAST_NOTIFICATION_TIME = None

#logging constants
LOG_FILE_NAME = 'decisions.log'
LOG_FILE_FD = open(LOG_FILE_NAME, 'w')
logging.basicConfig(level=logging.ERROR) # this guy exists because Growl is angry about something



def analyze():
    '''Invokes the VAD and logs the decision'''
    


    abs_samples,frame_chunks,speech_flag_final,frame_counter_flag,ampXPoints =  VAD.moattar_homayounpour(OUTPUT_FILE)

    plot = plot_multi_colour(abs_samples,frame_chunks,speech_flag_final,frame_counter_flag,ampXPoints)
    

    return plot

def plot_multi_colour(amplitude_array, frame_chunks,frame_flag_list,flag_counter_list,xPoints):
    '''
        Plots multi color sample_array based on value of flag_array
        amplitude_array: amplitude list
        frame_chunks: pair of x-coords for frame intervals
        frame_flag_list: activity flag for each frame
        flag_counter_list: counter value for each frame
        xPoints: x axis points (time)
     '''
    
    wave_color_flag = []
    wave_color_xPoints = []        
   
    
    for i, frame_bounds in enumerate(frame_chunks):
        frame_start = frame_bounds[0]
        frame_end = frame_bounds[1]
        frame_points = range(frame_start,frame_end)
        frame_length = frame_end - frame_start + 1
        frame = amplitude_array[frame_start:frame_end]

        # get x coordinates for teh frame (time)
        frame_xPoints = xPoints[frame_start:frame_end]
        #plot red or blue based on frame flag
        if frame_flag_list[i]:

            plot.plot(frame_xPoints, frame,'r')
        else:
            plot.plot(frame_xPoints, frame,'b')
     
    return plot

def exit():
    LOG_FILE_FD.close()
    OUTPUT_FILE.close()


if __name__ == "__main__":
    
    # while True:
    #     record(DURATION)
    
    fig = plot.figure()
    plot.subplot(111)
    plot = analyze()
    #plot.show()
    fig.savefig('analysis.pdf')

