import streamlit as st

import pandas as pd
import numpy as np

import plotly.graph_objects as go

file_path = './data/central_trend_2017_base.xlsx'
genders = ['Males', 'Females']

# Widgets
st.set_page_config(layout='centered', page_title='#WOW2023 Week 19')

primary_year = st.sidebar.selectbox('Primary Year', 
                            options=[str(year) for year in range(2011, 2051)],
                            index=2023-2011,
                            )

secondary_year = st.sidebar.selectbox('Secondary Year',
                            options=[str(year) for year in range(2011, 2051)],
                            index=0,
                            )

st.title('#WOW2023 Week 19: Can you create a jitterfly chart? ')
st.markdown(f'### What is the predicted population of {primary_year} vs {secondary_year}?')

@st.cache_data
def load_data(file_path):
    data = pd.read_excel(file_path, sheet_name=None)
    
    data_selected = {}
    for gender in genders:
        # Cut the age into discrete intervals
        bins = np.arange(0, data[f'Population - {gender}']['age'].max()+1, 10)
        bins[0] = -1
        labels = ['<=10' if age<10 else ('80+' if age>=80 else f'{age+1}-{age+10}') 
                for age in bins[:-1]]
        df = data[f'Population - {gender}']
        df['age_level'] = pd.cut(df['age'], bins=bins, labels=labels)
        df.columns = df.columns.astype('str')
        # Remove the items for London, which is the total population and duplicate.
        data_selected[gender] = df.query('district != "London"').groupby(['age_level', 'district']).sum(numeric_only=True)
        data_selected[f'{gender}_avg']  =data_selected[gender].groupby('age_level').mean(numeric_only=True)

    return data_selected


data_selected = load_data(file_path)

# Figure by plotly
fig = go.Figure()

colors = {'Males': '#86BCB6',
          'Females': '#BD54A1'}
width=0.9

for gender in genders:    
    # Add some jitter to the age level
    offset = 0.8
    unique_districts = data_selected[f'{gender}'].reset_index()['district'].unique()
    jitter = pd.DataFrame({'district': unique_districts,
                           'jitter': np.random.default_rng(123).uniform(
                               offset*(-width/2), offset*(width/2), len(unique_districts))})
    
    df = data_selected[f'{gender}'].reset_index().merge(jitter, on='district')
    age_level = df['age_level'].unique()
    age_pos = pd.DataFrame({'age_level': age_level,
                            'age_pos': np.arange(0, len(age_level))})
    df = df.merge(age_pos, on='age_level')
    
    # Hover templates
    py_idx = np.where(df.columns==primary_year)[0][0]
    sy_idx = np.where(df.columns==secondary_year)[0][0]
    df['pop_diff_pct'] = (df[primary_year] - df[secondary_year]) / df[secondary_year]
    df['icon'] = np.where(df['pop_diff_pct']>0, '▲', '▼')
    hovertemplate = (
    '<b>Population Estimates</b>'
    '<br><br><span style="color:gray">Age</span>: %{customdata[0]}'
    '<br><span style="color:gray">District</span>: %{customdata[1]}'
    f'<br><span style="color:gray">Gender</span>: {gender}'
    f'<br><span style="color:gray">{primary_year}</span>: %{{customdata[{py_idx}]:,.0f}}'
    f'<br><span style="color:gray">{secondary_year}</span>: %{{customdata[{sy_idx}]:,.0f}}'
    '<br><br>%{customdata[46]} %{customdata[45]:.1%}<extra></extra>'
    )
    
    # Add bar chart
    ys = np.arange(0, len(data_selected[f'{gender}_avg'].index))
    xs = data_selected[f'{gender}_avg'][primary_year]
    if gender == 'Females':
        xs = -xs
    bar_py_idx = np.where(data_selected[f'{gender}_avg'].columns==primary_year)[0][0]
    bar_sy_idx = np.where(data_selected[f'{gender}_avg'].columns==secondary_year)[0][0]
    fig.add_bar(x=xs, y=ys, orientation='h', name=gender, offset=-width/2,
                marker_color=colors[gender], marker_opacity=0.2,
                width=width, 
                customdata=data_selected[f'{gender}_avg'],
                hovertemplate=(f'<b>Average {gender}<b><br><br>'
                               f'<span style="color:gray">{primary_year}</span>: %{{customdata[{bar_py_idx}]:,.0f}}<br>'
                               f'<span style="color:gray">{secondary_year}</span>: %{{customdata[{bar_sy_idx}]:,.0f}}<extra></extra>'
                              )
               )
    
    # Add text in the center of the bar
    fig.add_scatter(x=[0]*len(ys), y=ys, text=data_selected[f'{gender}_avg'].index, mode='text',
                    hoverinfo='skip')
    
    # Add scatter chart
    xs = df[primary_year]
    ys = df['age_pos'] + df['jitter']
    if gender == 'Females':
        xs = -xs
    fig.add_scatter(x=xs, y=ys, mode='markers', name=f'{gender} per district',
                    marker_color=colors[gender], marker_opacity=0.6,
                    customdata=df,
                    hovertemplate=hovertemplate)

    # Add average population for the secondary year
    for ypos in np.arange(0, len(data_selected[f'{gender}_avg'].index)):
        xpos = data_selected[f'{gender}_avg'][secondary_year][ypos]
        if gender == 'Females':
            xpos = -xpos
        fig.add_shape(type='line', xref='x', yref='y',
                      x0=xpos, y0=ypos-width/2,
                      x1=xpos, y1=ypos+width/2,
                      line_color=colors[gender], 
                      line_width=3, opacity=1)  
    
    
fig.update_layout(template='simple_white', width=900, height=600,
                  hoverlabel_bgcolor="white", showlegend=False,
                  margin=dict(t=10)
                  )
fig.update_yaxes(range=[-0.7,9], autorange='reversed', visible=False,
                 ticktext=list(data_selected[f'{gender}_avg'].index), 
                 tickvals=np.arange(0, len(data_selected[f'{gender}_avg'].index)))
fig.update_xaxes(showline=False, ticks='', title='Population',
                 ticktext=[f'{abs(n)}K' for n in range(-40, 41, 10)],
                 tickvals=list(range(-40000, 40001, 10000)))
fig.add_annotation(x=0.5, y=-0.125,
            text="#WOW2023 W19 | Data: London Data Store | Created by @LZY_CHN",
            showarrow=False, font_color='gray',
            xref='paper', yref='paper')

# Plotly chart widgets
st.plotly_chart(fig, use_container_width=True)