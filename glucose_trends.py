import os
import plotly.graph_objs as go
from plotly.offline import plot
from read_data import glucose_data, records

def get_glucose_range(glucose):
    if glucose < 2:
        return '< 2 mmol/L'
    th = [2, 4, 6, 8, 10, 20]
    for i in range(len(th)-2):
        if glucose < th[i+1]:
            return '{0} - {1} mmol/L'.format(th[i], th[i+1])
    return '> 10 mmol/L'
    


def compare_data_subsets(data1, data1_name, data2, data2_name):
    
    index = ['2 - 4 mmol/L', '4 - 6 mmol/L', '6 - 8 mmol/L', 
                  '8 - 10 mmol/L', '> 10 mmol/L']
    
    glucose_vs_time1 = data1['glucose_range'].value_counts()
    time_vs_range1 = glucose_vs_time1.loc[index].values/60.
    
    
    glucose_vs_time2 = data2['glucose_range'].value_counts()
    time_vs_range2 = glucose_vs_time2.loc[index].values/60.
    
    bar1 = go.Bar(
        x=index,
        y=time_vs_range1 *100. / time_vs_range1.sum(),
        name=data1_name
    )
    bar2 = go.Bar(
        x=index,
        y=time_vs_range2 *100. / time_vs_range2.sum(),
        name=data2_name
    )

    plotbar_data = [bar1, bar2]
    
    
    data1 = data1[data1['original_data_point']]
    data2 = data2[data2['original_data_point']]
    
    pp_map = {True: 'post prandial', False: 'baseline'}
    x1 = data1['is_post_prandial'].map(pp_map)
    x2 = data2['is_post_prandial'].map(pp_map)
    
    box1 = go.Box(y=data1['Glucose (mmol/L)'],
                    x=x1,
                    marker={'size' : 2},
                    boxpoints='outliers',
                    jitter=0.2,
                    name=data1_name
                    )

    box2 = go.Box(y=data2['Glucose (mmol/L)'],
                    x=x2,
                    marker={'size' : 2},
                    boxpoints='outliers',
                    jitter=0.2,
                    name=data2_name
                    )

    plotbox_data = [box1, box2]
    
    layout = go.Layout(
                yaxis={
                       'title' : 'Time (%)',
                       'hoverformat': '.1f'
                      },
                boxmode='group',
                barmode='group',
                bargap=0.15,
                bargroupgap=0.1,
                legend={'x'         : 0.98,
                        'xanchor'   : 'right',
                        'y'         : 0.98,
                        'yanchor'   : 'top'
                        },                      
                )
    
    figbar = go.Figure(data=plotbar_data, layout=layout)
    if not os.path.exists('html'):
        os.mkdir('html')
    filename='{0}_vs_{1}_time_bar.html'.format(data1_name, data2_name)
    filename = os.path.join('html', filename)
    plot(figbar, filename)

    
    layout['yaxis']['title'] = 'Glucose (mmol/L)'
    figbox = {'data'   : plotbox_data,
              'layout' : layout,
             }
    filename='{0}_vs_{1}_glucose_box_bar.html'.format(data1_name, data2_name)   
    filename = os.path.join('html', filename)
    plot(figbox, filename=filename)
    

glucose_data['glucose_range'] = glucose_data['Glucose (mmol/L)'].apply(
                                                        get_glucose_range)

## comparing sleeep time to awake time
sleep_data = glucose_data[glucose_data['is_sleep']]
awake_data = glucose_data[~glucose_data['is_sleep']]
compare_data_subsets(sleep_data, 'sleep', awake_data, 'awake')


## comparing weekday to weekend   -- ## excluding 16 and 17th
batam = glucose_data['Time'].apply(lambda x: x.day in [16, 17])
glucose_data = glucose_data[~batam]
weekend = glucose_data['Time'].apply(lambda x: x.weekday() in [5, 6])
weekend_data = glucose_data[weekend]
weekday_data = glucose_data[~weekend]
compare_data_subsets(weekday_data, 'weekday', weekend_data, 'weekend')

