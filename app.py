import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import urllib

from factory_simulation import *


def main():

    with st.sidebar.form(key="my_form"):
        st.sidebar.title("Navigation")
        app_mode = st.sidebar.selectbox(
            "Select a page to view",
            [
                "🌄 Introduction",
                "📄 MES history",
                "📄 MES current state",
                "📊 Cycle time by step",
            ],
        )
        use_default_params = st.sidebar.checkbox(
            label="Use default factory parameters",
            value=True,
            help="Deselect to set these parameters yourself.",
        )

        submit_button = st.form_submit_button(label="Run simulation")

        if submit_button:
            # Create a text element and let the reader know the data is loading.
            data_load_state = st.text("Running simulation...")
            if use_default_params:
                mes = load_simulation()
            else:
                mes = load_simulation()
            # Notify the reader that the data was successfully loaded.
            data_load_state.text("Running simulation...done.")

    # Pages
    if app_mode == "🌄 Introduction":
        welcome_message = st.markdown(get_file_content_as_string("welcome_message.md"))
    elif app_mode == "📄 MES history":
        st.title("MES History")
        st.write(
            """The **MES history** table contains a row for each step that a lot has finished. Note how there are no `NULL` values under `process_end_time`.
        \nThis table also contains various cycle time calculations."""
        )
        st.write(mes.hist)
    elif app_mode == "📄 MES current state":
        st.title("MES Current State")
        st.write(
            """The **MES current** table contains the current state of lots in the factory.
        \nLots in this table are either:

        1. In queue to process at a step.
        2. Being processed at the step. 

        \nNote how this table always has at least one `NULL` value .
        """
        )
        st.write(mes.current)
    elif app_mode == "📊 Cycle time by step":
        option = st.selectbox(
            "Cycle time component:", ("Queue Time", "Process Time", "Step Cycle Time")
        )
        option_to_column = {
            "Queue Time": "queue_time_hours",
            "Process Time": "process_time_hours",
            "Step Cycle Time": "step_cycle_time_hours",
        }
        fig = px.histogram(
            mes.hist,
            x=option_to_column[option],
            y=option_to_column[option],
            color="step_name",
            marginal="box",  # or violin, rug
            hover_data=mes.hist.columns,
            title=f"{option} Distribution",
        )
        st.plotly_chart(fig)


def load_simulation(
    interarrival_time_scale=2,
    lots_ready_at_time_zero=3,
    random_seed=42,
    simulation_hours=50,
):
    np.random.seed(random_seed)
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
    env.run(until=simulation_hours)

    mes = create_mes_data(simulation_start_time=(2021, 1, 1))
    return mes


@st.cache(show_spinner=False)
def get_file_content_as_string(path):
    url = "https://raw.githubusercontent.com/chrisschopp/mes/master/" + path
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")


if __name__ == "__main__":
    main()
