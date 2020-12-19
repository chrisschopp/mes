import simpy
import random
import pandas as pd

def lot_counter():
    # Generator that assigns an incremental number to each lot, starting with lot_id = 1.
    num = 1
    while True:
        yield num
        num += 1

lot_id = lot_counter()

process_time_dist = {
                    'STEP A': 2,
                    'STEP B': 3,
                    'STEP C': 4
                    }


class GlobalVariables:
    lot_status = pd.DataFrame(columns=['lot_id','step_name','step_arrival_time','process_start_time','process_end_time'])


class Factory(object):
    def __init__(self, env, num_machines_ws1, num_machines_ws2, num_machines_ws3):
        '''Constructor for initiating SimPy simulation environment.'''
        self.env = env
        self.ws1 = simpy.Resource(env, capacity=num_machines_ws1)
        self.ws2 = simpy.Resource(env, capacity=num_machines_ws2)
        self.ws3 = simpy.Resource(env, capacity=num_machines_ws3)

    def step_a(self, lot):
        yield self.env.timeout(step_process_time_dist['STEP A'])

    def step_b(self, lot):
        yield self.env.timeout(step_process_time_dist['STEP B'])

    def step_c(self, lot):
        yield self.env.timeout(step_process_time_dist['STEP C'])


def start_lot(env, lot, factory):
    # A new lot is created and assigned the next lot id.
    current_lot_id = next(lot_id)


    # ws1, step_a
    # The first step has a step_arrival_time of when the lot was created.
    GlobalVariables.lot_status = pd.concat([GlobalVariables.lot_status,
                                            pd.DataFrame({'lot_id': current_lot_id,
                                                        'step_name': list(process_time_dist[0].keys())[0],
                                                        'step_arrival_time': env.now},
                                                        index=[current_lot_id])])

    with factory.ws1.request() as request:
        GlobalVariables.lot_status.at[current_lot_id, 'step_arrival_time'] = env.now # The lot gets in queue for the first process.
        yield request
        GlobalVariables.lot_status.at[current_lot_id, 'process_start_time'] = env.now # After yield, the lot begins the process.
        yield env.process(factory.step_a(lot))
        GlobalVariables.lot_status.at[current_lot_id, 'process_end_time'] = env.now # After yield, the lot has finished processing.


    # ws2, step_b
    GlobalVariables.lot_status = pd.concat([GlobalVariables.lot_status,
                                            pd.DataFrame({'lot_id': current_lot_id,
                                                        'step_name': list(process_time_dist[1].keys())[0],
                                                        'step_arrival_time': env.now},
                                                        index=[current_lot_id])])

    with factory.ws2.request() as request:
        GlobalVariables.lot_status.at[current_lot_id, 'step_arrival_time'] = env.now # The lot gets in queue for the first process.
        yield request
        GlobalVariables.lot_status.at[current_lot_id, 'process_start_time'] = env.now # After yield, the lot begins the process.
        yield env.process(factory.step_b(lot))
        GlobalVariables.lot_status.at[current_lot_id, 'process_end_time'] = env.now # After yield, the lot has finished processing.


    # ws3, step_c
    GlobalVariables.lot_status = pd.concat([GlobalVariables.lot_status,
                                            pd.DataFrame({'lot_id': current_lot_id,
                                                        'step_name': list(process_time_dist[2].keys())[0],
                                                        'step_arrival_time': env.now},
                                                        index=[current_lot_id])])

    with factory.ws3.request() as request:
        GlobalVariables.lot_status.at[current_lot_id, 'step_arrival_time'] = env.now # The lot gets in queue for the first process.
        yield request
        GlobalVariables.lot_status.at[current_lot_id, 'process_start_time'] = env.now # After yield, the lot begins the process.
        yield env.process(factory.step_c(lot))
        GlobalVariables.lot_status.at[current_lot_id, 'process_end_time'] = env.now # After yield, the lot has finished processing.

def run_factory(env, num_machines_ws1=1, num_machines_ws2=1, num_machines_ws3=1, lots_ready_at_time_zero=3, interarrival_time=2):
    factory = Factory(env, num_machines_ws1, num_machines_ws2, num_machines_ws3)

    # The factory starts with some number of lots ready to start processing at the first step.
    for lot in range(lots_ready_at_time_zero):
        env.process(start_lot(env, lot, factory))

    while True:
        yield env.timeout(interarrival_time)

        lot += 1
        env.process(start_lot(env, lot, factory))

def get_lot_status_df():
    return GlobalVariables.lot_status