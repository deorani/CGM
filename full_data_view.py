import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot
from read_data import get_data, config


def get_date_button(date):
    label = date.strftime('%d %b')
    date_range = [date, date + timedelta(1)]
    return {'label'    : label,
            'method'   : 'relayout',
            'args'     : [{'xaxis' : {'range' : date_range}}]
            }

def get_records_plot(record, color='rgba( 179, 181, 194, 0.2)'):
    time_step_size = timedelta(seconds=60)
    x = np.arange(record['Start'], record['Finish'] + time_step_size,
                    time_step_size)
    y = [15]*x.shape[0]
    record_plot = go.Scatter(
            x=pd.Series(x),
            y=y,
            fill='tozeroy',
            mode='none',
            fillcolor=color,
            text=[record['Event_details']]*x.shape[0],
            hoverinfo='text',
            showlegend=False
    )
    return record_plot


user = 'Cher Wee'
start_date = config[user]['start_date'] + timedelta(seconds=60*60*8)
records, cgm_data = get_data(user)

cgm_plot = go.Scatter(
        x=cgm_data['Time'],
        y=cgm_data['Glucose (mmol/L)'],
        name='Glucose (mmol/L)',
        hoverinfo='y',
        line={'color': '#1f77b4'},
        showlegend=False
    )

plot_data = [cgm_plot]

record_plot_colors = {'Sleep'    : 'rgba( 179, 181, 194, 0.2)',
                      'Meal'     : 'rgba( 85, 168, 104, 0.3)',
                      'Activity' : 'rgba( 129, 114, 178, 0.2)'
                     }
for n, row in records.iterrows():
    color = record_plot_colors[row['Event_type']]
    plot_data.append(get_records_plot(row, color=color))


buttons = [get_date_button(start_date + timedelta(days))
                                    for days in range(13)]
updatemenus=[{ 'buttons' : buttons }]

layout = go.Layout(
    xaxis={'range': [start_date, start_date + timedelta(1)]},
    yaxis={'range': [2, 14],
           'title' : 'Glucose (mmol/L)',
           'hoverformat' : '.1f'
          },
    plot_bgcolor='rgba(0,0,0,0)',
    updatemenus=updatemenus,
    hoverdistance=1
)

fig = go.Figure(
        data=plot_data,
        layout=layout
    )

if not os.path.exists('html'):
        os.mkdir('html')
plot(fig, show_link=False,
        filename=os.path.join('html', 'full_data_{}.html'.format(user)))
