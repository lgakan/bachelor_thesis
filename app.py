from datetime import datetime
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib.logger import logger
from scripts.system import SmartSystem


@st.cache_data
def interactive_plot(df: pd.DataFrame):
    x_value = df.pop("Date")
    fig = make_subplots(rows=len(df.columns), cols=1)
    for idx, y_col in enumerate(df.columns):
        fig.add_trace(go.Scatter(x=x_value, y=df[y_col], name=y_col), row=idx + 1, col=1)
    fig.update_layout(title="Smart System", autosize=False, width=2000, height=1350)
    st.plotly_chart(fig, use_container_width=True)


# st.set_page_config(page_title="RES", page_icon=":bar_chart:", layout="wide")
st.set_page_config(page_title="RES", page_icon=":bar_chart:")

st.title("Energy Management System")
st.markdown("_Prototype v0.4.1_")

with st.sidebar:
    date_start = datetime.strptime("04.09.2020 05:00:00", "%d.%m.%Y %H:%M:%S")
    date_end = datetime.strptime("04.09.2020 12:00:00", "%d.%m.%Y %H:%M:%S")
    date_earliest = datetime.strptime("01.09.2020 05:00:00", "%d.%m.%Y %H:%M:%S")
    date_oldest = datetime.strptime("20.09.2020 12:00:00", "%d.%m.%Y %H:%M:%S")
    date_start, date_end = st.slider("Date range",
                                     min_value=date_earliest,
                                     max_value=date_oldest,
                                     value=[date_start, date_end])
    energy_bank_max_lvl = st.number_input("Energy bank max lvl:", min_value=0.0, max_value=5.0, value=3.0)

with st.container():
    with st.expander("Chosen System Info"):
        st.write(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Molestie a iaculis at erat pellentesque adipiscing commodo elit at. Id venenatis a condimentum vitae. Felis donec et odio pellentesque diam volutpat. Diam phasellus vestibulum lorem sed risus. Turpis egestas sed tempus urna et pharetra pharetra. Commodo quis imperdiet massa tincidunt nunc. Diam vulputate ut pharetra sit amet aliquam id. Gravida neque convallis a cras. Porttitor lacus luctus accumsan tortor.")

    smart_system = SmartSystem()
    st.write(SmartSystem.__name__)
    for current_date in pd.date_range(start=date_start, end=date_end, freq=timedelta(hours=1)):
        logger.info(f"CURRENT DATE: {current_date}")
        smart_system.feed_consumption(current_date)

    st.write(f"TOTAL: {smart_system.summed_cost:.2}")
    x = smart_system.plot_charts()
    print(x)
    interactive_plot(x)
