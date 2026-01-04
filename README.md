# An Automatic Prediction Model for Musical Tension (TenseMusic)

TenseMusic is a python-based model automatically predicting musical tension from musical audio files. 

The tension prediction relies on the trend salience model developed by Farbood (2012). We enhanced this model by introducing automatic feature extraction methods, adjusting the tension prediction process, and optimizing the model on a set of 38 western classical pieces. 

Details about the automization process and the model optimization can be found here: https://doi.org/10.1371/journal.pone.0296385

This repository contains: 
- Notebooks defining our custom functions for the tension prediction and the feature extraction 
- Two example notebooks explaining the feature extraction and the tension prediction 
- A documentation of the functions we use for the tension extraction (docs/index.md)

- All music files we used during the model optimization 
- Our behavioral data (raw and sampled at 50 Hz as well as filtered and sampled at 10 Hz)


Citation: 

Barchet AV, Rimmele JM, Pelofi C (2024) TenseMusic: An automatic prediction model for musical tension. PLOS ONE 19(1): e0296385. https://doi.org/10.1371/journal.pone.0296385
