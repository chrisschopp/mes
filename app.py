import numpy as np
import pandas as pd
import streamlit as st

from factory_simulation import *


def main():
    # Create a text element and let the reader know the data is loading.
    data_load_state = st.text("Running simulation...")
    mes = simulation_config()
    # Notify the reader that the data was successfully loaded.
    data_load_state.text("Running simulation...done.")

    st.sidebar.title("Factory Simulation")
    app_mode = st.sidebar.selectbox(
        "Choose the app mode", ["Instructions", "📄 MES history", "📄 MES current state"],
    )
    if app_mode == "Instructions":
        st.write(welcome_message())
        st.sidebar.success("Select an option above.")
    elif app_mode == "📄 MES history":
        st.write(mes.hist)
    elif app_mode == "📄 MES current state":
        st.write(mes.current)


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
    env.run(until=10)


def welcome_message():
    text = """
    # Factory Simulation

    Welcome to the simulation.
    """
    return text


if __name__ == "__main__":
    main()
