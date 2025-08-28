Learning project for running a local real time animal classifier on a Raspberry Pi 5 based on the Perch V2 Model

## Steps to use
1. Create a new virtual enviornment and clone the repo
2. Install the requirements with pip install -r requirements.txt
3. run the test.py script to ensure that everything set up correctly
4. Run the process.py script with python process.py /soundclip/directory
5. Results are published in a csv file and some stats on processing times are output to a text file

## Notes for use
1. Perch expects sound files to be formatted as 5second audio clips sampled at 32kHz
2. by default the predictions simply output an ID number, this needs to be referenced against their labels file. This file can be downloaded from the model page directly.
3. Very specific versions of tensorflow, tensorflow hub, and tf-keras are required, follow the requirements doc

## Items to be added
I have a realtime processing loop that I'm working on. Once it is cleaned up I will provide the files needed to:
1. Accept an rtsp stream and automatically save it into the file format that Perch wants
2. Process these clips in real time outputting the results to a local database
3. A secondary process that takes the results, applies scientific and common names to predictions, combines sconsecutive files with matching predictions and then moves these audio clips to a long term storage
4. A simple process to auto purge sound clips over a specified age

My current prefered tools for reviewing and displaying results are to push all detections to an influx database and move sound clips to a local NAS folder. Then I can use influx or grafana to build visualizations based on the detection results. But the results can be handled any way you wish. 





This project uses the [Perch V2 bird-vocalization model](https://www.kaggle.com/models/google/bird-vocalization-classifier/tensorFlow2/perch_v2_cpu) by Google (Apache-2.0).
The model is not redistributed here; it is downloaded at runtime from Kaggle/TF-Hub.
