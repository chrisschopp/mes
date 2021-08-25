import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import urllib

from factory_simulation import *


def main():
    # Create a text element and let the reader know the data is loading.
    data_load_state = st.text("Running simulation...")
    mes = simulation_config()
    # Notify the reader that the data was successfully loaded.
    data_load_state.text("Running simulation...done.")

    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox(
        "Choose app mode",
        ["Introduction", "📄 MES history", "📄 MES current state", "📊 Process Time"],
    )
    if app_mode == "Introduction":
        welcome_message = st.markdown(get_file_content_as_string("welcome_message.md"))
        st.sidebar.success("Select an option above.")
    elif app_mode == "📄 MES history":
        st.write(mes.hist)
    elif app_mode == "📄 MES current state":
        st.write(mes.current)
    elif app_mode == "📊 Process Time":
        fig = px.histogram(
            mes.hist,
            x="process_time_hours",
            y="process_time_hours",
            color="step_name",
            marginal="box",  # or violin, rug
            hover_data=mes.hist.columns,
            title="Process Time Distribution by Step",
        )
        st.plotly_chart(fig)


def simulation_config():
    load_simulation(
        interarrival_time_scale=2, lots_ready_at_time_zero=3, random_seed=42
    )
    mes = create_mes_data(simulation_start_time=(2021, 1, 1))
    return mes


def load_simulation(
    interarrival_time_scale=2, lots_ready_at_time_zero=3, random_seed=42
):
    np.random.seed(42)
    interarrival_time = np.random.exponential(
        scale=interarrival_time_scale
    )  # The scale parameter (lambda) for an exponential distribution is equal to both the mean and std dev.

    env = simpy.Environment()
    env.process(
        run_factory(
            env,
            lots_ready_at_time_zero=lots_ready_at_time_zero,
            interarrival_time=interarrival_time,
        )
    )
    env.run(until=50)


@st.cache(show_spinner=False)
def get_file_content_as_string(path):
    url = "https://raw.githubusercontent.com/chrisschopp/mes/master/" + path
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")


if __name__ == "__main__":
    main()
