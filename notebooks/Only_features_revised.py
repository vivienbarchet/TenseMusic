#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from __future__ import print_function

import librosa.display
import librosa
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import Audio
from matplotlib.lines import Line2D
import pandas as pd


import dissonant
import os
import scipy
import spleeter
import numpy as np
import mir_eval
import crepe
import IPython.display as ipd
import os
import soundfile
from scipy.ndimage.filters import uniform_filter1d
from scipy.signal import savgol_filter


from scipy import signal
import scipy.signal
from predict_on_audio1 import compute_hcqt,compute_output


from basic_pitch.inference import predict_and_save
import tensorflow as tf
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
import math
import pickle, os
import matplotlib
import pretty_midi
import json
from scipy import stats
import glob


from mosqito.utils import load
from mosqito.sq_metrics import *

from mosqito import COLORS



# In[ ]:

def midi_creation(path):
    path = path + "*"
    files = [file for file in glob.glob(path)]

    predict_and_save(files, "midi/", True, True, False, False)

    print('midis were created')



def tempo_extraction(y, sr, start_bpm = 80):
    print("Estimating tempo...")
    #Constant Q-spectrogram
    C = np.abs(librosa.cqt(y=y, sr=sr))
    o_env3 = librosa.onset.onset_strength(sr=sr,S = librosa.amplitude_to_db(C, ref=np.max))
    
    times3 = librosa.frames_to_time(np.arange(len(o_env3)), sr=sr)



    # Obtain dynamic tempo
    dtempo3 = librosa.beat.tempo(y = y, sr = sr, onset_envelope = o_env3, aggregate = None, start_bpm = start_bpm)
    #t = librosa.frames_to_time(np.arange(len(dtempo3)))
    

    
    return dtempo3, times3



# In[ ]:
def noteToFreq(note):
    a = 440 #frequency of A (coomon value is 440Hz)
    return (a / 32) * (2 ** ((note - 9) / 12))

def tempo_evaluation(y,sr, start_bpm = 80):
    times, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=start_bpm)
    y_beats = librosa.clicks(frames=beats, sr=sr, length=len(y))
    aud = y + y_beats
    
    display(ipd.Audio(y+ y_beats, rate = sr))   
    return aud


# In[ ]:


def onset_freq_detection(y,sr):
    o_env = librosa.onset.onset_strength(y = y, sr=sr)

    onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    #Onset frequency = maximum event duration - current event duration
    diffs = np.diff(onset_times)

    max_diff = np.max(diffs)
    max_index = np.where(diffs == max_diff)

    # diff between max event and all events
    onset_freq2 = max_diff - diffs

    # remove first instance for plotting
    onset_times_rm2 = onset_times[1:,]


    #Smooth the signal
    wind = int((len(onset_freq2)/max(onset_times_rm2))*2)

    onset_density_smooth = uniform_filter1d(onset_freq2, size =wind) 


    return o_env, onset_frames, onset_density_smooth, onset_times_rm2


# In[ ]:


def onset_frequency(y,sr):
    print("Estimating Onset frequency...")
    o_env = librosa.onset.onset_strength(y = y, sr=sr)

    onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    
    ##Buildung in the adjustment for pieces with strong character changes leading to no onset detection by librosa
    onset_times_with_end = np.append(onset_frames, len(y)/512)
    onset_times_start_end = np.insert(onset_times_with_end, 0, 0, axis=0)
    
    onset_diffs_2 = np.diff(onset_times_start_end)
    
    if max(onset_diffs_2)>(5*sr)/512:
        print("The audio includes large parts > 5s in which no onsets are detected.")

        if (max(onset_diffs_2) == onset_diffs_2[-1]):
            print("The part without onset detections is in the end. Will now split the audio for onset detection.")

            sep = int(max(onset_frames)*512)
            y_1 = y[:sep+1]
            y_2 = y[sep+1:]

            o_env_1, onset_frames_1, density1, times_1 = onset_freq_detection(y_1, sr)
            o_env_2, onset_frames_2, density2, times_2 = onset_freq_detection(y_2, sr)

            onset_frames_1 = onset_frames_1[1:]
            onset_frames_2 = onset_frames_2[1:]
            onset_frames_2 = onset_frames_2 + max(onset_frames_1)
            onset_frames = np.append(onset_frames_1, onset_frames_2)
            
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)

            onset_envelope = np.append(o_env_1, o_env_2)
            onset_density_smooth = np.append(density1, density2)
            
        elif (max(onset_diffs_2) == onset_diffs_2[0]):
            
            print("The part without onset detections is in the beginning. Will now split the audio for onset detection.")
            
            sep = int(min(onset_frames)*512)
            y_1 = y[:sep+1]
            y_2 = y[sep+1:]

            o_env_1, onset_frames_1, density1, times_1 = onset_freq_detection(y_1, sr)
            o_env_2, onset_frames_2, density2, times_2 = onset_freq_detection(y_2, sr)

            onset_frames_1 = onset_frames_1[1:]
            onset_frames_2 = onset_frames_2[1:]
            onset_frames_2 = onset_frames_2 + max(onset_frames_1)
            onset_frames = np.append(onset_frames_1, onset_frames_2)
            
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)

            onset_envelope = np.append(o_env_1, o_env_2)
            onset_density_smooth = np.append(density1, density2)
            
            
        else:
            print("The part without onset detections is in the middle. Will calculate onset frequency normally but might not be accurate.")
            onset_envelope, onset_frames, onset_density_smooth, onset_times = onset_freq_detection(y,sr)

    else:
        onset_envelope, onset_frames, onset_density_smooth, onset_times = onset_freq_detection(y,sr)
        
        
    
    
    return onset_envelope, onset_density_smooth, onset_times


# In[ ]:


def onset_evaluation(onset_envelope,y,sr):
    onset_times = librosa.onset.onset_detect(onset_envelope=onset_envelope, sr=sr, units = "time")
    y_onsets = librosa.clicks(times=onset_times, sr=sr, length=len(y))
    aud = y + y_onsets
    
    display(ipd.Audio(y+ y_onsets, rate = sr))   
    return aud


# In[ ]:


# Calculate loudness
def extract_loudness(outpath, file_name):
    print("Estimating loudness...")
    
    sig, fs = load(outpath + file_name + "_trim"+ ".wav")

    loudness, N_spec, bark_axis, t = loudness_zwtv(sig, fs, field_type="free")

    return loudness,t




# In[ ]:


def roughness_extraction(outpath, file_name):
    print("Estimating roughness...")
    
    sig, fs = load(outpath + file_name + "_trim"+ ".wav")

    roughness, r_spec, bark, time = roughness_dw(sig, fs, overlap=0)
    

    return roughness,time



def pitch_estimation(outpath, file_name,sr):
    print("Estimating Pitch...")
    path = outpath + file_name + "_trim.wav"

    print('Estimating polyphone pitch using Deep Salience')
    task = "multif0"
    output_format = "multif0"
    threshold = 0.3
    use_neg = False
    sr = 44100

    # this is slow for long audio files
    print("Computing HCQT...")
    hcqt, freq_grid, time_grid = compute_hcqt(path)

    times,freqs = compute_output(
        hcqt, time_grid, freq_grid, task, output_format,
        threshold, use_neg)

    freqs_df = pd.DataFrame(freqs)

    colnames_new = []
    ncol = freqs_df.shape[1]

    for col in range(1,ncol+1):
        colname = "line"+str(col)
        colnames_new.append(colname)

    freqs_df.columns = colnames_new

    times_df = pd.DataFrame(times, columns = ["time"])


    #Fill smaller gaps with previous pitches
    freqs_df = freqs_df.fillna(method='ffill', limit = 100)
    #And larger gaps with zeros (breaks in the signal)
    freqs_df = freqs_df.fillna(0)
    
    pitch_score = []
    
    for l in freqs_df.iterrows():
        ps = []
        for v in l[1]:
            if v != 0:
                ps.append(v)
                
        p_score = np.nanmean(ps)
        pitch_score.append(p_score)
        
    freqs_df['mean'] = pitch_score

    pitches_df = pd.merge(times_df, freqs_df, left_index = True, right_index = True)


    return pitches_df, pitch_score, times


def evaluate_polyphonic_pitch(pitch_df, sr):
    #Sonify the melody pitches to check 
    sonified_pitches = []
    for col in pitch_df.columns:
        if col != "time":
            new_df = pitch_df.fillna(0)
            son = mir_eval.sonify.pitch_contour(new_df.time,new_df[col], sr)
            sonified_pitches.append(son)
    
    
    for i,s in enumerate(sonified_pitches):
        if i == 0:
            all_aud = s
        else:
            all_aud = all_aud + s
            
    display(ipd.Audio(all_aud, rate = sr))
    return all_aud, sonified_pitches

# In[1]:

def tonal_tension_extraction(file_name):
    path = "./midi/" + file_name + "_trim" + "_basic_pitch.mid"
    

    os.system('python3 tension_calculation.py -f {0} -o tonal_tension/ -k True -w 1'.format(str(path)))
    

    file_tensile = "tonal_tension/" + file_name + "_trim" + "_basic_pitch.tensile"
    file_time = "tonal_tension/" + file_name + "_trim" + "_basic_pitch.time"


    tensile = pickle.load(open(file_tensile,'rb'))
    t_tonal = pickle.load(open(file_time,'rb'))

    return tensile, t_tonal


# In[ ]:


def feature_standardization(t_tempo, tempo,t_loudness, loudness, t_pitch,pitch, t_onset, onset_freq, t_roughness, roughness,t_tonal, tonal):
    
    #Tempo & Loudness
    df_tempo = pd.DataFrame(zip(t_tempo, tempo), columns = ['time', 'tempo'])
    df_tempo['time'] = pd.to_datetime(df_tempo['time'], unit='s', errors='coerce')

    df_loudness = pd.DataFrame(zip(t_loudness, loudness), columns = ['time', 'loudness'])
    df_loudness['time'] = pd.to_datetime(df_loudness['time'], unit='s', errors='coerce')

    tempo_loudness = pd.merge_asof(left=df_tempo,right=df_loudness,on = "time",direction='nearest')

    tempo_loudness['tempo_z'] = stats.zscore(tempo_loudness['tempo'])
    tempo_loudness['loudness_z'] = stats.zscore(tempo_loudness['loudness'])

    #Pitch 
    df_pitch = pd.DataFrame(zip(t_pitch, pitch), columns = ['time', 'pitch'])
    df_pitch['time'] = pd.to_datetime(df_pitch['time'], unit='s', errors='coerce')
    
    tempo_loudness_pitch = pd.merge_asof(left=tempo_loudness.iloc[:,[0,3,4]],right=df_pitch,on = "time",direction='nearest')
    tempo_loudness_pitch['pitch'] = tempo_loudness_pitch['pitch'].fillna(0)
    
    tempo_loudness_pitch['pitch_z'] = stats.zscore(tempo_loudness_pitch['pitch'])
    

    #Onset frequency
    df_onset_freq = pd.DataFrame(list(zip(t_onset, onset_freq)), columns = ["time", "onset_freq"])
    df_onset_freq['onset_freq_z'] = stats.zscore(df_onset_freq['onset_freq'])
    df_onset_freq['time'] = pd.to_datetime(df_onset_freq['time'], unit='s', errors='coerce')
    
    merge_onset = pd.merge_asof(left=tempo_loudness_pitch,right=df_onset_freq,on = "time",direction='nearest')

    
    ##Roughness 
    df_roughness = pd.DataFrame(zip(t_roughness, roughness), columns = ['time', 'roughness'])
    df_roughness['time'] = pd.to_datetime(df_roughness['time'], unit='s', errors='coerce')
    
    merge_roughness = pd.merge_asof(left=merge_onset,right=df_roughness,on = "time",direction='nearest')

    merge_roughness['roughness_z'] = stats.zscore(merge_roughness['roughness'])
    
    
    ##Tonal Tension
    df_tonal = pd.DataFrame(zip(t_tonal, tonal), columns = ['time', 'tonal'])
    df_tonal['time'] = pd.to_datetime(df_tonal['time'], unit='s', errors='coerce')
    
    merge_tonal = pd.merge_asof(left=merge_roughness,right=df_tonal,on = "time",direction='nearest')

    merge_tonal['tonal_z'] = stats.zscore(merge_tonal['tonal'])
    
    df_all_features = merge_tonal
    
   
    #Transforming back to seconds (for plotting and joining)
    df_all_features['time_dt'] = df_all_features['time']
    df_all_features['diff'] = df_all_features['time_dt'] - pd.to_datetime(0, unit='s')
    df_all_features['time'] = df_all_features['diff'].dt.total_seconds()
                
    df_all_features = df_all_features.drop(columns = ['diff', 'time_dt'])
    
    df_plot = df_all_features.fillna(method='ffill')
    

    return df_all_features, df_plot

