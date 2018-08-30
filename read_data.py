from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
from scipy.interpolate import interp1d, PchipInterpolator

def expand_time(data):
    t = data['Time'].values.astype('uint64')/1e9
    g = data['Glucose (mmol/L)'].values

    new_t = np.arange(t[0], t[-1]+1, 60)
    #~ new_g = PchipInterpolator(t, g)(new_t)
    new_g = interp1d(t, g)(new_t)

    new_data = {'Time' : pd.to_datetime(pd.Series(new_t*1e9)),
                'Glucose (mmol/L)' : new_g}
    new_data = pd.DataFrame(new_data)
    new_data['original_data_point'] = new_data['Time'].isin(data['Time'])
    return new_data

def insert(df, index, values):
    df1 = df[:index]
    df2 = df[index:]
    values = {k:v for k,v in zip(df.columns.values, values)}
    df1 = df1.append(values,ignore_index=True)
    return pd.concat((df1, df2)).reset_index(drop=True)


def add_sleep_info(data, records):
    sleep_records = records[records['Event_type'] == 'Sleep']
    i = j = 0
    sleep_info = [False] * data.shape[0]
    while i < data.shape[0] and j < sleep_records.shape[0]:
        if data.iloc[i]['Time'] <= sleep_records.iloc[j]['Start']:
            i += 1
        elif data.iloc[i]['Time'] > sleep_records.iloc[j]['Start']:
            sleep_info[i] = True
            i += 1
        if data.iloc[i-1]['Time'] > sleep_records.iloc[j]['Finish']:
            j += 1

    data['is_sleep'] = sleep_info
    return data


def add_postprandial_info(data, records, time_interval=120):
    meal_records = records[records['Event_type'] == 'Meal']
    i = j = 0
    postprandial_info = [False] * data.shape[0]
    while i < data.shape[0] and j < meal_records.shape[0]:
        start = meal_records.iloc[j]['Start']
        interval_finish = start + timedelta(seconds=60*time_interval)
        if data.iloc[i]['Time'] <= start:
            i += 1
        elif data.iloc[i]['Time'] > start:
            postprandial_info[i] = True
            i += 1
        if data.iloc[i-1]['Time'] > interval_finish:
            j += 1

    data['is_post_prandial'] = postprandial_info
    return data


def read_cgm_data(fname, start_date, end_date):
    ## read and process glucose readings
    cgm_raw_file = os.path.join('data', 'raw', 'libre_data.txt')
    cgm_data = pd.read_csv(cgm_raw_file, sep='\t')
    time_reader = lambda s: datetime.strptime(s,'%Y/%m/%d %H:%M')
    cgm_data['Time'] = cgm_data['Time'].apply(time_reader)
    cgm_data = cgm_data[(cgm_data['Time'] > start_date)
                                & (cgm_data['Time'] <= end_date)]
    return cgm_data

def process_cgm_data(cgm_data, records):

    cgm_data = cgm_data.sort_values('Time')
    historic_gl = cgm_data['Historic Glucose (mmol/L)']
    scan_gl = cgm_data['Scan Glucose (mmol/L)']
    cgm_data['Glucose (mmol/L)'] = historic_gl.fillna(scan_gl)
    cgm_data = cgm_data[['Time', 'Glucose (mmol/L)']]

    time_gaps = np.where(cgm_data['Time'].diff() > timedelta(minutes=20))[0]
    for n, tg in enumerate(time_gaps):
        mid_time = cgm_data['Time'].iloc[tg+n-1] + timedelta(minutes=10)
        cgm_data = insert(cgm_data, tg+n, values=[mid_time, np.NaN])

    cgm_data = expand_time(cgm_data)
    ## post process glucose data
    cgm_data = add_sleep_info(cgm_data, records)
    cgm_data = add_postprandial_info(cgm_data, records)
    return cgm_data

def read_praveen_records():
    def time_reader(s):
        t = datetime.strptime(s, "%d/%m/%y %H:%M")
        return t

    records = pd.read_csv(os.path.join('data', 'raw', 'records_praveen.csv'))
    records['Start'] = records['Start'].apply(time_reader)
    records['Finish'] = records['Finish'].apply(time_reader)
    return records

def read_cherwee_records():
    def time_reader(s):
        t = datetime.strptime(s, "%d/%m/%y %H:%M")
        return t

    records = pd.read_csv(os.path.join('data', 'raw', 'records_cherwee.csv'))
    records['Start'] = records['Start'].apply(time_reader)
    records['Finish'] = records['Finish'].apply(time_reader)
    return records


def read_angela_records():
    def time_reader(s):
        s = s.replace('Jul ', 'July ').replace('Aug ', 'August ')
        t = datetime.strptime(s, '%d %B %H:%M %p')
        t = t.replace(year=2018)
        return t

    records = pd.read_csv(os.path.join('data', 'raw', 'records_angela.csv'))
    records['Start'] = records['Start'].apply(time_reader)
    records['Finish'] = records['Finish'].apply(time_reader)
    return records


def read_yq_records():
    def time_reader(s):
        t = datetime.strptime(s, '%Y/%m/%d %H:%M')
        return t

    records = pd.read_csv(os.path.join('data', 'raw', 'records_yq.csv'))
    records['Start'] = records['Start'].apply(time_reader)
    records['Finish'] = (records['Start']
                        + pd.to_timedelta(records['duration'], unit='m'))
    records['Event'] = records['Event'].str.capitalize()
    return records


def process_records(records):
    events = records['Event'].str.split(':', expand=True)
    events['Event_type'] = events.pop(0).str.strip()
    events['Event_details'] = events.pop(1).str.strip()
    times = records[['Start', 'Finish']]
    records = pd.concat((times, events), axis=1)
    return records

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_data(user):
    records_file = os.path.join('data', 'pkl', '{}_records.pkl'.format(user))
    cgm_file = os.path.join('data', 'pkl', '{}_cgm.pkl'.format(user))

    if os.path.exists(records_file):
        records = pd.read_pickle(records_file)
    else:
        records = config[user]['records_reader']()
        records = process_records(records)
        mkdir(os.path.join('data', 'pkl'))
        records.to_pickle(records_file)

    if os.path.exists(cgm_file):
        cgm_data = pd.read_pickle(cgm_file)
    else:
        start_date = config[user]['start_date']
        end_date = config[user]['end_date']
        cgm_data = read_cgm_data('libre_data.txt', start_date, end_date)
        cgm_data = process_cgm_data(cgm_data, records)
        mkdir(os.path.join('data', 'pkl'))
        cgm_data.to_pickle(cgm_file)

    return records, cgm_data


config = {
          'Praveen' :   {'start_date' : datetime(2018, 6, 5),
                         'end_date' : datetime(2018, 6, 18),
                         'records_reader' : read_praveen_records
                        },
          'Angela'  :   {'start_date' : datetime(2018, 7, 23),
                         'end_date' : datetime(2018, 8, 6),
                         'records_reader' : read_angela_records
                        },
           'YQ'     :    {'start_date' : datetime(2018, 5, 17),
                         'end_date' : datetime(2018, 5, 31),
                         'records_reader' : read_yq_records
                        },
           'Cher Wee' : {'start_date' : datetime(2018, 6, 26),
                         'end_date' : datetime(2018, 7, 10),
                         'records_reader' : read_cherwee_records
                        }
}
