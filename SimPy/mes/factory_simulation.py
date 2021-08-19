import random
import pandas as pd
import simpy


def _generate_lot_id():
    """Generator that assigns an incremental number to each lot, starting with lot_id = 1.
    """
    lot_id = 1
    while True:
        yield lot_id
        lot_id += 1


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

    lot_id = _generate_lot_id()

    process_time = [["STEP A", 1], ["STEP B", 2], ["STEP C", 3], ["STEP D", 4]]
    num_machines_at_ws = [{"ws1": 1}, {"ws2": 1}, {"ws3": 1}]

    # List of steps is set dynamically from process_time
    steps = [step[0] for step in process_time]


class Factory(object):
    """Holds the workstation(s) (i.e., SimPy Resource) and step that at which each Lot will be processed.
    """

    def __init__(self, env):
        """Constructor for initiating SimPy simulation environment.
        """
        self.env = env

    def step(self, lot):
        """A Lot runs at a step for the amount of time set by process_time.
        """
        yield self.env.timeout(GlobalVars.process_time[lot.step_sequence_number][1])


class Lot(object):
    """Holds variables specific to each Lot instance as it flows through steps in the Factory.
    """

    def __init__(self):
        self.lot_id = next(GlobalVars.lot_id)
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
                    "step_name": GlobalVars.process_time[lot.step_sequence_number][0],
                    "step_arrival_time": env.now,
                },
                index=lot.index,
            ),
        ]
    )

    with factory.ws1.request() as request:
        insert_datetime_for(
            env, lot, "step_arrival_time"
        )  # The lot gets in queue for the first process.
        yield request
        insert_datetime_for(
            env, lot, "process_start_time"
        )  # After yield, the lot begins the process.
        yield env.process(factory.step(lot))
        insert_datetime_for(
            env, lot, "process_end_time"
        )  # After yield, the lot has finished processing.

    lot.step_sequence_number += 1
    env.process(continue_lot(env, lot, factory))


def continue_lot(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws2
    GlobalVars.lot_status_df = pd.concat(
        [
            GlobalVars.lot_status_df,
            pd.DataFrame(
                {
                    "lot_id": lot.lot_id,
                    "step_name": GlobalVars.process_time[lot.step_sequence_number][0],
                    "step_arrival_time": env.now,
                },
                index=lot.index,
            ),
        ]
    )

    with factory.ws2.request() as request:
        insert_datetime_for(
            env, lot, "step_arrival_time"
        )  # The lot gets in queue for the first process.
        yield request
        insert_datetime_for(
            env, lot, "process_start_time"
        )  # After yield, the lot begins the process.
        yield env.process(factory.step(lot))
        insert_datetime_for(
            env, lot, "process_end_time"
        )  # After yield, the lot has finished processing.

    lot.step_sequence_number += 1
    env.process(continue_lot(env, lot, factory))


def run_factory(env, lots_ready_at_time_zero=3, interarrival_time=2):
    factory = Factory(env)

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
        yield env.timeout(interarrival_time)
        env.process(
            start_lot(env, Lot(), factory)
        )  # After yield, a new Lot arrives at the factory.


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

    MES = namedtuple("mes", ["hist", "current"])
    mes = MES(
        mes_data[~mes_data["process_end_time"].isna()].copy(),
        mes_data[mes_data["process_end_time"].isna()].copy(),
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

