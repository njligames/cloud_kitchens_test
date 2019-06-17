
import concurrent.futures
import os, sys, json, time, threading
import numpy as np
import queue
from multiprocessing.pool import ThreadPool
from MyClasses.PriorityQueue import PriorityQueue
from MyClasses.Order import Order
import datetime
import random
import uuid

def setup_orders():
    order_queue = queue.Queue()

    try:
        with open("orders.json") as file:
            data = json.loads(file.read())

            for d in data:
                order_queue.put(d)
    except:
        print('Could not open file.log')

    return order_queue

def update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue):

    hot_size = hot_shelf_queue.qsize()
    cold_size = cold_shelf_queue.qsize()
    frozen_size = frozen_shelf_queue.qsize()
    overflow_size = overflow_shelf_queue.qsize()
    waste_size = len(waste_array)
    sent_size = len(sent_array)

    normalized_value = 0
    average_normalized_value = 0

    if sent_size > 0:
        for o in sent_array:
            normalized_value = normalized_value + o.get_normalized_value()
        average_normalized_value = normalized_value / sent_size

    print('#########')
    print('hot_size', hot_size)
    print('cold_size', cold_size)
    print('frozen_size', frozen_size)
    print('overflow_size', overflow_size)
    print('waste_size', waste_size)
    print('sent_size', sent_size)
    print('total orders proccessed', hot_size + cold_size + frozen_size + overflow_size + waste_size + sent_size)
    print('total drivers dispatched', driver_queue.qsize())
    print('average_normalized_value', average_normalized_value)
    print('#########')

def parse_json_order(order):
    name = order["name"]
    temp = order["temp"]
    shelfLife = order["shelfLife"]
    decayRate = order["decayRate"]

    o = Order(name, temp, shelfLife, decayRate)

    return o

def queue_to_overflow(order, overflow_shelf_queue, waste_array):
    if overflow_shelf_queue.qsize() < 20:
        order.enable_overflow()
        overflow_shelf_queue.put(order)
    else:
        waste_array.append(order)

def queue_order(order, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array):

    order.set_order_time()

    if "frozen" == order.get_temp():
        if frozen_shelf_queue.qsize() < 15:
            frozen_shelf_queue.put(order)
        else:
            queue_to_overflow(order, overflow_shelf_queue, waste_array)
    elif "cold" == order.get_temp():
        if cold_shelf_queue.qsize() < 15:
            cold_shelf_queue.put(order)
        else:
            queue_to_overflow(order, overflow_shelf_queue, waste_array)
    elif "hot" == order.get_temp():
        if hot_shelf_queue.qsize() < 15:
            hot_shelf_queue.put(order)
        else:
            queue_to_overflow(order, overflow_shelf_queue, waste_array)
    else:
        print('Error: There is an unaccounted order temperature.')

def add_seconds(tm, secs):
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate.time()

def produce_orders(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, orders_thread, waste_array, sent_array, event):
    order_file_queue = orders_thread.get()


    start = time.time()
    while not event.is_set() or order_file_queue.qsize() > 0:

        elapsed_seconds = time.time() - start

        if elapsed_seconds >= 1.0:
            start = time.time()
            order_count = np.random.poisson(3.25)
            for i in range(1, order_count + 1):

                if order_file_queue.qsize() > 0:
                    json_order = order_file_queue.get()

                    order = parse_json_order(json_order)
                    queue_order(order, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array)

                    update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue)

                    start_time = datetime.datetime.now()
                    seconds_to_drive = random.randint(2, 10)
                    arrive_time = start_time + datetime.timedelta(seconds=seconds_to_drive)
                    driver_queue.put(arrive_time)


def cleanup_shelf(pq, waste_array):
    cleanup_list = []
    for i in range(len(pq.queue)):
        item = pq.queue[i]
        if item.calculate_value() <= 0:
            cleanup_list.append(i)

    for i in cleanup_list:
        order = pq.queue[i]
        waste_array.append(order)
        del pq.queue[i]

    if len(cleanup_list) > 0:
        return True
    return False

def adjust_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue, order_removed):
    shelves = [hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue]

    if overflow_shelf_queue.qsize() > 0:
        put_queue = None
        for shelf in shelves:
            if shelf.get_name() == order_removed.get_name():
                put_queue = shelf

        if put_queue is not None:
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("The put queue is", put_queue.get_name())
            print("The order removed is", order_removed.get_name())
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

            special_value = order_removed
            special_condition = lambda a, b: a.get_name() == b.get_name()

            order = overflow_shelf_queue.get(special_value, special_condition)

            if order is not None:
                queue_order(order, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array)

def cleanup_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue):
    should_update_display = False

    should_update_display = should_update_display or cleanup_shelf(hot_shelf_queue, waste_array)
    should_update_display = should_update_display or cleanup_shelf(cold_shelf_queue, waste_array)
    should_update_display = should_update_display or cleanup_shelf(frozen_shelf_queue, waste_array)
    should_update_display = should_update_display or cleanup_shelf(overflow_shelf_queue, waste_array)

    if True == should_update_display:
        update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue)

def consume_orders(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, waste_array, sent_array, event):

    while not event.is_set() or driver_queue.qsize() > 0:

        cleanup_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue)

        if driver_queue.qsize() > 0:
            current_time = datetime.datetime.now()
            first_available_time = driver_queue.peek()


            if current_time >= first_available_time:
                driver_queue.get()

                min_queue = None
                queue_list = []
                if hot_shelf_queue.qsize() > 0:
                    min_queue = hot_shelf_queue
                    queue_list.append(hot_shelf_queue)

                if cold_shelf_queue.qsize() > 0:
                    min_queue = cold_shelf_queue
                    queue_list.append(cold_shelf_queue)

                if frozen_shelf_queue.qsize() > 0:
                    min_queue = frozen_shelf_queue
                    queue_list.append(frozen_shelf_queue)

                if overflow_shelf_queue.qsize() > 0:
                    min_queue = overflow_shelf_queue
                    queue_list.append(overflow_shelf_queue)

                if min_queue is not None:
                    if len(queue_list) > 0:
                        min_queue = min_queue.min(queue_list)

                    order = min_queue.get()
                    normalized_value = order.mark_sent()

                    if overflow_shelf_queue != min_queue:
                        adjust_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue, order)

                    sent_array.append(order)

                    update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue)


def main():

    pool = ThreadPool(processes=1)
    orders_thread = pool.apply_async(setup_orders)

    driver_queue = PriorityQueue()
    driver_queue.set_name("driver")

    hot_shelf_queue = PriorityQueue()
    hot_shelf_queue.set_name("hot")

    cold_shelf_queue = PriorityQueue()
    cold_shelf_queue.set_name("cold")

    frozen_shelf_queue = PriorityQueue()
    frozen_shelf_queue.set_name("frozen")

    overflow_shelf_queue = PriorityQueue()
    overflow_shelf_queue.set_name("overflow")

    waste_array = []
    sent_array = []

    event = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(produce_orders, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, orders_thread, waste_array, sent_array, event)
        executor.submit(consume_orders, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, waste_array, sent_array, event)

        pqueues = [hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue]

        can_set_event = True
        while can_set_event:
            time.sleep(10)

            can_set_event = True
            for pq in pqueues:
                if pq.qsize() > 0:
                    can_set_event = can_set_event and False

        event.set()

if __name__ == "__main__":
    main()

