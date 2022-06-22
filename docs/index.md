# Documentation

The toolbox aims at predicting tension from musical files. The tension prediction requires several steps, beginning with loading the audio and cutting off silence from the files. The next step involves extracting loudness, tempo, onset frequency, pitch height, and dissonance from the audio files. These features are then, in a final step, used to predict the perceived tension. An additional optional step includes sonifying some of the features to evaluate the extraction performance for the specific piece at hand.

The tension extraction relies on the tension model developed by Farbood and Upham (https://www.frontiersin.org/articles/10.3389/fpsyg.2013.00998/full). 

Please note that the toolbox was developed to work with .wav files. Consider transforming your music files to .wav in order to use the functions. 

### 1. Loading Audio & Basics

#### audio_read_trim(file_name, path, sr = 44100):

Loads the audio at your desired sampling rate (default is 44.1 kHz). Additionally, the function trims any silence from the beginning and the end of the audio
and saves a trimmed version of your audio at the path provided. 

file_name = File name of your piece (without adding .wav)
path = absolute or relative path to your .wav


### 2. Feature extraction

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
seems to work accurately or not and make adequate adjustments. 

#### [loudness, t_loudness] = extract_loudness(y, sr):

Estimates the loudness by calculating the root-mean-square for the smoothed audio. Returns the loudness estimate and the time points in seconds. 

#### pitch_df = pitch_extraction(audio_fpath,sr, category = ["voice", "polyphonic", "solo"], melody_lower = 'C2', melody_higher = 'C6'):

Estimates the pitch height in the audio. The toolbox implements different pitch estimation methods. 
For solo music, it relies on probabilistic YIN (https://librosa.org/doc/main/generated/librosa.pyin.html). For polyphonic music, the toolbox uses 
deep salience representations for f0 estimation (https://github.com/rabitt/ismir2017-deepsalience). For vocal music, the toolbox first seperates the 
voiced melody from the background using spleeter (https://github.com/deezer/spleeter) and then uses pYIN for the melody and deep salience representations 
for the accompainment. Returns a dataframe with time points as well as pitch estimates for all lines.

For solo and vocal music, the pitch estimation will be improved by providing estimates of the lowest and the highest notes in the melody. The estimates will not be used for polyphonic pitch estimation. 


#### [dissonance, t_dissonance] = dissonance_extraction(pitch_df, sr):

Estimates the dissonance at each time point by using the pitch estimated by the pitch extraction. Dissonance is defined as the maximum pairwise dissonance 
computed by dissonant.py (https://pypi.org/project/dissonant/). 


### 3. (Optional) Checking feature extraction by sonification

The toolbox includes functions to sonify the estimated pitches as well as the beats and the onsets to evaluate the feature extraction by ear. 

#### t_eval = tempo_evaluation(y,sr, start_bpm = 80):

Returns the original piece with the extracted beats overlayed as clicks. 
To receive the same results as in the feature extraction, the same starting value as used for the tempo extraction should be used. 

#### onset_eval = onset_evaluation(onset_env, y, sr):

Returns the piece with the extracted onsets overlayed as clicks. The onset envelope should be the envelope returned by the onset frequency extraction function.

#### pitch_eval = evaluate_pitch(pitches, times, sr):

Pitch sonification for the melody line if using vocal music. Returns the sonified pitch contour estimated for the vocal melody. Only applicable if category = "voice" in the pitch extraction. 

#### pitch_eval, pitch_lists = evaluate_polyphonic_pitch(pitch_df, sr):

Pitch sonification for polyphonic pieces. The input should be the dataframe returned by the pitch extraction function. Returns the sonified pitches extracted by the deep salience representations.

If you wish to save the audios, this can be achieved by: 

audio = ipd.Audio(pitch_eval, rate=sr)
audio = AudioSegment(audio.data, frame_rate=sr, sample_width=2, channels=1)
audio.export("polyphonic_pitch.wav", format="wav", bitrate="64k")


### 4. Tension prediction

The tension prediction involves several steps: 

- Standardizing and merging all features 
- (Optional) Plotting all features over time
- Smoothing the features to enable an adequate slope detection
- Resampling the features: The toolbox includes methodes to resample at 10 Hz or at the beats (recommended: resampling at the beats)
- Tension prediction: The toolbox implements two different versions of the tension prediction that rely on the same basic model. One method uses different attentional windows for each feature. The other method applies different weights to every feature. See the publication for more details. We recommend using different attentional windows as this methods yielded the best results for our investigation and additionally, it seems to display a cognitively plausible method. 
- (Optional) Plotting the predicted tension and the feature graphs













