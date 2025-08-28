Learning project for running a local real time animal classifier on a Raspberry Pi 5 based on the Perch V2 Model

## Steps to Setup and Test Environment
1. Create a new virtual environment and clone the repo
2. Install the requirements with pip install -r requirements.txt
3. run the test.py script to ensure that everything set up correctly

## Using the batch processor
the process.py file will process all files in a specified directory and return predictions and processing stats
1. Run the process.py script with python process.py /soundclip/directory
2. Results are published in a csv file and some stats on processing times are output to a text file

### Notes for use
1. Perch expects sound files to be formatted as 5second audio clips sampled at 32kHz
2. by default the predictions simply output an ID number, this needs to be referenced against their labels file. This file can be downloaded from the model page directly.

## Setting up automatic rtsp processing
I've included files that will allow for automatically capturing rtsp streams and saving them into files formatted for perch to use  
I've also included files that will setup timers to automatically purge old audio files so that your drive doesn't fill. By default the timer runs every 4 hours and deletes anything older than 3 hours.   
1. Review the setup-rtsp-processors.sh file to make sure you agree with that it will do. This script sets up services to process the rtsp streams and auto purge old files
2. make the setup-rtsp-processors.sh executable with chmod +x
3. Run the setup-rtsp-processors.sh script
4. The script will ask you for a short name for each script, the rtsp stream url, and the directory you want the clips to store into


## Items to be added
I have a realtime processing loop that I'm working on. Once it is cleaned up I will provide the files needed to:
1. ~Accept an rtsp stream and automatically save it into the file format that Perch wants~
2. Process these clips in real time outputting the results to a local database
3. A secondary process that takes the results, applies scientific and common names to predictions, combines consecutive files with matching predictions and then moves these audio clips to a long term storage
4. A simple process to auto purge sound clips over a specified age

My current preferred tools for reviewing and displaying results are to push all detections to an influx database and move sound clips to a local NAS folder. Then I can use influx or grafana to build visualizations based on the detection results. But the results can be handled any way you wish. 





This project uses the [Perch V2 bird-vocalization model](https://www.kaggle.com/models/google/bird-vocalization-classifier/tensorFlow2/perch_v2_cpu) by Google (Apache-2.0).
The model is not redistributed here; it is downloaded at runtime from Kaggle/TF-Hub.
