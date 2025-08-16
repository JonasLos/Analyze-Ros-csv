This code was created for vehicle rosbag recording analysis, so the displayed data is in terms of a vehicle driving on a road. Note: Currently, only odometry and imu topics are supported. Other topics may still display run time, but no other information, unless the data names are the same as in these topics.
If you are wondering how this code works, there are discriptions both in the code itself and in the powerpoint presentation that is included. 
There are a couple of things to keep in mind when using this script: 
1. The code assumes that the time information is in gps time (nanoseconds).
2. The code assumes that the data columns will have numerical information, if there are non-numerical strings other than the title, it will crash.
3. For vibration analysis, there are default filters, but those can be changed easily to display more useful information. Just look for the high/low cutoff in the code, and change the numbers. (The numbers are assumed to be in Hz)
4. For determining acceleration events, the default threshold is set to 1.5 m/s/s, this can also be easily changed within the code.
5. Determining possible road type from vibration is not completely accurate. More data would be needed to teach the code what comfort index correlates to what possible road type.
         Note: To have more accurate road type determination, speed would be needed to be taken into account, but, in the data I used, speed is not included in the same topic as accelerations, so it would be difficult to correlate them.


To use this code, go to the correct directory in your terminal, then input:
   
`python3 read_csv.py file_name.csv`


I have also included an odometry and an imu csv file for testing purposes, and to show the type of information the script can anazlyze.
