import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import bokeh.plotting as bp
import bokeh.models as bm
import bokeh.transform as bt

if 'top_num' not in st.session_state:
    st.session_state.top_num = 5

if 'metrics' not in st.session_state:
    st.session_state.metrics = '# of Customers'

st.set_page_config(layout='wide', page_title='2023 Week 16')

# The main widgets
title = f'Top {st.session_state.top_num} Products - {st.session_state.metrics}'
st.title(title)

st.sidebar.markdown(
    'Select the number of products you would like to be included '
    'and the metric you would like to see in the charts.')

st.sidebar.divider()

top_num = st.sidebar.radio(
    'Select Top Products',
    options=np.arange(1, 6, 1),
    key='top_num')

metrics_opts = [
    '# of Customers', 'Gross Margin', 'Gross Margin %',
    'Total COGS', 'Total Revenue']
metrics = st.sidebar.radio(
    'Select Metric', options=metrics_opts, key='metrics')

fields = {
    '# of Customers': 'Customer Key',
    'Gross Margin': 'Gross Margin',
    'Gross Margin %': 'Gross Margin %',
    'Total COGS': 'COGS',
    'Total Revenue': 'Revenue'}

st.sidebar.divider()

# Chart content

# Manipulate data
file_path = './data/Dataset-Customer Profitability.xlsx'
geo_file = './data/gadm41_USA_1.json'


@st.cache_data
def read_data_from_files(file_path, geo_file):
    # Read data
    data = pd.read_excel(file_path, sheet_name=None)
    customers = data['customer'].merge(
        data['industry'], left_on='Industry ID', right_on='ID', how='left').merge(
        data['state'], left_on='State', right_on='StateCode', how='left')
    data_customer = data['factsales'].sort_values(by='YearPeriod').reset_index(drop=True).merge(
        data['product'], on='Product Key', how='left').merge(
        customers, left_on='Customer Key', right_on='Customer', how='left').merge(
        data['date'], on='YearPeriod', how='left')
    data_customer['COGS'] = data_customer.iloc[:, range(6, 12)].sum(axis=1)
    data_customer['Gross Margin'] = data_customer['Revenue'] - \
        data_customer['COGS']
    data_selected = data_customer.loc[:, ['YearPeriod', 'Customer Key', 'Industry',
                                          'Product', 'State_y', 'Revenue', 'COGS', 'Gross Margin', 'Year', 'Qtr', 'Month']]
    data_selected['Product'] = data_selected['Product'].fillna('(Blank)')
    data_selected['Industry'] = data_selected['Industry'].fillna('(Blank)')
    data_selected['Month'] = pd.Categorical(data_selected['Month'].values,
                                            categories=['Jan', 'Feb', 'Mar', 'Apr',
                                                        'May', 'Jun', 'Jul', 'Aug',
                                                        'Sep', 'Oct', 'Nov', 'Dec'],
                                            ordered=True)
    data_selected = data_selected.astype({'Year': 'str'})

    # Read geodata
    us_df = gpd.read_file(geo_file)
    us_df_wm = us_df.to_crs(epsg=3857)
    us_df_wm['center'] = us_df_wm['geometry'].centroid
    us_df_center = us_df_wm.loc[:, ['NAME_1', 'center']].rename(
        columns={'center': 'geometry'})

    return {'sales': data_selected, 'patches': us_df_wm, 'points': us_df_center}


@st.cache_data
def load_plotting_data(top_num, metrics):
    data = read_data_from_files(file_path, geo_file)
    field = fields[metrics]
    us_df_json = data['patches'].iloc[:, slice(0, -1)].to_json()
    if metrics == '# of Customers':
        table_data = data['sales'].groupby('Product', dropna=False).nunique(
        ).sort_values(by=field, ascending=False)[[field]]
        indx = table_data.index[:top_num]
        filtered_rows = data['sales']['Product'].apply(lambda x: x in indx)
        bar_data = data['sales'].loc[filtered_rows, :].groupby(
            'Industry', dropna=False).nunique().sort_values(by=field)[[field]]
        line_group = data['sales'].loc[filtered_rows, :].groupby(
            ['Year', 'Qtr', 'Month'], dropna=False, observed=True)
        line_data = line_group.nunique()[[field]]
        state_data = data['sales'].loc[filtered_rows, :].groupby('State_y').nunique()[
            [field]]
        state_data.index = state_data.index.str.title().str.replace(' ', '')
        state_data_geo = data['points'].merge(
            state_data, right_index=True, left_on='NAME_1').to_json()

    elif metrics in ['Gross Margin', 'Total COGS', 'Total Revenue']:
        table_data = data['sales'].groupby('Product', dropna=False).sum(
            numeric_only=True).sort_values(by=field, ascending=False)[[field]]
        indx = table_data.index[:top_num]
        filtered_rows = data['sales']['Product'].apply(lambda x: x in indx)
        bar_data = data['sales'].loc[filtered_rows, :].groupby(
            'Industry', dropna=False).sum(numeric_only=True).sort_values(by=field)[[field]]
        line_data = data['sales'].loc[filtered_rows, :].groupby(
            ['Year', 'Qtr', 'Month'], dropna=False, observed=True).sum(numeric_only=True)[[field]]
        state_data = data['sales'].loc[filtered_rows, :].groupby(
            'State_y').sum(numeric_only=True)[[field]]
        state_data.index = state_data.index.str.title().str.replace(' ', '')
        state_data_geo = data['points'].merge(
            state_data, right_index=True, left_on='NAME_1').to_json()

    elif metrics == 'Gross Margin %':
        table_data = data['sales'].groupby('Product', dropna=False).sum(
            numeric_only=True)[['Revenue', 'Gross Margin']]
        table_data[field] = table_data['Gross Margin'] / \
            table_data['Revenue']
        table_data = table_data.sort_values(by=field, ascending=False)[
            [field]]
        indx = table_data.index[:top_num]
        filtered_rows = data['sales']['Product'].apply(lambda x: x in indx)

        bar_data = data['sales'].loc[filtered_rows, :].groupby(
            'Industry', dropna=False).sum(numeric_only=True)
        bar_data[field] = bar_data['Gross Margin'] / bar_data['Revenue']
        bar_data = bar_data.sort_values(by=field)[[field]]

        line_data = data['sales'].loc[filtered_rows, :].groupby(
            ['Year', 'Qtr', 'Month'], dropna=False, observed=True).sum(numeric_only=True)
        line_data[field] = line_data['Gross Margin'] / line_data['Revenue']
        line_data = line_data[[field]]

        state_data = data['sales'].loc[filtered_rows, :].groupby(
            'State_y').sum(numeric_only=True)
        state_data[field] = state_data['Gross Margin'] / \
            state_data['Revenue']
        state_data = state_data[[field]]
        state_data.index = state_data.index.str.title().str.replace(' ', '')
        state_data_geo = data['points'].merge(
            state_data, right_index=True, left_on='NAME_1').to_json()

    return {'table': table_data, 'line': line_data, 'bar': bar_data,
            'map': {'patches': us_df_json, 'points': state_data_geo}}


data = load_plotting_data(top_num, metrics)
field = fields[metrics]

# source = bm.ColumnDataSource(data_selected)
source_table = bm.ColumnDataSource(data['table'])
source_bar = bm.ColumnDataSource(data['bar'])
source_line = bm.ColumnDataSource(data['line'])
source_map_patches = bm.GeoJSONDataSource(geojson=data['map']['patches'])
source_map_points = bm.GeoJSONDataSource(geojson=data['map']['points'])

# Table chart
columns = [
    bm.TableColumn(field='Product', title='Product'),
    bm.TableColumn(field=field, title='Value')]
chart_table = bm.DataTable(
    columns=columns, source=source_table,
    width=250, height=150,
    index_position=None,
    view=bm.CDSView(filter=bm.IndexFilter(list(range(top_num)))))

# Line chart
chart_line = bp.figure(width=700, height=250,
                       x_range=bm.FactorRange(
                           *source_line.data['Year_Qtr_Month'], group_padding=0, subgroup_padding=0),
                       tooltips=[("Month", "@Year_Qtr_Month"), ("Value", f"@{{{field}}}")])
chart_line.line(x='Year_Qtr_Month', y=field, source=source_line)

# Bar chart
chart_bar = bp.figure(width=350, height=500, y_range=source_bar.data['Industry'],
                      tooltips=[("Industry", "@Industry"), ("Value", f"@{{{field}}}")])
chart_bar.hbar(y='Industry', right=field, source=source_bar,
               line_color='white')

# Map chart
chart_map = bp.figure(x_range=(-14000000, -7000000), y_range=(2700000, 6400000),
                      width=600, height=300,
                      x_axis_type="mercator", y_axis_type="mercator"
                      )

chart_map.add_tile("CartoDB Positron", retina=True)
chart_map.patches(xs='xs', ys='ys', source=source_map_patches,
                  line_color='gray', fill_alpha=0)

scale = {
    '# of Customers': 15,
    'Gross Margin': 1/100,
    'Gross Margin %': 50,
    'Total COGS': 1/100,
    'Total Revenue': 1/100}

v_func = f'''
const norm = new Float64Array(xs.length)
for (let i = 0; i < xs.length; i++) {{
    norm[i] = Math.sqrt(xs[i] / Math.PI)*{scale[metrics]};
}}
return norm
'''

js_trans = bm.CustomJSTransform(v_func=v_func)
r1 = chart_map.circle(x='x', y='y', size=bt.transform(field, js_trans),
                      source=source_map_points)
tooltip = bm.HoverTool(
    tooltips=[("State", "@NAME_1"), ("Value", f"@{{{field}}}")], renderers=[r1])
chart_map.add_tools(tooltip)

chart_map.grid.grid_line_color = None
chart_map.axis.axis_line_color = None
chart_map.axis.major_tick_line_color = None
chart_map.axis.minor_tick_line_color = None
chart_map.axis.major_label_text_color = None

# for reference https://geopandas.org/en/stable/gallery/plotting_basemap_background.html#Matching-coordinate-systems
col1, col2 = st.columns([2, 3])

with col1:
    st.markdown(f'### {metrics} for Top {top_num} Products')
    st.markdown('Aug 2013 - Nov 2014')
    st.bokeh_chart(chart_table, use_container_width=True)
    st.markdown(f'Total: {45}')

with col2:
    st.markdown(f'### {metrics} for Top {top_num} Over Time')
    st.markdown('Aug 2013 - Nov 2014')
    st.bokeh_chart(chart_line, use_container_width=True)


col3, col4 = st.columns([2, 3])

with col3:
    st.markdown(f'### {metrics} by Industry for Top {top_num} Products')
    st.markdown('Aug 2013 - Nov 2014')
    st.bokeh_chart(chart_bar, use_container_width=True)

with col4:
    st.markdown(f'### {metrics} by State for Top {top_num} Products')
    st.markdown('Aug 2013 - Nov 2014')
    st.bokeh_chart(chart_map, use_container_width=True)
