#!/usr/bin/env python
# original code by https://github.com/shriphani

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
import csv as csv
import getopt
import itertools as itr
import multiprocessing as multiprocessing
import glob as glob
from VAD import VAD
#import timing


# VAD constants
MH_FRAME_DURATION = 20
# frame length in milliseconds for Moattar & Homayounpour (increased from
# 10 to 100 for speed)

# plotting constants
# if we need to save plots (csv stored by default for all runs)
PLOT_SAVE = False
PRINT_SILENCE = True
SAVE_AS_NUMPY = False
SAVE_AS_CSV = True


def main(argv):
    input_arg = ''
    print_silence = False
    isFile = True

    try:
        opts, args = getopt.getopt(argv, "hsi:d:", ["input="])
    except getopt.GetoptError:
        return False
    for opt, arg in opts:
        if opt == '-h':
            print 'audio_analyze.py -i <inputwavfile> \n or audio_analyze.py -d <inputwavdir>'
            sys.exit()
        elif opt in ("-i", "--input"):
            input_arg = arg
            isFile = True
        elif opt == "-d":
            input_arg = arg
            isFile = False
        elif opt == "-s":
            print_silence = True
    return input_arg, isFile, print_silence


def analyze(input_wav_file, print_silence, start_time):
    '''Invokes the VAD and plots waveforms'''

    abs_samples, frame_chunks, speech_flag_final, siren_flag_final, ampXPoints, sampling_frequency = VAD.moattar_homayounpour(
        input_wav_file, MH_FRAME_DURATION, print_silence, start_time)
    if not print_silence:
        print("Frame analysis end --- %s seconds ---" %
              (time.time() - start_time))
        print_string = "Frame analysis end --- %s seconds ---\n" % (
            time.time() - start_time)
    # call function to create csv list and multi color plots (if needed)
    plot_figure, print_string, frame_csv_rows = plot_multi_colour(
        abs_samples, frame_chunks, speech_flag_final, siren_flag_final, ampXPoints, print_string, print_silence, start_time)
    #print(" Plotting end --- %s seconds ---" % (time.time() - start_time))

    print_string += "Plotting end --- %s seconds ---\n" % (
        time.time() - start_time)
    print_string += "Sampling Frequency: %d  Hz\n" % sampling_frequency
    print_string += "Frame Duration: %d ms\n" % MH_FRAME_DURATION

    return plot_figure, print_string, frame_csv_rows


def set_plot_parameters(plot_figure, xPoints, print_string):
    ''' Sets axis and grid settings for plots'''

    ax1 = plot_figure.add_subplot(211)
    ax2 = plot_figure.add_subplot(212)

    # Remove the plot frame lines. They are unnecessary chartjunk.

    ax1.spines["top"].set_visible(False)
    ax1.spines["bottom"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_visible(False)

    ax2.spines["top"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["left"].set_visible(False)

    # Ensure that the axis ticks only show up on the bottom and left of the plot.
    # Ticks on the right and top of the plot are generally unnecessary
    # chartjunk.
    ax1.get_xaxis().tick_bottom()
    ax1.get_yaxis().tick_left()
    ax2.get_xaxis().tick_bottom()
    ax2.get_yaxis().tick_left()

    # logic to show ticks and labels only at major intervals based on x
    # axis length

    xPoints_max = max(xPoints)

    if(xPoints_max > 36000):
        x_Step = 3600
    elif(xPoints_max > 3600):
        x_Step = 300
    elif(xPoints_max > 1200):
        x_Step = 120
    elif(xPoints_max > 60):
        x_Step = 30
    else:
        x_Step = 5

    x_Display_Points = np.arange(min(xPoints), xPoints_max + 1, x_Step)
    x_Display_Points_Label = [str(dt.timedelta(seconds=x))
                              for x in x_Display_Points]

    ax1.xaxis.set_ticks(x_Display_Points, )
    ax1.set_xticklabels(x_Display_Points_Label, rotation=45, ha='right')
    ax2.xaxis.set_ticks(x_Display_Points, )
    ax2.set_xticklabels(x_Display_Points_Label, rotation=45, ha='right')

    ax1.grid(True, which='major', axis='x')
    ax2.grid(True, which='major', axis='x')
    print_string += " Plotting axis setup end --- %s seconds ---\n" % (
        time.time() - start_time)
    return plot_figure, ax1, ax2, print_string


def plot_multi_colour(amplitude_array, frame_chunks, frame_speech_flag, frame_siren_flag, xPoints, print_string, print_silence, start_time):
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

    input_speech_length = 0
    input_silence_length = 0
    input_siren_length = 0
    frame_csv_rows = []

    # create two vertically aligned plots
    plot_figure = plot.figure(num=None, figsize=(
        48, 16), dpi=80, facecolor='w', edgecolor='k')

    plot_figure, ax1, ax2, print_string = set_plot_parameters(
        plot_figure, xPoints, print_string)

    for i, frame_bounds in enumerate(frame_chunks):
        frame_start = frame_bounds[0]
        frame_end = frame_bounds[1]
        frame_points = range(frame_start, frame_end)
        frame_length = frame_end - frame_start + 1
        frame = amplitude_array[frame_start:frame_end]

        # get x coordinates for teh frame (time)
        frame_xPoints = xPoints[frame_start:frame_end]
        frame_time_length = xPoints[frame_end] - xPoints[frame_start]
        frame_xPoints_points = len(frame_xPoints)
        # create row to add to csv file
        frame_row = zip(frame_xPoints, frame,
                        itr.repeat(int(frame_speech_flag[i]), frame_xPoints_points), itr.repeat(int(frame_siren_flag[i]), frame_xPoints_points))

        # plot colors based on speech or siren flag
        if frame_siren_flag[i] == 1:
            input_siren_length += frame_time_length
            if PLOT_SAVE:
                ax1.plot(frame_xPoints, frame, 'k')
        else:
            if PLOT_SAVE:
                ax1.plot(frame_xPoints, frame, 'c')

        if frame_speech_flag[i] == 1:
            input_speech_length += frame_time_length
            if PLOT_SAVE:
                ax2.plot(frame_xPoints, frame, 'k')
        else:
            if PLOT_SAVE:
                ax2.plot(frame_xPoints, frame, 'c')

            input_silence_length += frame_time_length

        # Append frame rows to main csv list
        frame_csv_rows.extend(frame_row)

    # plot.show()
    print_string += " Plotting loop end --- %s seconds ---\n" % (
        time.time() - start_time)

    # print % of speech vs total

    speech_ratio = round((input_speech_length * 100 /
                          (input_speech_length + input_silence_length)), 2)
    print_string += "Siren Length (s): %d \n" % input_siren_length
    print_string += "Speech Length (H:i:s): %s \n" % str(
        dt.timedelta(seconds=(input_speech_length)))
    print_string += "Speech Length (s): %d \n" % input_speech_length
    print_string += "Total Length of audio(H:i:s):  %s \n" % str(
        dt.timedelta(seconds=(input_speech_length + input_silence_length)))
    print_string += "Speech Ratio: %f \n" % speech_ratio

    if PLOT_SAVE:

        if not print_silence:
            print "Plots prepared ..."

    return plot_figure, print_string, frame_csv_rows


def save_as_numpy(frame_rows):
    frame_array = np.asarray(frame_rows)
    print frame_array


def process_file(input_file, print_silence, start_time, plot_save):
    plot_figure, print_string, frame_csv_rows = analyze(
        input_file, print_silence, start_time)

    filename = os.path.basename(input_file)
    filename = os.path.splitext(filename)[0]
    date_string = dt.datetime.now().strftime("%Y-%m-%d-%H-%M")
    if plot_save:
        #fig = plot_process.figure()
        # show plot if needed
        plot_figure.show()
        # save plot as png
        plot_figure.savefig('png/' + filename + '-' + date_string +
                            '-' + str(MH_FRAME_DURATION) + 'ms.png')
        # close plot

        plot.close(plot_figure)

    # print logs and timestamps to txt file
    with open('txt/' + filename + '-' + date_string + '-' + str(MH_FRAME_DURATION) + 'ms.txt', "w") as text_file:
        print_string += "End --- %s seconds ---\n" % (time.time() - start_time)
        text_file.write(print_string)
     # save as numpy
    if SAVE_AS_NUMPY:
        with open('numpy/' + filename + '-' + date_string + '-' + str(MH_FRAME_DURATION) + 'ms.npy', "w") as numpy_file:
            np.save(numpy_file, frame_csv_rows)
    # print csv list to csv file
    if SAVE_AS_CSV:
        with open('csv/' + filename + '-' + date_string + '-' + str(MH_FRAME_DURATION) + 'ms.csv', "w") as csv_file:
            csv_writer = csv.writer(csv_file)
            header = ['Amplitude', 'time', 'speechFlag', 'SirenFlag']
            csv_writer.writerow(header)
            [csv_writer.writerow(row) for row in frame_csv_rows]
    if not print_silence:
        print print_string
        #print("End --- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":

    start_time = time.time()

    print start_time

    try:
        # fetch input command arguments or throw exception
        inputFileorDir, isFile, print_silence = main(sys.argv[1:])
        if print_silence:
            print "Print is set to silent mode. Nothing will be printed"
        else:
            print "Print is NOT set to silent mode. Output will be printed"

        if(isFile):

            # input argument is a file
            if(inputFileorDir):
                process_file(inputFileorDir, print_silence,
                             start_time, PLOT_SAVE)
            else:
                print 'File %s  does not exist' % inputFileorDir
                sys.exit()
        else:

            # input argument  is a directory
            # create thread for
            # print inputFileorDir
            p = multiprocessing.Pool()
            for f in glob.glob(inputFileorDir + "/*.wav"):
                # launch a process for each file
                # The result will be approximately one process per CPU core
                # available.
                p.apply_async(process_file, args=(f, print_silence))

            p.close()
            p.join()  # Wait for all child processes to close.
            if not print_silence:
                print "All files have been processed in %s seconds" % (time.time() - start_time)

    except Exception, e:
        print(traceback.format_exc())
        sys.exit()
