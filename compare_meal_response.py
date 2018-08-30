import re
import os
from datetime import timedelta
from copy import deepcopy
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot
from read_data import get_data, config



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

def get_glucose_plot(cgm_data, color='rgb(31, 119, 180)',
                        name='Glucose (mmol/L)', user='praveen'):
    color = color.replace('(', 'a(')
    color = color.replace(')', ', 0.8)')
    glucose_plot = go.Scatter(
            x=cgm_data['Time'],
            y=cgm_data['Glucose (mmol/L)'],
            name='{0}, Meal : {1}'.format(user, name),
            hoverinfo='y',
            line={'color': color,
                  },
            showlegend=True,
        )
    return glucose_plot

def get_time_interval_data(meal, interval=120):

    user = meal[0]
    records, cgm_data = get_data(user)
    start = records['Start'].iloc[meal[1]]

    def get_minutes(tdelta):
        days = tdelta.days
        seconds = tdelta.seconds
        return days * 1440 + seconds/60.


    records['Start'] = (records['Start'] - start).apply(get_minutes)
    records['Finish'] = (records['Finish'] - start).apply(get_minutes)
    cgm_data['Time'] = (cgm_data['Time'] - start).apply(get_minutes)


    records = records[(records['Start'] >= 0)
                        & (records['Start'] <= interval)]

    cgm_data = cgm_data[(cgm_data['Time'] >= 0)
                                  & (cgm_data['Time'] <= interval)]

    return records, cgm_data


def get_time_interval_plot(meal, glucose_color='rgb(31, 119, 180)',
                                ypos=5, interval=120):
    records, cgm_data = get_time_interval_data(meal, interval=interval)
    plot_colors = {'Sleep'    : 'rgba( 179, 181, 194, 0.5)',
                   'Meal'     : 'rgba( 85, 168, 104, 0.5)',
                   'Activity' : 'rgba( 129, 114, 178, 0.5)'
                   }
    name = records.iloc[0]['Event_details']
    user = meal[0]
    glucose_plot = get_glucose_plot(cgm_data, color=glucose_color,
                                        name=name, user=user)
    plot_data = [glucose_plot]
    for n, row in records.iterrows():
        color = plot_colors[row['Event_type']]
        plot_data.extend(get_records_plot(row, ypos, color=color,
                                            fontcolor=glucose_color))

    return plot_data


def get_comparision_plot(meals, interval=120):

    if len(meals) == 2:
        ypositions = [0, 1]
    else:
        ypositions = [0, 0.8, 1.6, 2.4]
    line_colors = ['rgb(31,119,180)', 'rgb(255,127,14)',
                        'rgb(148,103,189)', 'rgb(214,39,40)']
    plot_data = []
    for m, ypos, color in zip(meals, ypositions, line_colors):
        plot = get_time_interval_plot(m, glucose_color=color,
                                     ypos=ypos, interval=interval)
        plot_data.extend(plot)

    return plot_data

def get_animation_frames(plot_data):
    frame = deepcopy(plot_data)
    for data in frame:
        if data.name is not None:
            if 'Meal' in data.name:
                data['y'] = data['y'] - data['y'].iloc[0] + 5

    return [{'data' : frame, 'name' : 'normalize'},
            {'data' : plot_data, 'name' : 'original'}
            ]


def get_layout():
    return go.Layout(
        xaxis={'range': [0, interval],
               'title' : 'Time (minutes)',
               'tickvals' : [0, 60, 120, 180, 240],
               'zeroline' : False,
              },
        yaxis={'range': [-0.5, 14],
               'tickvals' : [4,6,8,10,12,14],
               'title' : 'Glucose (mmol/L)',
               'zeroline' : False,
               'hoverformat' : '.1f'
              },
        plot_bgcolor='rgba(0,0,0,0)',
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


def remove_startup_animation(fname):
    fname = re.sub("\\.then\\(function\\(\\)\\{Plotly\\.animate"
                    "\\(\\'[0-9a-zA-Z-]*\\'\\)\\;\\}\\)", "", fname)
    return fname




def compare_records(meals, fname, interval=120):

    plot_data = get_comparision_plot(meals, interval=interval)

    frames = get_animation_frames(plot_data)
    layout = get_layout()
    fig = {'data'   : plot_data,
           'layout' : layout,
           'frames' : frames
           }


    div = plot(fig, output_type='div', show_link=False)
    div = remove_startup_animation(div)


    if not os.path.exists('html'):
        os.mkdir('html')
    with open(fname, 'w') as fd:
        fd.write("""<html>
        <head>
        </head>
        <body>
            {}
        </body>
    </html>
    """.format(div))



interval = 240
all_meals =[
            {
             'meals' : [
                     ('Praveen', 36),
                     ('Praveen', 42),
                     ('Praveen', 47),
                     ('Praveen', 60)
                     ],
             'fname' : 'bread_jam_icetea.html'
             },
            {
             'meals' : [
                     ('Angela', 13),
                     ('Angela', 49)
                     ],
             'fname' : 'angela_breakfast.html'
             },
            {
             'meals' : [
                     ('Angela', 10),
                     ('Angela', 14),
                     ('Angela', 55)
                     ],
             'fname' : 'angela_chicken_rice.html'
             },
             {
             'meals' : [
                     ('Praveen', 12),
                     ('Praveen', 18),
                     ('Praveen', 22)
                    ],
             'fname' : 'bread_pnb_icetea.html'
            },
            {'meals' : [
                     ('Praveen', 13),
                     ('Praveen', 19)
                    ],
            'fname' : 'vivo_indian.html'
            },
            {'meals' : [
                     ('Praveen', 14),
                     ('Praveen', 20)
                    ],
            'fname' : 'chapati_ladyfinger.html'
            },
            {'meals' : [
                     ('Praveen', 25),
                     ('Praveen', 62)
                    ],
            'fname' : 'snacks.html'
            },
            {'meals' : [
                     ('Praveen', 26),
                     ('Angela', 50)
                    ],
            'fname' : 'McD.html'
            },
            {'meals' : [
                     ('YQ', 2),
                     ('YQ', 23),
                     ('YQ', 73)
                    ],
            'fname' : 'yq_breakfast.html'
            },
            {'meals' : [
                     ('YQ', 16),
                     ('YQ', 30),
                     ('YQ', 55),
                     ('YQ', 64)
                    ],
            'fname' : 'yq_lunch.html'
            },
            {'meals' : [
                     ('Praveen', 34),
                     ('Praveen', 61),
                     ('Angela', 0)
                    ],
            'fname' : 'subway.html'
            },
            {'meals' : [
                     ('Cher Wee', 2),
                     ('Cher Wee', 3)
                    ],
            'fname' : 'cw1.html'
            },
            {'meals' : [
                     ('Cher Wee', 4),
                     ('Cher Wee', 5),
                     ('Cher Wee', 8)
                    ],
            'fname' : 'cw2.html'
            },

]

for item in all_meals:
    meals = item['meals']
    fname = item['fname']
    fname = os.path.join('html', fname)
    compare_records(meals, fname, interval=interval)
