import numpy as np
import pandas as pd
import simpy


def _generate_lot_id():
    """Generator that assigns an incremental number to each lot,
    starting with lot_id = 1.
    """
    lot_id = 1
    while True:
        yield lot_id
        lot_id += 1


_lot_id = _generate_lot_id()


def _generate_interarrival_time(scale):
    """When called, returns the time until the next lot arrives
    at the factory.

    The scale parameter is passed to the exponential distribution,
    where it is equal to the mean and standard deviation.
    """
    while True:
        yield np.random.exponential(scale)


def _sample_from_gamma_distribution(shape, scale):
    while True:
        yield np.random.default_rng().gamma(shape, scale)


class GlobalVars:
    """Holds variables needed by other classes.
    """

    lot_status_df = pd.DataFrame(
        columns=[
            "lot_id",
            "step_name",
            "step_arrival_time",
            "process_start_time",
            "process_end_time",
        ]
    )

    step_list = [
        {
            "step_name": "STEP A",
            "process_time": _sample_from_gamma_distribution(shape=4, scale=1.0),
        },
        {
            "step_name": "STEP B",
            "process_time": _sample_from_gamma_distribution(shape=4, scale=0.5),
        },
        {
            "step_name": "STEP C",
            "process_time": _sample_from_gamma_distribution(shape=4, scale=2.0),
        },
        {
            "step_name": "STEP D",
            "process_time": _sample_from_gamma_distribution(shape=4, scale=0.7),
        },
    ]

    num_machines_at_ws = [{"ws1": 2}, {"ws2": 4}, {"ws3": 4}]

    # List of steps is set dynamically from process_time
    steps = [step["step_name"] for step in step_list]


class Factory(object):
    """Holds the workstation(s) (i.e., SimPy Resource) and step that
    at which each Lot will be processed.
    """

    def __init__(self, env):
        """Constructor for initiating SimPy simulation environment.
        """
        self.env = env

    def step(self, lot):
        """A Lot runs at a step for the amount of time set in process_time.
        """
        yield self.env.timeout(
            next(GlobalVars.step_list[lot.step_sequence_number]["process_time"])
        )


class Lot(object):
    """Holds variables specific to each Lot instance as it flows through
    steps in the Factory.
    """

    def __init__(self):
        self.lot_id = next(_lot_id)
        self.step_sequence_number = 0


def insert_datetime_for(env, lot, lot_event):
    """Inserts event datetimes into the lot_status_df.
    
    Examples of events would be 'step_arrival_time',
    'process_start_time', and 'process_end_time'.
    """
    GlobalVars.lot_status_df.at[lot.index, str(lot_event)] = env.now


def start_lot(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws1
    # The first step has a step_arrival_time of when the lot was created.
    GlobalVars.lot_status_df = pd.concat(
        [
            GlobalVars.lot_status_df,
            pd.DataFrame(
                {
                    "lot_id": lot.lot_id,
                    "step_name": GlobalVars.step_list[lot.step_sequence_number][
                        "step_name"
                    ],
                    "step_arrival_time": env.now,
                },
                index=lot.index,
            ),
        ]
    )

    with factory.ws1.request() as request:
        # The lot gets in queue for the first process.
        insert_datetime_for(env, lot, "step_arrival_time")
        yield request
        # After yield, the lot begins the process.
        insert_datetime_for(env, lot, "process_start_time")
        yield env.process(factory.step(lot))
        # After yield, the lot has finished processing.
        insert_datetime_for(env, lot, "process_end_time")

    lot.step_sequence_number += 1
    env.process(lot_at_step_b(env, lot, factory))


def lot_at_step_b(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws2
    GlobalVars.lot_status_df = pd.concat(
        [
            GlobalVars.lot_status_df,
            pd.DataFrame(
                {
                    "lot_id": lot.lot_id,
                    "step_name": GlobalVars.step_list[lot.step_sequence_number][
                        "step_name"
                    ],
                    "step_arrival_time": env.now,
                },
                index=lot.index,
            ),
        ]
    )

    with factory.ws2.request() as request:
        # The lot gets in queue for the first process.
        insert_datetime_for(env, lot, "step_arrival_time")
        yield request
        # After yield, the lot begins the process.
        insert_datetime_for(env, lot, "process_start_time")
        yield env.process(factory.step(lot))
        # After yield, the lot has finished processing.
        insert_datetime_for(env, lot, "process_end_time")

    lot.step_sequence_number += 1
    env.process(lot_at_step_c(env, lot, factory))


def lot_at_step_c(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws3
    GlobalVars.lot_status_df = pd.concat(
        [
            GlobalVars.lot_status_df,
            pd.DataFrame(
                {
                    "lot_id": lot.lot_id,
                    "step_name": GlobalVars.step_list[lot.step_sequence_number][
                        "step_name"
                    ],
                    "step_arrival_time": env.now,
                },
                index=lot.index,
            ),
        ]
    )

    with factory.ws3.request() as request:
        # The lot gets in queue for the first process.
        insert_datetime_for(env, lot, "step_arrival_time")
        yield request
        # After yield, the lot begins the process.
        insert_datetime_for(env, lot, "process_start_time")
        yield env.process(factory.step(lot))
        # After yield, the lot has finished processing.
        insert_datetime_for(env, lot, "process_end_time")

    lot.step_sequence_number += 1
    env.process(lot_at_step_d(env, lot, factory))


def lot_at_step_d(env, lot, factory):
    # Last step does not increment lot.step_sequence_number at the end.
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws2
    GlobalVars.lot_status_df = pd.concat(
        [
            GlobalVars.lot_status_df,
            pd.DataFrame(
                {
                    "lot_id": lot.lot_id,
                    "step_name": GlobalVars.step_list[lot.step_sequence_number][
                        "step_name"
                    ],
                    "step_arrival_time": env.now,
                },
                index=lot.index,
            ),
        ]
    )

    with factory.ws2.request() as request:
        # The lot gets in queue for the first process.
        insert_datetime_for(env, lot, "step_arrival_time")
        yield request
        # After yield, the lot begins the process.
        insert_datetime_for(env, lot, "process_start_time")
        yield env.process(factory.step(lot))
        # After yield, the lot has finished processing.
        insert_datetime_for(env, lot, "process_end_time")


def run_factory(env, lots_ready_at_time_zero=3, interarrival_time=2):
    factory = Factory(env)
    _lot_arrival = _generate_interarrival_time(interarrival_time)

    # Sets num_machines_at_ws dynamically.
    for ws in GlobalVars.num_machines_at_ws:
        ws_name = list(ws.keys())[0]
        num_machines_in_ws = simpy.Resource(env, capacity=list(ws.values())[0])
        setattr(Factory, ws_name, num_machines_in_ws)

    # The factory starts with some number of lots ready to start processing at the first step.
    for _ in range(lots_ready_at_time_zero):
        env.process(start_lot(env, Lot(), factory))

    # The factory receives new lots according the the interarrival_time.
    while True:
        yield env.timeout(next(_lot_arrival))
        # After yield, a new Lot arrives at the factory.
        env.process(start_lot(env, Lot(), factory))


def get_cycle_time_hours(df):
    """Returns a DataFrame of 
    """
    first_step = df[df["step_name"] == GlobalVars.steps[0]]
    last_step = df[df["step_name"] == GlobalVars.steps[-1]]

    merged = first_step.merge(
        last_step, left_on="lot_id", right_on="lot_id", suffixes=["_first", "_last"]
    )
    merged["cycle_time_hours"] = (
        merged["process_end_time_last"] - merged["step_arrival_time_first"]
    ) / pd.Timedelta(hours=1)

    return merged[["lot_id", "cycle_time_hours"]]


def create_mes_data(simulation_start_time):
    """Creates a namedtuple storing mes data from the simulation. 

    Returns:
        mes: namedtuple with attributes for mes.hist and mes.current.
    """

    from collections import namedtuple

    mes_data = GlobalVars.lot_status_df.copy()
    year, month, day = simulation_start_time

    # Convert simulation minutes to datetimes starting at simulation_start_time.
    # Converts unit time to hours so we have a longer time period
    simulation_start_time = pd.Timestamp(year=year, month=month, day=day)
    for event in ["step_arrival_time", "process_start_time", "process_end_time"]:
        mes_data[event] = simulation_start_time + pd.to_timedelta(
            mes_data[event], unit="h"
        )

    MES = namedtuple("mes", ["hist", "current", "cycle_time"])
    mes = MES(
        mes_data[~mes_data["process_end_time"].isna()].copy(),
        mes_data[mes_data["process_end_time"].isna()].copy(),
        get_cycle_time_hours(mes_data[~mes_data["process_end_time"].isna()].copy()),
    )

    mes.hist["queue_time_hours"] = (
        mes.hist["process_start_time"] - mes.hist["step_arrival_time"]
    ) / pd.Timedelta(hours=1)
    mes.hist["process_time_hours"] = (
        mes.hist["process_end_time"] - mes.hist["process_start_time"]
    ) / pd.Timedelta(hours=1)
    mes.hist["step_cycle_time_hours"] = (
        mes.hist["process_end_time"] - mes.hist["step_arrival_time"]
    ) / pd.Timedelta(hours=1)

    return mes

