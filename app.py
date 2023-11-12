import copy
from datetime import datetime
from datetime import timedelta
from typing import List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib.logger import logger
from scripts.system import BareSystem, PvSystem, RawFullSystem, SmartSystem, SmartSaveSystem


@st.cache_data
def interactive_plot(df: pd.DataFrame):
    x_value = df.pop("Date")
    fig = make_subplots(rows=len(df.columns), cols=1)
    for idx, y_col in enumerate(df.columns):
        fig.add_trace(go.Scatter(x=x_value, y=df[y_col], name=y_col), row=idx + 1, col=1)
    fig.update_layout(autosize=False, width=2000, height=1350)
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data
def plot_total(df_list: List[pd.DataFrame]):
    x_value = list(df_list[0]["Date"])
    y_values = [list(val["Total price [zl]"]) for val in df_list]
    columns = ["Date", "Bare", "Pv", "Raw", "Smart", "SaveSmart"]
    chart_data = pd.DataFrame({k: v for k, v in zip(columns, [x_value] + y_values)})
    st.line_chart(chart_data, x="Date", y=columns[1:])


st.set_page_config(page_title="RES", page_icon=":bar_chart:")
st.title("Energy Management System")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    eb_capacity = st.number_input("Energy bank capacity:", min_value=3.0, max_value=10.0, value=3.0)
with col2:
    eb_cost = st.number_input("Energy bank cost [zl]:", min_value=0.0, step=1.0, value=500.0)
with col3:
    eb_cycles = st.number_input("Energy bank cycles:", min_value=0, value=500)
with col4:
    eb_min_lvl = st.number_input("Energy bank min value:", min_value=0.0, max_value=eb_capacity / 2, value=1.0)
with col5:
    eb_start_lvl = st.number_input("Energy bank start lvl:", min_value=eb_min_lvl, max_value=eb_capacity, value=eb_min_lvl)

col1, col2 = st.columns(2)
with col1:
    pv_size = st.number_input("Photovoltaics installation size:", min_value=0.0, max_value=10.0, step=1.0, value=5.0)
with col2:
    load_multiplier = st.number_input("Load multiplier:", min_value=0.5, max_value=2.0, step=0.1, value=1.0)

with st.form("my_form"):
    date_start = datetime.strptime("04.09.2020 05:00:00", "%d.%m.%Y %H:%M:%S")
    date_end = datetime.strptime("04.09.2020 12:00:00", "%d.%m.%Y %H:%M:%S")
    date_earliest = datetime.strptime("01.09.2020 05:00:00", "%d.%m.%Y %H:%M:%S")
    date_oldest = datetime.strptime("10.09.2020 12:00:00", "%d.%m.%Y %H:%M:%S")
    date_start, date_end = st.slider("Date range", min_value=date_earliest, max_value=date_oldest, value=[date_start, date_end])
    with st.expander("Info about smart systems"):
        st.markdown("""##### *SmartSystem* \n\n _The operation of this system is divided into two phases: day and night.
                    At the beginning of the nighttime period, the system optimally allocates the projected energy demand
                     for that period (first satisfying consumption during the most expensive hours). In the case of the 
                     daytime period, the system dynamically calculates the optimal actions of buying, selling, or 
                     storing the generated energy. The advantage is resistance to negative prices, while the disadvantage 
                     is the continuous operation of the energy bank, which may lead to faster wear and tear._""")
        st.markdown("""##### *SmartSaveSystem* \n\n _The system relies on maximizing the lifespan of the energy bank. 
                    Decisions regarding the purchase, sale, and storage of energy are made based on the profitability of 
                    such operations. Profitability is calculated based on the average purchase/sale price of energy from 
                    a given period (night or day) combined with the cost of operations in the energy bank. The advantage 
                    is the efficient operation of the energy bank, while the disadvantage is the lack of resistance to 
                    negative energy prices._""")

    submitted = st.form_submit_button("Run!")
    if submitted:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Bare", "pv", "full_raw", "smart", "save_smart", "summary"])
        bare_system = BareSystem(load_multiplier=load_multiplier)
        pv_system = PvSystem(pv_size=pv_size, load_multiplier=load_multiplier)
        raw_full_system = RawFullSystem(eb_capacity=eb_capacity, eb_min_lvl=eb_min_lvl, eb_start_lvl=eb_start_lvl,
                                        eb_purchase_cost=eb_cost, eb_cycles=eb_cycles, pv_size=pv_size,
                                        load_multiplier=load_multiplier)
        smart_system = SmartSystem(eb_capacity=eb_capacity, eb_min_lvl=eb_min_lvl, eb_start_lvl=eb_start_lvl,
                                   eb_purchase_cost=eb_cost, eb_cycles=eb_cycles, pv_size=pv_size,
                                   load_multiplier=load_multiplier)
        smart_save_system = SmartSaveSystem(eb_capacity=eb_capacity, eb_min_lvl=eb_min_lvl, eb_start_lvl=eb_start_lvl,
                                            eb_purchase_cost=eb_cost, eb_cycles=eb_cycles, pv_size=pv_size,
                                            load_multiplier=load_multiplier)
        for current_date in pd.date_range(start=date_start, end=date_end, freq=timedelta(hours=1)):
            logger.info(f"CURRENT DATE: {current_date}")
            bare_system.feed_consumption(current_date)
            pv_system.feed_consumption(current_date)
            raw_full_system.feed_consumption(current_date)
            smart_system.feed_consumption(current_date)
            smart_save_system.feed_consumption(current_date)

with st.container():
    try:
        systems = [bare_system, pv_system, raw_full_system, smart_system, smart_save_system]
        tabs = [tab1, tab2, tab3, tab4, tab5]
        for system, tab in zip(systems, tabs):
            with tab:
                st.write(f"Energy cost: {system.summed_cost:.2}")
                if system in [raw_full_system, smart_system, smart_save_system]:
                    st.write(f"Bank value: {system.energy_bank.lvl * system.energy_pricer.get_rce_by_date(date_end)/1000:.2}")
                df_to_plot = copy.deepcopy(system.plotter.df)
                interactive_plot(df_to_plot)
        with tab6:
            st.write(f"Summary of total costs")
            dfs_to_plot = [s.plotter.df for s in systems]
            plot_total(dfs_to_plot)
    except:
        st.info('Click "Run!" button to run the system!')
        st.stop()
