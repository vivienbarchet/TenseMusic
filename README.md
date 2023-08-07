# An Automatic Prediction Model for Musical Tension (TenseMusic)

TenseMusic is a python-based model automatically predicting musical tension from musical audio files. 

The tension prediction relies on the trend salience model developed by Farbood (2012). We enhanced this model by introducing automatic feature extraction methods, adjusting the tension prediction process, and optimizing the model on a set of 38 western classical pieces. 

Details about the automization process and the model optimization can be found here: https://psyarxiv.com/xck3w/

This repository contains: 
- Notebooks defining our custom functions for the tension prediction and the feature extraction 
- Two example notebooks explaining the feature extraction and the tension prediction 
- A documentation of the functions we use for the tension extraction (docs/index.md)

- All music files we used during the model optimization 
- Our behavioral data (raw and sampled at 50 Hz as well as filtered and sampled at 10 Hz)


Citation: 

Barchet, A. V., Rimmele, J. M., & Pelofi, C. (2022, November 25). TenseMusic: An automatic prediction model for musical tension. https://doi.org/10.31234/osf.io/xck3w
