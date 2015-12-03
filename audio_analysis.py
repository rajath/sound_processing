#!/usr/bin/env python
#Author: Shriphani Palakodety
#Environment monitoring for the hearing impaired.

import traceback
#import pyaudio
import datetime
import time
import wave
import sys
import numpy as np
import struct
import os
from matplotlib import pyplot as plot
import matplotlib.dates as md
import datetime as dt
import sys, getopt
from VAD import VAD
#import timing





# VAD constants

MH_FRAME_DURATION = 100
#frame length in milliseconds for Moattar & Homayounpour (increased from 10 to 100 for speed)


def main(argv):
   inputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hi:",["input="])
   except getopt.GetoptError:
      return False
   for opt, arg in opts:
      if opt == '-h':
         print 'audio_analyze.py -i <inputfile> '
         sys.exit()
      elif opt in ("-i", "--input"):
         inputfile = arg
         return inputfile   

def analyze(input_wav_file):
    '''Invokes the VAD and logs the decision'''
    


    abs_samples,frame_chunks,speech_flag_final,ampXPoints,sampling_frequency =  VAD.moattar_homayounpour(input_wav_file,MH_FRAME_DURATION)

    #print(" Frame analysis end --- %s seconds ---" % (time.time() - start_time))
    print_string = " Frame analysis end --- %s seconds ---\n" % (time.time() - start_time)
    plot,print_string = plot_multi_colour(abs_samples,frame_chunks,speech_flag_final,ampXPoints,print_string)
    #print(" Plotting end --- %s seconds ---" % (time.time() - start_time))
    print_string += " Plotting end --- %s seconds ---\n" % (time.time() - start_time)
    print_string += "Sampling Frequency: %d  Hz\n" % sampling_frequency
    print_string += "Frame Duration: %d ms\n" % MH_FRAME_DURATION


    return plot, print_string

def plot_multi_colour(amplitude_array, frame_chunks,frame_flag_list,xPoints,print_string):
    '''
        Plots multi color sample_array based on value of flag_array
        amplitude_array: amplitude list
        frame_chunks: pair of x-coords for frame intervals
        frame_flag_list: activity flag for each frame
        flag_counter_list: counter value for each frame
        xPoints: x axis points (time)
     '''
    print "Creating plots ..."
    wave_color_flag = []
    wave_color_xPoints = []        
   
    input_speech_length = 0
    input_silence_length = 0
    
    for i, frame_bounds in enumerate(frame_chunks):
        frame_start = frame_bounds[0]
        frame_end = frame_bounds[1]
        frame_points = range(frame_start,frame_end)
        frame_length = frame_end - frame_start + 1
        frame = amplitude_array[frame_start:frame_end]

        # get x coordinates for teh frame (time)
        frame_xPoints = xPoints[frame_start:frame_end]
        frame_time_length = xPoints[frame_end] - xPoints[frame_start]
        
        #plot red or blue based on frame flag
        if frame_flag_list[i]:
            input_speech_length += frame_time_length
            plot.plot(frame_xPoints, frame,color=[214/255., 39/255., 40/255.])
        else:
            plot.plot(frame_xPoints, frame,color=[31/255., 119/255., 180/255.])
            input_silence_length += frame_time_length

        #print frame_xPoints    
        
    
    # print % of speech vs total

    speech_ratio = round((input_speech_length * 100 / (input_speech_length + input_silence_length)),2)
    print_string += "Speech Length (H:i:s): %s \n" % str(dt.timedelta(seconds=(input_speech_length)))
    print_string += "Speech Length (s): %d \n" % input_speech_length
    print_string += "Total Length of audio(H:i:s):  %s \n" % str(dt.timedelta(seconds=(input_speech_length + input_silence_length)))
    print_string += "Speech Ratio: %f \n" % speech_ratio

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
    plot.grid(True,which='major',axis='x')
    # Remove the plot frame lines. They are unnecessary chartjunk.    
    ax = plot.subplot(111)    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)    
      
    # Ensure that the axis ticks only show up on the bottom and left of the plot.    
    # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
    ax.get_xaxis().tick_bottom()    
    ax.get_yaxis().tick_left() 

    print "Plots created ..."
    #print x_Display_Points_Label 
    return plot,print_string



if __name__ == "__main__":

    start_time = time.time()
    
    try:
        input_file = main(sys.argv[1:])
        if(input_file):
        
            fig = plot.figure()
            plot ,print_string = analyze(input_file)
            
           

            #plot.show()
            filename = os.path.basename(input_file)
            filename = os.path.splitext(filename)[0]
            date_string = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
            #write print string to file and save plot as png
            fig.savefig('png/'+ filename +'-' + date_string + '-' + str(MH_FRAME_DURATION) + 'ms.png')
            with open('txt/'+ filename +'-' + date_string + '-' +str(MH_FRAME_DURATION) + 'ms.txt', "w") as text_file:
                print_string += "End --- %s seconds ---\n" % (time.time() - start_time)
                text_file.write(print_string)
        else:
            print 'No input file'
            sys.exit()

        print print_string
        #print("End --- %s seconds ---" % (time.time() - start_time))

    except Exception,e: 
        print(traceback.format_exc())
        sys.exit()


