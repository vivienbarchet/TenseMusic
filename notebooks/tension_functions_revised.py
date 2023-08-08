#!/usr/bin/env python
# coding: utf-8

# In[23]:


from __future__ import print_function

import librosa.display
import librosa
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import Audio
from scipy.ndimage.filters import uniform_filter1d


import dissonant
import os
import scipy
import pandas as pd
pd.options.mode.chained_assignment = None

from scipy import stats
import spleeter

from pydub import AudioSegment
import soundfile
from scipy.signal import savgol_filter
from scipy import signal
import scipy.signal
from matplotlib.lines import Line2D
import seaborn as sns

# In[ ]:


import Only_features_revised     #defining our custom functions


# In[ ]:


def music_loading(file_name, inpath, outpath, sr = 44100):
    #Enter file name and (relative) path
    audio_fpath = inpath + file_name + '.wav'
    print(audio_fpath)

    # load audio file
    y, sr = librosa.load(audio_fpath, sr = 44100)

    ###Trimming should be done in the very beginning (cut out silent parts)
    y, index = librosa.effects.trim(y=y, frame_length=sr, top_db=60)

    trimmed_audio_path = outpath + file_name + "_trim" + '.wav'
    soundfile.write(trimmed_audio_path, y, sr)

    return y,sr, trimmed_audio_path


# In[9]:


def feature_extraction(outpath, y,sr,file_name, start_bpm = 80):
    #Features 

    #Tempo
    [tempo, t_tempo] = Only_features_revised.tempo_extraction(y,sr, start_bpm = start_bpm)

    #Onset
    [onset_env, onset_freq, t_onset] = Only_features_revised.onset_frequency(y,sr)

    #Loudness
    [loudness, t_loudness] = Only_features_revised.extract_loudness(outpath,file_name)

    #pitches
    [pitch_list, pitch, t_pitch] = Only_features_revised.pitch_estimation(outpath, file_name, sr)
    
    #Roughness
    [roughness, t_roughness] = Only_features_revised.roughness_extraction(outpath,file_name)
    
    #Tonal Tension
    [tonal_tension, t_tonal] = Only_features_revised.tonal_tension_extraction(file_name)
    
    
    df_all_features, df_plot = Only_features_revised.feature_standardization(t_tempo, tempo,t_loudness, loudness, t_pitch,pitch, t_onset, onset_freq, t_roughness, roughness,t_tonal, tonal_tension)

    return df_all_features, df_plot


# In[18]:


def feature_smoothing_resampling(df_all_features):
    
    ###Smoothing
    smooth_features = []
    for f in df_all_features.columns[1:]:
        feature = df_all_features[f].fillna(0)
        feature_smooth = uniform_filter1d(feature, size =int(len(df_all_features)/30)) 
        smooth_features.append(feature_smooth)

    dict_smooth = dict(zip(df_all_features.columns[1:], smooth_features))

    features_smooth = pd.DataFrame(dict_smooth)
    features_smooth['time'] = df_all_features['time']


    
    ###Resampling
    sr_features = len(features_smooth)/max(features_smooth['time'])

    df_features = features_smooth.iloc[::int(sr_features/10)]
    df_features = df_features.reset_index()

    features_unsmoothed = df_all_features.iloc[::int(sr_features/10)]
    features_unsmoothed = features_unsmoothed.reset_index()
    
    
    return df_features, features_unsmoothed


# In[13]:


def tension_prediction(df_features, model_variant = ['weight', 'time_scale']):
    prediction = []
    feature_cols = ['tempo_z', 'loudness_z', 'onset_freq_z','pitch_z','tonal_z', 'roughness_z']

    # get the exact sampling rate for our features: 
    sr_features = len(df_features)/max(df_features['time'])

    #Calculate the shift (0.25 s recommended)
    shift = int(0.25*sr_features)
    prevSlope = 0.5    

    feature_predictions = pd.DataFrame()


    ##Weighted Model
    if model_variant == 'weight':
        att = {'tempo_z': 3, 'loudness_z': 3, 'onset_freq_z': 3, 'roughness_z': 3, 'pitch_z': 3, 'tonal_z':3}
        mem = {'tempo_z': 3, 'loudness_z': 3, 'onset_freq_z': 3, 'roughness_z': 3, 'pitch_z': 3, 'tonal_z':3}
        weights = np.array([0.05,  0.49,  -0.02,  0.21,  0.07, 0.14 ])



    elif model_variant == "time_scale":
        att = {'tempo_z': 3, 'loudness_z': 3, 'onset_freq_z': 3, 'roughness_z': 3, 'pitch_z': 5, 'tonal_z':7}
        mem = {'tempo_z': 20, 'loudness_z': 3, 'onset_freq_z': 20, 'roughness_z': 4, 'pitch_z': 12, 'tonal_z':12}
        weights = np.array([-0.18,  0.47,  0.00,  0.10,  0.20, 0.07])


    windows = [att, mem]


    for f in df_features[feature_cols]:

        ##Window Durations
        attention_window = windows[0][f]
        memory_window = windows[1][f]

        n_samp_m = int(memory_window*round(sr_features))
        n_samp_a = int(attention_window*round(sr_features))

        for i in range(0,len(df_features), shift):
            slopes = []
            #get start and end points for attentional window
            start_a = i
            end_a = n_samp_a + i
            x_a = list(range(0,n_samp_a))

            #End: attentional window is shorter
            if (len(df_features) - end_a) < 0:
                end_a = len(df_features) 
                x_a = range(0,(end_a - start_a))

            #and for the memory window (if there is one)
            if memory_window > 0:
                end_m = start_a - 1
                start_m = end_m - n_samp_m +1
                if start_m < 0:
                    start_m = 0

                curr_mem = end_m - start_m +1

                x_m = list(range(0,curr_mem))

                if i > 2: # need at least 2 points for memory window
                    memoryWindowActive = True
                else:
                    memoryWindowActive = False

            #get the current attentional window
            curr_win = df_features.iloc[start_a:end_a]



            if len(curr_win) > 1:
                slope = np.polyfit(x_a, curr_win[f], 1)
                slope = slope[0]

            if memory_window > 0 and memoryWindowActive == True:
                curr_win_m = prediction[start_m:end_m+1]
                slope_m = np.polyfit(x_m,curr_win_m,1)
                prevSlope = slope_m[0]



            epsilon = .0001;
            decay = .001;

            if (memory_window > 0) and memoryWindowActive:

                # if both attentional and memory windows are in the same
                # direction, negative or positive, strengthen the attentional
                # window slope in the current direction
                if ((slope > 0) and (prevSlope > 0)) or ((slope < 0) and (prevSlope < 0)):
                    # 5 = recommendation
                    slope = slope * 5


            cur_slope = slope*np.array(x_a)

            if start_a < (len(df_features)-1):
                if start_a == 0:
                    prediction = cur_slope

                else:
                    start = prediction[0:start_a]
                    startval = prediction[start_a]
                    middle = np.array(cur_slope[0:(len(prediction)-(start_a))]+prediction[(start_a):])/2

                    if middle.size!=0:
                        offset1 = startval - middle[0]
                        middle = middle + offset1

                    endChunk = cur_slope[len(middle)+1:]

                    if middle.size!=0 & endChunk.size!=0:
                        offset2 = middle[-1] - endChunk[0]
                        endChunk = endChunk + offset2

                    if endChunk.size!=0:
                        prediction = list(start) + list(middle) + list(endChunk)
                    else:
                        prediction = list(start) + list(middle)

        prediction = stats.zscore(prediction)

        feature_predictions[f] = prediction


    ###Multiply with weights and sum up 
    feature_slopes = pd.DataFrame(feature_predictions, columns = feature_cols)
    pred = feature_slopes*weights
    tension_prediction_final = pred.sum(axis = 1)
    tension_with_time = pd.DataFrame(zip(df_features['time'], tension_prediction_final), 
                                    columns = ['time', 'tension_prediction'])

    return tension_with_time, feature_slopes
      


# In[22]:


def plot_tension_and_features_10Hz(tension_with_time, feature_slopes):
    plt.figure(figsize = [20,8])


    new_pal = [sns.color_palette('colorblind')[3], sns.color_palette('colorblind')[1], 
          sns.color_palette('colorblind')[0], sns.color_palette('colorblind')[5], 
          sns.color_palette('colorblind')[2], sns.color_palette('colorblind')[4]]

    custom_lines = []
    count = 0
    
    feature_list = ['Loudness', 'Pitch', 'Tonal Tension', 'Roughness','Onset Frequency', 'Tempo', 'Tension Prediction']
    
    feature_slopes = feature_slopes[['loudness_z', 'pitch_z', 'tonal_z', 'roughness_z','onset_freq_z', 'tempo_z']]
    feature_slopes['time'] = tension_with_time['time'].to_numpy()


    for f in feature_slopes.columns[:-1]:
        plt.plot(feature_slopes.time, feature_slopes[f], color = new_pal[count])
        
        custom_lines.append(Line2D([0], [0], color = new_pal[count], lw = 3))
        count = count+1
        

    plt.plot(tension_with_time['time'], tension_with_time['tension_prediction'], color = "black", 
             linewidth = 4, alpha = 1)
    
    custom_lines.append(Line2D([0], [0], color = 'black', lw = 4))

    


    plt.legend(custom_lines, feature_list , 
               loc='right', bbox_to_anchor=(1.2, 0.37), fancybox=True, facecolor='white', framealpha=1, 
              edgecolor = "black", fontsize = 20)

    plt.title("All Features and the Tension Prediction over Time", fontsize = 30)
    plt.ylabel("Z-Scores", fontsize = 20)
    plt.xlabel("Time (s)", fontsize = 20)


# In[3]:





# In[ ]:




