import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import urllib

from factory_simulation import *


def main():

    with st.sidebar.form(key="my_form"):
        use_default_params = parameter_ui()

        submit_button = st.form_submit_button(label="Run simulation")

        if submit_button:
            # Create a text element and let the reader know the data is loading.
            data_load_state = st.text("Running simulation...")
            mes = load_simulation()
            # Notify the reader that the data was successfully loaded.
            data_load_state.text("Running simulation...done.")

    with st.expander("🌄 Introduction", expanded=True):
        welcome_message = st.markdown(get_file_content_as_string("welcome_message.md"))
    with st.expander("📄 MES history"):
        st.title("MES History")
        st.write(
            """The **MES history** table contains a row for each step that a lot has finished. Note how there are no `NULL` values under `process_end_time`.
        \nThis table also contains various cycle time calculations."""
        )
        try:
            st.write(mes.hist)
        except UnboundLocalError:
            st.error("Run the simulation to continue.")
    with st.expander("📄 MES current state"):
        st.title("MES Current State")
        st.write(
            """The **MES current** table contains the current state of lots in the factory.
        \nLots in this table are either:

        1. In queue to process at a step.
        2. Being processed at the step. 

        \nNote how lots in this table have at least one `NULL` value .
        """
        )
        try:
            st.write(mes.current)
        except UnboundLocalError:
            st.error("Run the simulation to continue.")
    with st.expander("📊 Cycle time by step"):
        try:
            fig = px.histogram(
                mes.hist,
                x="queue_time_hours",
                y="queue_time_hours",
                color="step_name",
                marginal="box",  # or violin, rug
                hover_data=mes.hist.columns,
                title=f"Queue Time Distribution",
            )
            st.plotly_chart(fig)

            fig = px.histogram(
                mes.hist,
                x="process_time_hours",
                y="process_time_hours",
                color="step_name",
                marginal="box",  # or violin, rug
                hover_data=mes.hist.columns,
                title=f"Process Time Distribution",
            )
            st.plotly_chart(fig)

            fig = px.histogram(
                mes.hist,
                x="step_cycle_time_hours",
                y="step_cycle_time_hours",
                color="step_name",
                marginal="box",  # or violin, rug
                hover_data=mes.hist.columns,
                title=f"Step Cycle Time Distribution",
            )
            st.plotly_chart(fig)
        except UnboundLocalError:
            st.error("Run the simulation to continue.")


def parameter_ui():
    st.sidebar.title("Simulation Parameters")
    use_default_params = st.sidebar.checkbox(
        label="Use defaults",
        value=True,
        help="Deselect to set these parameters yourself.",
    )

    if not use_default_params:
        interarrival_time_scale = st.sidebar.slider(
            "Mean interarrival time (hours)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.1,
            help="""
            Random arrivals can be modeled with an exponential distribution. In this case, we are assuming that arrivals to the factory (in the form of orders) are independent of one another.

            The scale parameter, λ, for an exponential distribution is equal to both the mean and std dev.
            """,
        )
    return use_default_params


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
