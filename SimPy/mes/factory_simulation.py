import simpy
import random
import pandas as pd

def lot_counter():
    # Generator that assigns an incremental number to each lot, starting with lot_id = 1.
    num = 1
    while True:
        yield num
        num += 1


class GlobalVars:
    '''Holds variables needed by other classes.
    '''
    lot_status = pd.DataFrame(columns=['lot_id', 'step_name', 'step_arrival_time', 'process_start_time', 'process_end_time'])
    process_time_dist = [
                            ['STEP A', 1],
                            ['STEP B', 2],
                            ['STEP C', 3]
                        ]


class Factory(object):
    def __init__(self, env, num_machines_ws1, num_machines_ws2, num_machines_ws3):
        '''Constructor for initiating SimPy simulation environment.'''
        self.env = env
        self.ws1 = simpy.Resource(env, capacity=num_machines_ws1)
        self.ws2 = simpy.Resource(env, capacity=num_machines_ws2)
        self.ws3 = simpy.Resource(env, capacity=num_machines_ws3)

    def step_a(self, lot):
        yield self.env.timeout(GlobalVars.process_time_dist[0][1])

    def step_b(self, lot):
        yield self.env.timeout(GlobalVars.process_time_dist[1][1])

    def step_c(self, lot):
        yield self.env.timeout(GlobalVars.process_time_dist[2][1])


class Lot(object):
    def __init__(self):
        '''Constructor for initiating lot.'''
        self.lot_id = next(lot_counter())
        self.step_sequence_number = 1


def insert_datetime_for(env, lot, lot_event):
    GlobalVars.lot_status.at[lot.index, str(lot_event)] = env.now


def start_lot(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status)]
    # ws1, step_a
    # The first step has a step_arrival_time of when the lot was created.
    # 1 is subtracted from step_sequence_number to align with zero indexed list.
    GlobalVars.lot_status = pd.concat([GlobalVars.lot_status,
                                            pd.DataFrame(
                                                        {'lot_id': lot.lot_id,
                                                        'step_name': GlobalVars.process_time_dist[lot.step_sequence_number - 1][0],
                                                        'step_arrival_time': env.now},
                                                        index=lot.index
                                                        )
                                            ])

    with factory.ws1.request() as request:
        # 1 is subtracted from the length of the lot_status DataFrame so that the datetimes are inserted into the correct, zero-indexed row.
        insert_datetime_for(env, lot, 'step_arrival_time') # The lot gets in queue for the first process.
        yield request
        insert_datetime_for(env, lot, 'process_start_time') # After yield, the lot begins the process.
        yield env.process(factory.step_a(lot))
        insert_datetime_for(env, lot, 'process_end_time') # After yield, the lot has finished processing.

    lot.step_sequence_number += 1
    env.process(continue_lot(env, lot, factory))


def continue_lot(env, lot, factory):
    lot.index = [len(GlobalVars.lot_status)]
    # ws2, step_b
    GlobalVars.lot_status = pd.concat([GlobalVars.lot_status,
                                            pd.DataFrame({'lot_id': lot.lot_id,
                                                        'step_name': GlobalVars.process_time_dist[lot.step_sequence_number - 1][0],
                                                        'step_arrival_time': env.now},
                                                        index=[len(GlobalVars.lot_status)])])

    with factory.ws2.request() as request:
        GlobalVars.lot_status.at[lot.index, 'step_arrival_time'] = env.now # The lot gets in queue for the first process.
        yield request
        GlobalVars.lot_status.at[lot.index, 'process_start_time'] = env.now # After yield, the lot begins the process.
        yield env.process(factory.step_b(lot))
        GlobalVars.lot_status.at[lot.index, 'process_end_time'] = env.now # After yield, the lot has finished processing.


def run_factory(env, num_machines_ws1=1, num_machines_ws2=1, num_machines_ws3=1, lots_ready_at_time_zero=3, interarrival_time=2):
    factory = Factory(env, num_machines_ws1, num_machines_ws2, num_machines_ws3)

    # The factory starts with some number of lots ready to start processing at the first step.
    for lot in range(lots_ready_at_time_zero):
        env.process(start_lot(env, Lot(), factory))

    # The factory receives new lots according the the interarrival_time.
    while True:
        yield env.timeout(interarrival_time)

        lot += 1
        env.process(start_lot(env, Lot(), factory))

def get_lot_status_df():
    return GlobalVars.lot_status