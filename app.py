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


st.set_page_config(page_title="RES", page_icon=":bar_chart:")
st.title("Energy Management System")

with st.form("my_form"):
    date_start = datetime.strptime("04.09.2020 05:00:00", "%d.%m.%Y %H:%M:%S")
    date_end = datetime.strptime("04.09.2020 12:00:00", "%d.%m.%Y %H:%M:%S")
    date_earliest = datetime.strptime("01.09.2020 05:00:00", "%d.%m.%Y %H:%M:%S")
    date_oldest = datetime.strptime("10.09.2020 12:00:00", "%d.%m.%Y %H:%M:%S")
    date_start, date_end = st.slider("Date range",
                                     min_value=date_earliest,
                                     max_value=date_oldest,
                                     value=[date_start, date_end])
    energy_bank_max_lvl = st.number_input("Energy bank max lvl:", min_value=0.0, max_value=5.0, value=3.0)
    day_algorithm_choice = st.selectbox("Chose a day algorithm", ("full_bank", "interval"))
    with st.expander("Info about day algorithms"):
        st.markdown("""##### *full_bank* \n\n _The priority of this algorithm is to ensure the maximum energy bank level
                    during the day. If consumption exceeds production, and there's a need to source additional energy, 
                    the system will prefer to purchase it. It will only use the energy bank when it is certain that it 
                    will be fully charged by the end of the day.This algorithm works best when prices fluctuate 
                    unpredictably._""")
        st.markdown("""##### *interval* \n\n _The goal of the algorithm is to utilize the time between the appearance of 
                    energy prices for a new day and sunset (the moment when photovoltaic production stops). During this 
                    period, system calculates the optimal plan for using energy from the energy bank until the next 
                    morning. This algorithm is particularly effective during the summer when sunset occurs later._""")

    submitted = st.form_submit_button("Run!")
    if submitted:
        smart_system = SmartSystem()
        for current_date in pd.date_range(start=date_start, end=date_end, freq=timedelta(hours=1)):
            logger.info(f"CURRENT DATE: {current_date}")
            smart_system.feed_consumption(current_date)

with st.container():
    try:
        st.write(f"TOTAL: {smart_system.summed_cost:.2}")
        df_to_plot = smart_system.plot_charts()
        interactive_plot(df_to_plot)
    except:
        st.info('Click "Run!" button run the system!')
        st.stop()
