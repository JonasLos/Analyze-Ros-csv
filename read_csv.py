import math
import csv
import decimal
import sys
from decimal import Decimal
from colorama import Fore, Style
import endaq
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np 
import scipy
from endaq import calc
from endaq.calc import filters as endaq_filters
from endaq.plot import octave_spectrogram, multi_file_plot_attributes, octave_psd_bar_plot
from endaq.plot.utilities import set_theme
import inspect
import endaq.calc.filters
from plotly.subplots import make_subplots

def read_csv(file_path):
    
    ##Checks to ensure the file is a csv file##
    if not file_path.lower().endswith(".csv"):
        print(Fore.RED+"ERROR-------FILE TYPE NOT SUPPORTED, USE A .csv FILE")
        return
    
    found = False
    display = 1
    contains_posx = False
    contains_posy = False
    containst = False
    contains_posz = False
    contains_twistx = False
    contains_accelx = False
    contains_accely = False
    contains_accelz = False
    time_error = True
    x_position = []
    time = []
    y_position = []
    z_position = []
    forward_speed = []
    x_accel = []
    y_accel = []
    z_accel = []

    ##Takes the different topics in the csv and creates lists of the data##
    with open(file_path, newline='') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        if 'field.pose.pose.position.x' in fieldnames:
            contains_posx = True
            found = True
        if 'field.pose.pose.position.y' in fieldnames:
             contains_posy = True
             found = True
        if '%time' in fieldnames:
            containst = True
            found = True
        if 'field.pose.pose.position.z' in fieldnames:
            contains_posz = True
            found = True
        if 'field.twist.twist.linear.x' in fieldnames:
            contains_twistx = True
            found = True
        if 'field.linear_acceleration.x' in fieldnames:
            contains_accelx = True
            found = True
        if 'field.linear_acceleration.y' in fieldnames:
            contains_accely = True
            found = True
        if 'field.linear_acceleration.z' in fieldnames:
            contains_accelz = True
            found = True
        for row in reader:
            if contains_posx:
                  x_position.append(float(row['field.pose.pose.position.x']))
            if contains_posy:
                 y_position.append(float(row['field.pose.pose.position.y']))
            if containst:
                time.append(Decimal(row['%time']))
            if contains_posz:
                z_position.append(float(row['field.pose.pose.position.z']))
            if contains_twistx:
                forward_speed.append(float(row['field.twist.twist.linear.x']))
            if contains_accelx:
                x_accel.append(float(row['field.linear_acceleration.x']))
            if contains_accely:
                y_accel.append(float(row['field.linear_acceleration.y']))
            if contains_accelz:
                z_accel.append(float(row['field.linear_acceleration.z']))
  
    ##Returns if there are no applicable topics##
        if found == False:
             print(Fore.RED + "ERROR ------- FILE DOES NOT CONTAIN THE PROPER DATA FOR ANALYZING -------"+ Style.RESET_ALL)
             return
    print("-------------------------------------------------------------------------------------------")
    print(Style.RESET_ALL+"For %s:" %file_path)
    print()

    ##Creates a list of time in seconds for the run##
    start_time = time[0]
    time_list = [(t - start_time)/ Decimal(1e9) for t in time]

    ##Checks to ensure endaq is installed on the device##
    if contains_accelx and contains_accely and contains_accelz and containst:
        try:
            import endaq
            plot_error = False
        except: 
            print(Fore.RED + "ERROR-------Endaq is not installed, plots will not be displayed-------" + Style.RESET_ALL)
            print()
            plot_error = True

    ##For a cleaner display##
    if contains_posx and contains_posy:
        display = 1
    if contains_accelx and contains_accely:
        display = 2

    ##Subtracts the force of gravity from the z acceleration##
    if contains_accelz:
        i = 0
        new_zaccel = []
        while i < len(z_accel):
            new_zaccel.append((z_accel[i] - 9.80665))
            i = i + 1

    ##Determines the run time of the recording##
    if containst:
        dt_nano = (time[-1]- time[0])

        ##Makes sure that the time data hasn't been condensed##
        if dt_nano == 0:
            time_error = True
            print(Fore.RED + "     TIME ERROR----MAKE SURE TIME DATA HAS NOT BEEN CONDENSED."+ Style.RESET_ALL)
            print()
        else:
            time_error = False
            dt_sec = dt_nano / Decimal('1e9')
            dt_min = dt_sec / 60
            dt_hour = dt_min / 60
            if dt_hour < 1 and dt_min < 1:
                if dt_sec == 1:
                    print("     Runtime: %.3f second" %dt_sec)
                else:
                    print("     Runtime: %.3f seconds" %dt_sec)
                print()
            if dt_hour < 1 and dt_min >= 1:
                real_min = math.floor(dt_min)
                real_sec = dt_sec - (real_min * 60)
                if math.floor(dt_min) == 1 and dt_sec == 1:
                    print("     Runtime: %.0f minute" %real_min +" and %.0f second" %real_sec)
                if math.floor(dt_min) == 1 and dt_sec != 1:
                    print("     Runtime: %.0f minute" %real_min +" and %.3f seconds" %real_sec)
                if math.floor(dt_min) != 1 and dt_sec == 1:
                    print("     Runtime: %.0f minutes" %real_min +" and %.0f second" %real_sec)
                if math.floor(dt_min) !=1 and dt_sec != 1:
                    print("     Runtime: %.0f minutes" %real_min +" and %.3f seconds" %real_sec)
            if dt_hour >= 1:
                real_hour = math.floor(dt_hour)
                real_min = math.floor(dt_min - (real_hour * 60))
                real_sec = math.floor(dt_sec - (real_hour * 3600) - (real_min * 60))
                hour_label = "hour" if real_hour == 1 else "hours"
                min_label = "minute" if real_min == 1 else "minutes"
                sec_label = "second" if real_sec == 1 else "seconds"
                print("     Runtime: %.0f " %real_hour+(hour_label) +" %.0f "%real_min+(min_label)+" and" + " %.3f " %real_sec+(sec_label))
            if display == 1:
                print()

    ##Calculates Distance##
    if contains_posx and contains_posy:
        distance = 0
        i = 0
        while i < len(x_position) -1:
            dx = (x_position[i+1] - x_position[i])
            dy = (y_position[i+1] - y_position[i])
            distance = distance + math.sqrt(dx**2+dy**2)
            i = i+1
        if distance >= 1000:
                real_km = distance/1000
                print("     The distance traveled was %.3f kilometers." %real_km)
        else:
                print("     The distance traveled was %.3f meters." %distance)

    ##Calculates average speed from distance/time or mean(x twist)##
    if contains_twistx:
        avg_speed1 = 0
        avg_speed1 = sum(forward_speed) / len(forward_speed)
        avg_speed2 = 0
        if containst and time_error == False:
            avg_speed2 = Decimal(distance) / dt_sec
            print("     The average speed (mean) was %.3f m/s" %avg_speed1 + " and (Distance/Time) was %.3f m/s." %avg_speed2) 
        elif time_error == True:
            print("     The average speed (mean) was %.3f m/s." %avg_speed1)
    
    ##Determines max forward speed##
    if contains_twistx:
        max_speed = max(forward_speed)
        print("     The maximum speed reached was %.3f m/s." %max_speed)

    ##Calculates the change in altitude over the entire run##
    if contains_posz:
        altitude_change = 0
        i = 1
        while i <len(z_position) -1:
            dz = (z_position[i+1] - z_position[i])
            altitude_change = altitude_change + abs(dz)
            i = i+1
        print()
        print("     The change in altitude was %.3f meters." %altitude_change)

        ##Calculates the difference in altitude from the start##
        dif_altitude = (z_position[-1] - z_position[1])
        print("     The difference in altitude from the start was %.3f meters." %dif_altitude)

    ##Determines the maximum forward acceleration##
    if contains_accelx:
        max_accel = max(x_accel)
        max_g = max_accel / 9.80665
        print()
        print("     The maximum forward acceleration was %.3f m/s/s " %max_accel + "(%.3f G)" %max_g)

    ##Applies a butterworth filter to the acceleration data and plots them with the raw data##
    if contains_accelx and contains_accely and contains_accelz and time_error==False and plot_error==False:
        time_deltas = np.diff(time_list)
        avg_dt = np.mean(time_deltas)
        sampling_rate = 1 / avg_dt        
        nyq = sampling_rate/2

        ##Adjust these as needed, these are in Hz, then normalized##
        low_cutoff = None
        high_cutoff = 3

        ##Specifics for comfort calculation is set to 5Hz low and 20Hz high##
        low_cutoff_norm_comfort = float(Decimal('5')/nyq)
        high_cutoff_norm_comfort = float(Decimal('20')/nyq)
        if low_cutoff != None:
            low_cutoff_norm = float(Decimal(low_cutoff)/nyq)
        else:
            low_cutoff_norm = None
        if high_cutoff != None:
            high_cutoff_norm = float(Decimal(high_cutoff)/nyq)
        else:
            high_cutoff_norm = None

        ##For event detection, the low cutoff is set to 5 Hz and there is no high cutoff##
        low_cutoff_norm_event = float(Decimal('5')/nyq)
        high_cutoff_norm_event = None

        fig = go.Figure()
        x_series = pd.Series(x_accel, name="x_raw")
        y_series = pd.Series(y_accel, name="y_raw")
        z_series = pd.Series(new_zaccel, name="z_raw")
        x_df = pd.DataFrame(x_series)
        y_df = pd.DataFrame(y_series)
        z_df = pd.DataFrame(z_series)
        xaccel_filtered=endaq.calc.filters.butterworth(x_df, low_cutoff=low_cutoff_norm, high_cutoff=high_cutoff_norm)
        yaccel_filtered=endaq.calc.filters.butterworth(y_df, low_cutoff=low_cutoff_norm, high_cutoff=high_cutoff_norm)
        zaccel_filtered=endaq.calc.filters.butterworth(z_df, low_cutoff=low_cutoff_norm, high_cutoff=high_cutoff_norm)

        xaccel_comfort = endaq.calc.filters.butterworth(x_df, low_cutoff=low_cutoff_norm_comfort, high_cutoff=high_cutoff_norm_comfort)
        yaccel_comfort=endaq.calc.filters.butterworth(y_df, low_cutoff=low_cutoff_norm_comfort, high_cutoff=high_cutoff_norm_comfort)
        zaccel_comfort=endaq.calc.filters.butterworth(z_df, low_cutoff=low_cutoff_norm_comfort, high_cutoff=high_cutoff_norm_comfort)

        xaccel_events = endaq.calc.filters.butterworth(x_df, low_cutoff=low_cutoff_norm_event, high_cutoff=high_cutoff_norm_event)
        yaccel_events=endaq.calc.filters.butterworth(y_df, low_cutoff=low_cutoff_norm_event, high_cutoff=high_cutoff_norm_event)
        zaccel_events=endaq.calc.filters.butterworth(z_df, low_cutoff=low_cutoff_norm_event, high_cutoff=high_cutoff_norm_event)

        filtered_magnitude = np.sqrt( xaccel_events.iloc[:, 0]**2+yaccel_events.iloc[:,0]**2+zaccel_events.iloc[:, 0]**2)
        magnitude_series = pd.Series(filtered_magnitude, name="filt_mag")

        xaccel_filtered.columns = xaccel_filtered.columns.map(str)
        yaccel_filtered.columns = yaccel_filtered.columns.map(str)
        zaccel_filtered.columns = zaccel_filtered.columns.map(str)
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        subplot_titles=("X Acceleration", "Y Acceleration", "Z Acceleration", "All Vector Acceleration"))
        fig.add_trace(go.Scatter(x=time_list, y=x_series, mode='lines', name='x_raw'), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_list, y=xaccel_filtered.iloc[:, 0], mode='lines', name='x_filtered'), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_list, y=y_series, mode='lines', name='y_raw'), row=2, col=1)
        fig.add_trace(go.Scatter(x=time_list, y=yaccel_filtered.iloc[:, 0], mode='lines', name='y_filtered'), row=2, col=1)
        fig.add_trace(go.Scatter(x=time_list, y=z_series, mode='lines', name='z_raw'), row=3, col=1)
        fig.add_trace(go.Scatter(x=time_list, y=zaccel_filtered.iloc[:, 0], mode='lines', name='z_filtered'), row=3, col=1)
        fig.add_trace(go.Scatter(x=time_list, y=magnitude_series, mode='lines', name='vector_magnitude'), row=4, col=1)
        fig.update_layout(
            height=1100,
            width=1000,
            title='Raw and Filtered Accelerations of %s'%file_path,
            xaxis_title='Time (s)',
            yaxis_title='Acceleration (m/s²)',
            template='plotly_white'
        )
        fig.show()
        print()
        print("     -----Plot is Displayed Successfully in Browser-----")
        print("     Plot Info:")
        if high_cutoff is None:
            print("          High Pass Filter Set to: None")
        else:
            print("          High Pass Filter Set to: %.2f"%high_cutoff+" Hz")
        if low_cutoff is None:
            print("          Low Pass Filter Set to: None")
        else:
            print("          Low Pass Filter Set to: %.2f"%low_cutoff+" Hz")
        comfort_index = np.mean(filtered_magnitude)
        print()
        ##Adjust the number comparison as needed based on different indexes of different roads##
            #####Note: This way of calculating could result in a rough or poorly paved road being shown as gravel#####
        if comfort_index > .3:
            print("     The Filtered Comfort Index is %.3f (Possibly Gravel)" %comfort_index)
        elif .1 < comfort_index < .2:
            print("     The Filtered Comfort Index is %.3f (Possibly Paved or Smooth Slab)" %comfort_index)
        elif comfort_index < .1:
            print("     The Filtered Comfort Index is %.3f (Possibly Smooth Paved)" %comfort_index)

        ##Finds the relative maximums above a given total acceleration (default 1.5) and finds the number of times that occurs##
        i = 0
        event = 0
        while i < len(magnitude_series):
            if magnitude_series[i] > 1.5 and magnitude_series[i-1] < magnitude_series[i] and magnitude_series[i+1] < magnitude_series[i]:
                event = event + 1
            i = i + 1
        if event > 0:
            event_occurrance = dt_sec / event
            print("     The rate of acceleration events is on average every %.3f seconds."%event_occurrance)
        if event > 10:
            print("     This recording is very bumpy with %.0f large bumps." %event)
        elif 0<event<10:
            print("     This recording is smooth, with only %.0f large bumps." % event)
        elif event == 0:
            print("     This recording is very smooth, with no large bumps.")



    ##Calculates unfiltered RMS of acceleration##
    if contains_accelx and contains_accely and contains_accelz:
        i = 0
        magnitude_sum = 0
        while i < len(x_accel) -1:
            magnitude_sum += (x_accel[i]**2 + y_accel[i]**2 + new_zaccel[i]**2)
            i = i+1
        rms = math.sqrt(magnitude_sum / (len(x_accel)-1))
        print()
        print("     The RMS Acceleration (Unfiltered) was %.3f m/s/s." %rms)

    ##Finds the point that the change in acceleration (jerk) is greatest and the time it occurrs##
    if contains_accelx and contains_accely and contains_accelz:
        i = 0
        d_accel_total = []
        while i < len(x_accel) -1:
            dxacc = (x_accel[i+1]-x_accel[i])
            dyacc = (y_accel[i+1]-y_accel[i])
            dzacc = (new_zaccel[i+1]-new_zaccel[i])
            d_accel_total.append(math.sqrt(dxacc**2+dyacc**2+dzacc**2))
            i = i +1
        max_daccel = max(d_accel_total)
        max_index = d_accel_total.index(max_daccel)
        time_of_max_daccel = float(time_list[max_index])
        print("     The maximum change in acceleration was %.3f m/s/s" %max_daccel+" at %.3f seconds." %time_of_max_daccel)

    print("-------------------------------------------------------------------------------------------")
file_path = sys.argv[1]
read_csv(file_path)