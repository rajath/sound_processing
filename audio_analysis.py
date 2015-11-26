#!/usr/bin/env python
#Author: Shriphani Palakodety
#Environment monitoring for the hearing impaired.

import logging
#import pyaudio
import datetime
import wave
import sys
import numpy as np
import struct
import os
from gntp import notifier
from matplotlib import pyplot as plot
import matplotlib.dates as md
import datetime as dt

from VAD import VAD


# VAD constants
INSTANCES_VAD_IS_RUN = 0
AVERAGE_INTENSITY_OF_RUNS = 0
DURATION = 3   # length of 1 recording
INPUT_FILE = 'analysis.wav'

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



def analyze(input_wav_file):
    '''Invokes the VAD and logs the decision'''
    


    abs_samples,frame_chunks,speech_flag_final,frame_counter_flag,ampXPoints =  VAD.moattar_homayounpour(input_wav_file)

    plot = plot_multi_colour(abs_samples,frame_chunks,speech_flag_final,frame_counter_flag,ampXPoints)
    

    return plot, ampXPoints

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

        #print frame_xPoints    
        
    
    

    #logic to show ticks and labels only at major intervals based on x axis length

    xPoints_max = max(xPoints)

    if(xPoints_max > 36000):
        x_Step = 3600
    elif(xPoints_max > 3600):
        x_Step = 600
    elif(xPoints_max > 60):
        x_Step = 30
    else:
        x_Step = 5    


    x_Display_Points = np.arange(min(xPoints), xPoints_max+1, x_Step)
    x_Display_Points_Label = [str(dt.timedelta(seconds=x)) for x in x_Display_Points]

    plot.xticks(x_Display_Points,x_Display_Points_Label)
    plot.xticks( rotation=45 )
    plot.grid(True,which='major')

    #print x_Display_Points_Label 
    return plot

def exit():
    LOG_FILE_FD.close()
    OUTPUT_FILE.close()


if __name__ == "__main__":
    
    # while True:
    #     record(DURATION)
    
    fig = plot.figure()
    plot ,ampXPoints = analyze(INPUT_FILE)

    #plot.show()
    fig.savefig('analysis.png')

