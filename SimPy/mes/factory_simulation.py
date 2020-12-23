import numpy as np
import pandas as pd
import simpy


def _generate_lot_id():
    '''Generator that assigns an incremental number to each lot, starting with lot_id = 1.
    '''
    lot_id = 1
    while True:
        yield lot_id
        lot_id += 1

_lot_id = _generate_lot_id()

def _generate_interarrival_time(scale):
    '''When called, returns the time until the next lot arrives
    at the factory.

    The scale parameter is passed to the exponential distribution,
    where it is equal to the mean and standard deviation.
    '''
    while True:
        yield np.random.exponential(scale)

def sample_from_gamma_distribution(shape, scale):
    while True:
        yield np.random.default_rng().gamma(shape, scale)

class GlobalVars:
    '''Holds variables needed by other classes.
    '''
    lot_status_df = pd.DataFrame(columns=['lot_id', 'step_name', 'step_arrival_time', 'process_start_time', 'process_end_time'])

    step_process_time = [['STEP A', sample_from_gamma_distribution(shape=4, scale=1.0)],
                        ['STEP B', sample_from_gamma_distribution(shape=4, scale=0.5)],
                        ['STEP C', sample_from_gamma_distribution(shape=4, scale=2.0)],
                        ['STEP D', sample_from_gamma_distribution(shape=4, scale=0.7)]]

    num_machines_at_ws = [{'ws1': 2},
                        {'ws2': 4},
                        {'ws3': 4}]

class Factory(object):
    '''Holds the workstation(s) (i.e., SimPy Resource) and step that at which each Lot will be processed.
    '''
    def __init__(self, env):
        '''Constructor for initiating SimPy simulation environment.
        '''
        self.env = env

    def step(self, lot):
        '''A Lot runs at a step for the amount of time set in process_time.
        '''
        yield self.env.timeout(next(GlobalVars.step_process_time[lot.step_sequence_number][1]))


class Lot(object):
    '''Holds variables specific to each Lot instance as it flows through steps in the Factory.
    '''
    def __init__(self):
        self.lot_id = next(_lot_id)
        self.step_sequence_number = 0


def insert_datetime_for(env, lot, lot_event):
    '''Inserts event datetimes into the lot_status_df.
    
    Examples of events would be 'step_arrival_time',
    'process_start_time', and 'process_end_time'.
    '''
    GlobalVars.lot_status_df.at[lot.index, str(lot_event)] = env.now


def start_lot(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws1
    # The first step has a step_arrival_time of when the lot was created.
    GlobalVars.lot_status_df = pd.concat([GlobalVars.lot_status_df,
                                            pd.DataFrame(
                                                        {'lot_id': lot.lot_id,
                                                        'step_name': GlobalVars.step_process_time[lot.step_sequence_number][0],
                                                        'step_arrival_time': env.now},
                                                        index=lot.index
                                                        )
                                            ])

    with factory.ws1.request() as request:
        insert_datetime_for(env, lot, 'step_arrival_time') # The lot gets in queue for the first process.
        yield request
        insert_datetime_for(env, lot, 'process_start_time') # After yield, the lot begins the process.
        yield env.process(factory.step(lot))
        insert_datetime_for(env, lot, 'process_end_time') # After yield, the lot has finished processing.

    lot.step_sequence_number += 1
    env.process(lot_at_step_b(env, lot, factory))


def lot_at_step_b(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws2
    GlobalVars.lot_status_df = pd.concat([GlobalVars.lot_status_df,
                                            pd.DataFrame(
                                                        {'lot_id': lot.lot_id,
                                                        'step_name': GlobalVars.step_process_time[lot.step_sequence_number][0],
                                                        'step_arrival_time': env.now},
                                                        index=lot.index
                                                        )
                                            ])

    with factory.ws2.request() as request:
        insert_datetime_for(env, lot, 'step_arrival_time') # The lot gets in queue for the first process.
        yield request
        insert_datetime_for(env, lot, 'process_start_time') # After yield, the lot begins the process.
        yield env.process(factory.step(lot))
        insert_datetime_for(env, lot, 'process_end_time') # After yield, the lot has finished processing.

    lot.step_sequence_number += 1
    env.process(lot_at_step_c(env, lot, factory))

def lot_at_step_c(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws3
    GlobalVars.lot_status_df = pd.concat([GlobalVars.lot_status_df,
                                            pd.DataFrame(
                                                        {'lot_id': lot.lot_id,
                                                        'step_name': GlobalVars.step_process_time[lot.step_sequence_number][0],
                                                        'step_arrival_time': env.now},
                                                        index=lot.index
                                                        )
                                            ])

    with factory.ws3.request() as request:
        insert_datetime_for(env, lot, 'step_arrival_time') # The lot gets in queue for the first process.
        yield request
        insert_datetime_for(env, lot, 'process_start_time') # After yield, the lot begins the process.
        yield env.process(factory.step(lot))
        insert_datetime_for(env, lot, 'process_end_time') # After yield, the lot has finished processing.

    lot.step_sequence_number += 1
    env.process(lot_at_step_d(env, lot, factory))

def lot_at_step_d(env, lot, factory):
    # Last step does not increment lot.step_sequence_number at the end.
    lot.index = [len(GlobalVars.lot_status_df)]
    # ws2
    GlobalVars.lot_status_df = pd.concat([GlobalVars.lot_status_df,
                                            pd.DataFrame(
                                                        {'lot_id': lot.lot_id,
                                                        'step_name': GlobalVars.step_process_time[lot.step_sequence_number][0],
                                                        'step_arrival_time': env.now},
                                                        index=lot.index
                                                        )
                                            ])

    with factory.ws2.request() as request:
        insert_datetime_for(env, lot, 'step_arrival_time') # The lot gets in queue for the first process.
        yield request
        insert_datetime_for(env, lot, 'process_start_time') # After yield, the lot begins the process.
        yield env.process(factory.step(lot))
        insert_datetime_for(env, lot, 'process_end_time') # After yield, the lot has finished processing.



def run_factory(env, lots_ready_at_time_zero=3, interarrival_time_scale=2):
    factory = Factory(env)
    _lot_arrival = _generate_interarrival_time(interarrival_time_scale)

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
        env.process(start_lot(env, Lot(), factory)) # After yield, a new Lot arrives at the factory.

def get_lot_status_df():
    return GlobalVars.lot_status_df
