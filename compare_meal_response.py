import re
from datetime import timedelta
from copy import deepcopy
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot
from read_data import data, records



def get_records_plot(record, ypos, color='rgba( 179, 181, 194, 0.2)',
                                    fontcolor='rgb( 179, 181, 194)'):
    x = np.arange(record['Start'], record['Finish'] + 1, 1)
    y = [ypos]*x.shape[0]
    text = ['']*x.shape[0]
    text[0] = record['Event_type']
    record_plot = go.Scatter(
            x=x,
            y=y,
            mode='lines+text',
            fill='none',
            line = {
                'color' : color,
                'width' : 0.1
            },
            text=text,
            textposition='top right',
            textfont={'size' : 10,
                      'color' : fontcolor
                      },
            hoverinfo='none',
            showlegend=False,
    )
    text = [record['Event_details']] * x.shape[0]
    trace2 = go.Scatter(
            x=x,
            y=[i-0.35 for i in y],
            mode='none',
            fill='tonexty',
            fillcolor=color,
            line = {
                'color' : color,
            },
            text=text,
            hoverinfo='text',
            showlegend=False,
    )
    return [record_plot, trace2]
    
def get_glucose_plot(glucose_data, color='rgb(31, 119, 180)',
                        name='Glucose (mmol/L)'):
    color = color.replace('(', 'a(')
    color = color.replace(')', ', 0.8)')
    glucose_plot = go.Scatter(
            x=glucose_data['Time'], 
            y=glucose_data['Glucose (mmol/L)'],
            name='Meal : {0}'.format(name),
            hoverinfo='y',
            line={'color': color,
                  },
            showlegend=True,
        )
    return glucose_plot

def get_time_interval_data(start, records, glucose_data, interval=120):
    records = records.copy()
    glucose_data = glucose_data.copy()
    
    def get_minutes(tdelta):
        days = tdelta.days
        seconds = tdelta.seconds
        return days * 1440 + seconds/60.
        
    
    records['Start'] = (records['Start'] - start).apply(get_minutes)
    records['Finish'] = (records['Finish'] - start).apply(get_minutes)
    glucose_data['Time'] = (glucose_data['Time'] - start).apply(get_minutes)
    
    
    records = records[(records['Start'] >= 0)
                        & (records['Start'] <= interval)]
    
    glucose_data = glucose_data[(glucose_data['Time'] >= 0)
                                  & (glucose_data['Time'] <= interval)]
                                
    return records, glucose_data
    

def get_time_interval_plot(start, records, glucose_data, 
                             glucose_color='rgb(31, 119, 180)',
                                ypos=5, interval=120):
    records, glucose_data = get_time_interval_data(start, records, 
                                    glucose_data, interval=interval)
    plot_colors = {'Sleep'    : 'rgba( 179, 181, 194, 0.5)',
                   'Meal'     : 'rgba( 85, 168, 104, 0.5)',
                   'Activity' : 'rgba( 129, 114, 178, 0.5)'
                   }
    name = records.iloc[0]['Event_details']
    glucose_plot = get_glucose_plot(glucose_data, color=glucose_color,
                                        name=name)
    plot_data = [glucose_plot]
    for n, row in records.iterrows():
        color = plot_colors[row['Event_type']]
        plot_data.extend(get_records_plot(row, ypos, color=color,
                                            fontcolor=glucose_color))
        
    return plot_data


def get_comparision_plot(time1, time2, records, 
                            glucose_data, interval=120):
    plot1 = get_time_interval_plot(time1, records, glucose_data, 
                                    glucose_color='rgb(31, 119, 180)',
                                     ypos=1.3, interval=interval)
    plot2 = get_time_interval_plot(time2, records, glucose_data, 
                                    glucose_color='rgb( 196, 78, 82)',
                                     ypos=2.5, interval=interval)
    return plot1 + plot2


def get_animation_frames(plot_data):
    frame = deepcopy(plot_data)
    for data in frame:
        if data.name is not None:
            if data.name.startswith('Meal'):
                data['y'] = data['y'] - data['y'].iloc[0] + 5
    
    return [{'data' : frame, 'name' : 'normalize'},
            {'data' : plot_data, 'name' : 'original'}
            ]
            


interval = 120
time1 = records['Start'].iloc[8]
time2 = records['Start'].iloc[14]
plot_data = get_comparision_plot(time1, time2, records, data,
                                    interval=interval)
frames = get_animation_frames(plot_data)


layout = go.Layout(
    xaxis={'range': [0, interval],
           'title' : 'Time (minutes)',
           'zeroline' : False,
          },
    yaxis={'range': [0, 14],
           'tickvals' : [4,6,8,10,12,14],
           'title' : 'Glucose (mmol/L)',
           'zeroline' : False,
          },
    hovermode='closest',
    legend={'x'         : 0.98,
            'xanchor'   : 'right',
            'y'         : 0.98,
            'yanchor'   : 'top'
            },
    updatemenus=[{'type'   : 'buttons',
                  'buttons': [{'label': 'Normalized',
                               'method': 'animate',
                               'args': [['normalize']]
                               },
                               {'label': 'Original',
                               'method': 'animate',
                               'args': [['original']]
                               }
                             ]
                        }],
                               
)



fig = {'data'   : plot_data,
       'layout' : layout,
       'frames' : frames
       }
    

fname = 'compare.html'
pl1 = plot(fig, output_type='div')
pl1 = re.sub("\\.then\\(function\\(\\)\\{Plotly\\.animate\\(\\'[0-9a-zA-Z-]*\\'\\)\\;\\}\\)", "", pl1)
with open(fname, 'w') as fd:
    fd.write("""<html>
<head>
</head>
<body>
{}
</body>
</html>
""".format(pl1))



