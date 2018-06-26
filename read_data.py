from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d, PchipInterpolator

def expand_time(data):
    t = data['Time'].values.astype('uint64')/1e9
    g = data['Glucose (mmol/L)'].values
    
    new_t = np.arange(t[0], t[-1]+1, 60)
    #~ new_g = PchipInterpolator(t, g)(new_t)
    new_g = interp1d(t, g)(new_t)
    
    new_data = {'Time' : pd.to_datetime(pd.Series(new_t*1e9)),
                'Glucose (mmol/L)' : new_g}
    return pd.DataFrame(new_data)

def insert(df, index, values):
    df1 = df[:index]
    df2 = df[index:]
    values = {k:v for k,v in zip(df.columns.values, values)}
    df1 = df1.append(values,ignore_index=True)
    return pd.concat((df1, df2)).reset_index(drop=True)

start_date = datetime(2018, 6, 5)
end_date = datetime(2018, 6, 18)

## read and process glucose readings
data = pd.read_csv('libre_data2.txt', sep='\t')
data['Time'] = data['Time'].apply(datetime.strptime, args=('%Y/%m/%d %H:%M',))
data = data[(data['Time'] > start_date) 
            & (data['Time'] <= end_date)]

data = data.sort_values('Time')
data['Glucose (mmol/L)'] = data['Historic Glucose (mmol/L)'].fillna(
                                        data['Scan Glucose (mmol/L)']
                                        )
data = data[['Time', 'Glucose (mmol/L)']]


time_gaps = np.where(data['Time'].diff() > timedelta(minutes=20))[0]
for n, tg in enumerate(time_gaps):
    mid_time = data['Time'].iloc[tg+n-1] + timedelta(minutes=10)
    data = insert(data, tg+n, values=[mid_time, np.NaN])


data = expand_time(data)
## read and process records of sleep, meal and activity
records = pd.read_csv("Continous_glucose_monitoring_praveen.csv")
read_date = lambda s : datetime.strptime(s, "%d %B %I:%M %p").replace(year=2018)
records['Start'] = records['Start'].apply(read_date)
records['Finish'] = records['Finish'].apply(read_date)
events = records['Event'].str.split(':', expand=True)
events['Event_type'] = events.pop(0).str.strip()
events['Event_details'] = events.pop(1).str.strip()
times = records[['Start', 'Finish']]
records = pd.concat((times, events), axis=1)


