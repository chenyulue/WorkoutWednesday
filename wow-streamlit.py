import streamlit as st
import numpy as np
import pandas as pd
import bokeh.plotting as bkp
import bokeh.models as bkm

if 'top_num' not in st.session_state:
    st.session_state.top_num = 5

if 'metrics' not in st.session_state:
    st.session_state.metrics = '# of Customers'

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
metrics = st.sidebar.radio('Select Metric', options=metrics_opts, key='metrics')

st.sidebar.divider()

# Chart content

## Manipulate data
@st.cache_data
def get_data(file_path):
    data = pd.read_excel(file_path, sheet_name=None)
    customers = data['customer'].merge(
        data['industry'], left_on='Industry ID', right_on='ID', how='left').merge(
        data['state'], left_on='State', right_on='StateCode', how='left')
    data_customer = data['factsales'].merge(
        data['product'], on='Product Key', how='left').merge(
        customers, left_on='Customer Key', right_on='Customer', how='left').merge(
        data['date'], on='YearPeriod', how='left')
    data_customer['COGS'] = data_customer.iloc[:,range(6, 12)].sum(axis=1)
    data_customer['Gross Margin'] = data_customer['Revenue'] - data_customer['COGS']
    data_selected = data_customer.loc[:, ['YearPeriod', 'Customer Key', 
                                          'Industry', 'Product', 'State_y', 
                                          'COGS', 'Gross Margin', 'Year', 
                                          'Qtr', 'Month']]
    data_selected['Product'] = data_selected['Product'].fillna('<?>')
    data_selected['Industry'] = data_selected['Industry'].fillna('<?>')

    return data_selected
    
@st.cache_resource
def load_data(top_num, metrics):
    data_selected = get_data('./data/Dataset-Customer Profitability.xlsx')
    if metrics == '# of Customers':
        table_data = data_selected.groupby(
            'Product', dropna=False).nunique().sort_values(
                by='Customer Key', ascending=False)[['Customer Key']]
        indx = table_data.index[:(top_num+1)]
        filtered_rows = data_selected['Product'].apply(lambda x: x in indx)
        bar_data = data_selected.loc[filtered_rows, :].groupby(
            'Industry', dropna=False).nunique().sort_values(
                by='Customer Key', ascending=False)[['Customer Key']]
        line_data = data_selected.loc[filtered_rows, :].groupby(
            ['Year', 'Qtr', 'Month'], dropna=False).nunique()[['Customer Key']]
        state_data = data_selected.loc[filtered_rows, :].groupby(
            'State_y').nunique()[['Customer Key']]

    return (bkm.ColumnDataSource(data_selected), 
            bkm.ColumnDataSource(table_data),
            bkm.ColumnDataSource(line_data),
            bkm.ColumnDataSource(bar_data),
            bkm.ColumnDataSource(state_data))

source, source_table, source_line, source_bar, source_map = load_data(
    top_num, metrics)

# Table
@st.cache_resource
def plot_table(_src, top_num):
	columns = [
	        bkm.TableColumn(field="Product", title="Product",),
	        bkm.TableColumn(field="Customer Key", title="Value")]
	data_table = bkm.DataTable(
	    source=_src, 
	    view=bkm.CDSView(filter=bkm.IndexFilter(list(range(top_num)))),
	    columns=columns, width=300, height=150,
	    index_position=None)
	return data_table
	
data_table = plot_table(source_table, top_num)

st.bokeh_chart(data_table)