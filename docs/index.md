# Documentation

The toolbox aims at predicting tension from musical files. The tension prediction requires several steps, beginning with loading the audio and cutting off silence from the files. The next step involves extracting loudness, tempo, onset frequency, pitch height, and dissonance from the audio files. These features are then, in a final step, used to predict the perceived tension. An additional optional step includes sonifying some of the features to evaluate the extraction performance for the specific piece at hand.

The tension extraction relies on the tension model developed by Farbood (2012, https://online.ucpress.edu/mp/article/29/4/387/46442/A-Parametric-Temporal-Model-of-Musical-Tension)

Please note that the toolbox was developed to work with .wav files. Consider transforming your music files to .wav in order to use the functions. 

## 1. Loading Audio & Basics

#### y,sr,trimmed_audio_path = music_loading(file_name, path, sr = 44100):

Loads the audio at your desired sampling rate (default is 44.1 kHz). Additionally, the function trims any silence from the beginning and the end of the audio
and saves a trimmed version of your audio at the path provided. 

file_name = File name of your piece (without adding .wav)

path = absolute or relative path to your .wav

Returns the trimmed audio file, the sampling rate, and the path to the trimmed audio file for later use during feature extraction.


## 2. Feature extraction

#### [tempo, t_tempo] = tempo_extraction(y,sr, tempo_guess = 80):

Dynamically estimates the beat tempo for the piece and plots the tempo over time. Returns the tempo estimate at every time point and a list of time points in seconds.
If you have an idea of what the approximate tempo of your piece should be, you can submit a tempo guess (in bpm) that will be used as the starting value for the 
tempo estimation. Otherwise, the start value will be 80 bpm. 

#### [onset_env, onset_freq, t_onset] = onset_frequency(y,sr):

Estimates the onset density at each given time point and plots the onset frequency over time. 
Returns the onset envelope (used again later), the estimated onset frequencies and the time points in seconds. 

**Please note:** The function will return a warning message if there are no onsets detected in a time window longer than 
five seconds. This might happen if the piece involves strong changes in character or instrumentation. 
If the window without detected onsets lies in the end or the beginning of the piece, the toolbox involves a procedure to estimate onsets for the two 
windows seperately and clipping the parts together afterwards. If the window lies in the middle of the piece, you have to judge if the onset estimation
seems to work accurately or not and make adequate adjustments. Consider using the onset sonification function to evaluate the onset detection.

#### [loudness, t_loudness] = extract_loudness(outpath, file_name):

Estimating the loudness using the Zwicker model for temporally variable sounds implemented in the python library MoSQITo. 

#### pitch_df, pitch_score, times = pitch_extraction(outpath, file_name,sr):

Estimates the pitch height in the audio. The toolbox uses 
deep salience representations for f0 estimation (https://github.com/rabitt/ismir2017-deepsalience). Returns a dataframe with time points as well as pitch estimates for all lines. Additionally, the pitch score as the aggregated mean of all pitches at each time point is returned. 


#### [tensile, t_tonal] = tonal_tension_extraction(file_name):

Estimates tonal tension using the model developed by Herremans and Chew (2016) based on the spiral array theory. The model is implemented in the python library midi-miner. The midi input required for the estimation of tonal tension is created using the python package basic-pitch. Tonal tension is estimated as the tensile strain as defined by Herremans and Chew (2016). 

#### [roughness, t_roughness] = roughness_extraction(outpath, file_name):

Estimates roughness using the algorithm developed by Daniel and Weber (1997) implemented in MoSQITo. 

## 3. (Optional) Checking feature extraction by sonification

The toolbox includes functions to sonify the estimated pitches as well as the beats and the onsets to evaluate the feature extraction by ear. 

#### t_eval = tempo_evaluation(y,sr, start_bpm = 80):

Returns the original piece with the extracted beats overlayed as clicks. 
To receive the same results as in the feature extraction, the same starting value as used for the tempo extraction should be used. 

#### onset_eval = onset_evaluation(onset_env, y, sr):

Returns the piece with the extracted onsets overlayed as clicks. The onset envelope should be the envelope returned by the onset frequency extraction function.

#### pitch_eval, pitch_lists = evaluate_polyphonic_pitch(pitch_df, sr):

Pitch sonification for polyphonic pieces. The input should be the dataframe returned by the pitch extraction function. Returns the sonified pitches extracted by the deep salience representations.

If you wish to save the audios, this can be achieved by: 

audio = ipd.Audio(pitch_eval, rate=sr)

audio = AudioSegment(audio.data, frame_rate=sr, sample_width=2, channels=1)

audio.export("polyphonic_pitch.wav", format="wav", bitrate="64k")


## 4. Tension prediction

The tension prediction involves several steps: 


### Standardizing and merging all features 

#### df_all_features, df_plot = feature_extraction(outpath, y,sr,file_name, start_bpm = 80):

This function extracts all features applying the functions explained above. Additionally, it merges all features at the desired sampling rate (as all features are extracted at different time scales). The pitch lines are combined into one aggregated pitch score. 

The function returns a dataframe containing all z-standardized features and time stamps. 



### Smoothing the features to enable an adequate slope detection

#### df_features, features_unsmoothed = feature_smoothing_resampling(df_all_features):

This function smoothes the extracted features using a running mean filter and resamples them at 10 Hz. The function returns the smoothed and the unsmoothed features sampled at 10 Hz. 


### Tension prediction: 
The toolbox implements two different versions of the tension prediction that rely on the same basic model. One method uses different attentional windows for each feature. The other method applies different weights to every feature. See the publication for more details. The toolbox uses our optimized weights and window durations. 

#### tension_with_time, feature_slopes = tension_prediction(df_features, model_variant = ['weight', 'time_scale'])

This function predicts tension from the musical features using the trend salience model (Farbood, 2012). 
The model can be configured to allow for different feature window sizes or to use a fixed window size across all features. 

###### Returns: 
tension_with_time: dataframe with time and the tension prediction sampled at 10 Hz 

feature_slopes: The slopes for all features estimated using our optimized window sizes. 



















