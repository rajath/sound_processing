#!/usr/bin/env python



#import required modules
from numpy.fft import *
from numpy import log10, sqrt
import numpy as np
import math
import wave
import struct
import csv
from matplotlib import pyplot
from array import array



SAMPLING_FREQUENCY = 44100 #redundant as we calculate sampling frequency now
MLD_FRAME_DURATION = 30 #frame length in milliseconds for milanovic, lukac and domazetovic
MLD_SAMPLES_PER_SECOND = SAMPLING_FREQUENCY
MLD_SAMPLES_PER_FRAME = int(MLD_SAMPLES_PER_SECOND * (MLD_FRAME_DURATION / 1000.0))

MH_FRAME_DURATION = 50 
#frame length in milliseconds for Moattar & Homayounpour (increased from 10 to 100 for speed)
MH_SAMPLES_PER_SECOND = SAMPLING_FREQUENCY
MH_SAMPLES_PER_FRAME = int(MH_SAMPLES_PER_SECOND * (MH_FRAME_DURATION / 1000.0))


def get_mh_samples_per_frame(sampling_frequency=SAMPLING_FREQUENCY,mh_frame_duration=MH_FRAME_DURATION):

    '''
        Get samples per frame based on caluclated sampling frequency

    '''
    return    int(sampling_frequency * (mh_frame_duration / 1000.0))       


def chunk_frames_indices(samples, samples_per_frame):
    '''
    Args:
        - samples: 16 bit values representing a sampled point.

    Returns:
        - an array of <FRAME_DURATION> length chunks
    '''
    return zip(
        range(0, len(samples), samples_per_frame),
        range(samples_per_frame, len(samples), samples_per_frame)
    )

def energy(samples):
    '''
    Args:
        - samples of a signal
    '''
    return sum([x**2 for x in samples])

def real_imaginary_freq_domain(samples):
    '''
    Apply fft on the samples and return the real and imaginary
    parts in separate 
    '''
    freq_domain = fft(samples)
    
    freq_domain_real = [abs(x.real) for x in freq_domain]
    freq_domain_imag = [abs(x.imag) for x in freq_domain]


    return freq_domain_real, freq_domain_imag

def get_dominant_freq(real_freq_domain_part, imag_freq_domain_part,sampling_frequency):
    '''Returns the dominant frequency'''
    max_real = max(real_freq_domain_part)
    max_imag = max(imag_freq_domain_part)

    dominant_freq = 0

    if (max_real > max_imag):
        dominant_freq = abs(fftfreq(len(real_freq_domain_part), d=(1.0/sampling_frequency))[real_freq_domain_part.index(max_real)])
    else:
        dominant_freq = abs(fftfreq(len(imag_freq_domain_part), d=(1.0/sampling_frequency))[imag_freq_domain_part.index(max_imag)])

    #print dominant_freq    
    return dominant_freq

def get_freq_domain_magnitudes(real_part, imaginary_part):
    '''Magnitudes of the real-imag frequencies'''
    return [sqrt(x**2 + y**2) for x, y in zip(real_part, imaginary_part)]

def get_sfm(frequencies):

    a_mean = arithmetic_mean(frequencies)
    if a_mean > 0:
        return 10 * log10(geometric_mean(frequencies) / a_mean)
    else:
        return 0     

def geometric_mean(frame):
 
        return 10 ** (sum([log10(x) for x in frame if x > 0]) / float(len(frame)))


def arithmetic_mean(frame):
    return float(sum(frame)) / float(len(frame))

def get_sample_intensity(samples):
    return 20.8 * log10(sqrt(sum([x ** 2 for x in samples])/float(len(samples))))

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r  

def locateInArray(list1, list2):
    ''' Locates a list within a list and sends back index
    '''
    x = 0
    y = 0
    for x in xrange(len(list1)):
        if list1[x] == list2[0]:
            counter = 0
            for y in xrange(len(list2)):
                try:
                    if list1[x+y] != list2[y]:
                        break
                    else:
                        counter += 1
                except IndexError:
                    return -1
            if counter == len(list2):
                return x
    return -1    

class VAD(object):

    @staticmethod
    def moattar_homayounpour(wave_file,mh_frame_duration):
        '''
        Args:
            - wave_file : filename containing the audio to be processes
            - mh_frame_duration: frame length in ms for moattar homayanpour analysis
  
        '''

        in_file = wave.open(wave_file, 'rb')

        #set primary thresholds for energy, frequency and SFM
        #these values were determined using experiements by the authors
        #themselves
        energy_prim_thresh = 40
        freq_prim_thresh = 185
        sfm_prim_thresh = 5
        n_frames = in_file.getnframes()
        n_channels = in_file.getnchannels()
        sample_width = in_file.getsampwidth()
        sampling_frequency = in_file.getframerate()
        print n_frames

        ampXPoints = []
        ampYPoints = []
        xPoints = []
        y1Points = []
        y2Points = []
        y3Points = []

        print sampling_frequency

        samples = in_file.readframes(n_frames)

        if sample_width == 1: 
            fmt = "%iB" % n_frames # read unsigned chars
        elif sample_width == 2:
            fmt = "%ih" % n_frames # read signed 2 byte shorts
        else:
            raise ValueError("Only supports 8 and 16 bit audio formats.")
        abs_samples = struct.unpack(fmt, samples)

        abs_samples = normalize(abs_samples)

        ampXPoints = range(n_frames)
        ampXPoints[:] = [float(x) / sampling_frequency for x in ampXPoints]


        #compute the intensity
        intensity = get_sample_intensity(abs_samples)

        #print intensity

        #frame attribute arrays
        frame_energies = []  #holds the energy value for each frame
        frame_max_frequencies = []  #holds the dominant frequency for each frame
        frame_SFMs = []  #holds the spectral flatness measure for every frame
        frame_voiced = []  #tells us if a frame contains silence or speech

        #attributes for the entire sampled signal
        min_energy = 0
        min_dominant_freq = 0
        min_sfm = 0

        #check for the 30 frame mark
        thirty_frame_mark = False

        #chunk frame indices here creates a list of time intervale pairs orresponsing to each frame   
        frame_chunks = chunk_frames_indices(abs_samples, get_mh_samples_per_frame(sampling_frequency,mh_frame_duration))

        #tracks counter value for each frame
        frame_counter_flag = []
        speech_on = False
        speech_flag_true_count = 0
        speech_flag_false_count = 0
        speech_flag_final = []

        for i, frame_bounds in enumerate(frame_chunks):

            frame_start = frame_bounds[0]
            frame_end = frame_bounds[1]

            # marks if 30 frames have been sampled
            if i >= 30:
                thirty_frame_mark = True

            frame = abs_samples[frame_start:frame_end]

          
           
    
            #compute frame energy
            frame_energy = energy(frame)
            
            freq_domain_real, freq_domain_imag = real_imaginary_freq_domain(frame)
            freq_magnitudes = get_freq_domain_magnitudes(freq_domain_real, freq_domain_imag)
            dominant_freq = get_dominant_freq(freq_domain_real, freq_domain_imag,sampling_frequency)
           
            frame_SFM = get_sfm(freq_magnitudes)
            xPoints.append(i)
            

            #now, append these attributes to the frame attribute arrays created previously
            frame_energies.append(frame_energy)
            frame_max_frequencies.append(dominant_freq)
            frame_SFMs.append(frame_SFM)

            #the first 30 frames are used to set min-energy, min-frequency and min-SFM
            if not thirty_frame_mark and not i:
                min_energy = frame_energy
                min_dominant_freq = dominant_freq
                min_sfm = frame_SFM
    	        
            elif not thirty_frame_mark:
                min_energy = min(min_energy, frame_energy)
                min_dominant_freq = min(dominant_freq, min_dominant_freq)
                min_sfm = min(frame_SFM, min_sfm)

            #once we compute the min values, we compute the thresholds for each of the frame attributes
            energy_thresh = energy_prim_thresh * log10(min_energy)
            dominant_freq_thresh = freq_prim_thresh
            sfm_thresh = sfm_prim_thresh

            counter = 0
            energy_counter = 0
            dom_freq_counter = 0
            sfm_thresh_counter = 0

            #print frame_energy
            #print min_energy
            #print energy_thresh
            frame_counter_flag.append(0)

            if (frame_energy - min_energy) > energy_thresh:
                counter += 1
                energy_counter += 1
                frame_counter_flag[i] += 1
            if (dominant_freq - min_dominant_freq) > dominant_freq_thresh:
                counter += 1
                dom_freq_counter += 1
                frame_counter_flag[i] += 1
            if ( frame_SFM  - min_sfm) > sfm_thresh:
                counter += 1
                sfm_thresh_counter += 1
                frame_counter_flag[i] += 1

            energy_freq_list = [frame_energy,min_energy,energy_thresh,dominant_freq,min_dominant_freq,dominant_freq_thresh,frame_SFM, min_sfm,sfm_thresh]   
            sfm_list = [frame_SFM, min_sfm,sfm_thresh]
            counter_list = [counter,energy_counter,dom_freq_counter,sfm_thresh_counter]
            #y1Points.append(min_dominant_freq)
         
            # y2Points.append(energy_thresh)
            #print energy_freq_list
            #print counter_list
       
            if counter > 1:     #this means that the current frame is not silence.
                frame_voiced.append(1)
                speech_flag_true_count += 1
                speech_flag_false_count = 0
                #print frame_start
                #print energy_freq_list
                
                
                #break
            else:
                frame_voiced.append(0)
                speech_flag_false_count += 1
                speech_flag_true_count = 0
                #calculate new min energy based on average energy
                min_energy = ((frame_voiced.count(0) * min_energy) + frame_energy)/(frame_voiced.count(0) + 1)
               
            
            if speech_flag_true_count >= 5:
                speech_flag_final.append(1)
            elif speech_flag_false_count >=  10 :
                speech_flag_final.append(0)     
            elif i > 0:
                #maintain previous value if no conditions are met
                speech_flag_final.append(speech_flag_final[i-1]) 
            else:
                #start with a zero value
                speech_flag_final.append(0)      
            

            #now update the energy threshold
            energy_thresh = energy_prim_thresh * log10(min_energy)

        #close the input file    
        in_file.close()
        #pyplot.plot(xPoints,y1Points)
        #pyplot.show()

        return (abs_samples,frame_chunks,speech_flag_final,ampXPoints,sampling_frequency)



    
if __name__ == "__main__":

    #a, b = VAD.moattar_homayounpour('analysis.wav', 0, 0)
    print 