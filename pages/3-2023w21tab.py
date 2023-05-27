import streamlit as st
import plotly.express as px
import pandas as pd

file_path = "./data/Superstore with Target Profit WOW2023 W21.xlsx"


@st.cache_data
def load_data(file_path):
    data = pd.read_excel(file_path)
    data_grouped = (
        data[data["Order Date"].dt.year == 2023]
        .groupby(data["Order Date"].dt.month)
        .sum(numeric_only=True)
    )
    return data_grouped


# Initialize state
if "tval" not in st.session_state:
    st.session_state["tval"] = 0.05

# Widgets
st.set_page_config(layout="wide", page_title="#WOW2023 Week 21")

col1, col2 = st.columns([4, 1])

with col2:
    st.text(f"Tolerance:\nPercent Around Target\n{st.session_state.tval:.0%}")
    tolerance = st.slider(
        "Percent Around Target",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        label_visibility="collapsed",
        key="tval",
    )

col1.markdown(
    f"## #WOW2023 Week 21 | 2023 Profit vs Target (with {tolerance:.0%} tolerance)"
)

# Figure
data_grouped = load_data(file_path)
lower = data_grouped["Target Profit"] * (1 - tolerance)
upper = data_grouped["Target Profit"] * (1 + tolerance)
labels = [
    "Above Target" if p > u else ("Below Target" if p < l else "On Target")
    for p, l, u in zip(data_grouped["Profit"], lower, upper)
]

data_px = data_grouped.reset_index()
data_px["labels"] = labels
data_px["month"] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
data_px["profit diff"] = (data_px["Profit"] - data_px["Target Profit"]) / data_px[
    "Target Profit"
]
color_maps = {
    "Above Target": "#91B3D7",
    "On Target": "#BAB0AC",
    "Below Target": "#E15759",
}

fig = px.bar(
    data_px,
    x="Order Date",
    y="Profit",
    color="labels",
    color_discrete_map=color_maps,
)  # This includes three traces

# We need to update the customdata for each traces of different colors
for l, c in color_maps.items():
    fig.update_traces(
        selector=dict(marker_color=c),
        customdata=data_px.loc[
            :, ["month", "Profit", "profit diff", "Target Profit", "labels"]
        ].query("labels==@l"),
        hovertemplate=(
            "<b>%{customdata[0]} 2023</b><br>"
            "Profit: <b>$%{customdata[1]:,.0f}</b><br>"
            "%{customdata[2]:.0%} difference from Target ($%{customdata[3]:,.0f})<extra></extra>"
        ),
        hoverlabel=dict(bgcolor="white", font_size=14),
    )

for m, t, l, u in zip(data_px["Order Date"], data_px["Target Profit"], lower, upper):
    fig.add_shape(type="line", x0=m - 0.4, y0=t, x1=m + 0.4, y1=t, line_color="gray")
    fig.add_shape(
        type="rect",
        x0=m - 0.5,
        y0=l,
        x1=m + 0.5,
        y1=u,
        line_color="gray",
        fillcolor="gray",
        opacity=0.3,
        layer="below",
    )

fig.update_layout(
    # paper_bgcolor='yellow',
    width=900,
    height=600,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        xanchor="left",
        x=0,
        y=1,
        title_text="",
        font_size=16,
    ),
    # margin=dict(b=5, t=5, l=5, r=10),
)
fig.update_xaxes(
    tickvals=data_px["Order Date"],
    ticktext=data_px["month"],
    title_text="",
    tickfont_size=16,
)
fig.update_yaxes(title_text="", tickfont_size=16)

fig.add_annotation(
    text="Workout Wednesday Week 21 | Challenge by L-ZY @LZY_CHN",
    x=1,
    y=0,
    yshift=-30,
    xref="paper",
    yref="paper",
    xanchor="right",
    yanchor="top",
    showarrow=False,
    font=dict(color="gray", size=12),
    opacity=0.8,
)

col1.plotly_chart(fig, use_container_width=True)
