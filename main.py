
import concurrent.futures
import os, sys, json, time, threading
import numpy as np
import queue
from multiprocessing.pool import ThreadPool
from MyClasses.PriorityQueue import PriorityQueue
from MyClasses.Order import Order
import random
import datetime

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

def update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array):

    hot_size = hot_shelf_queue.qsize()
    cold_size = cold_shelf_queue.qsize()
    frozen_size = frozen_shelf_queue.qsize()
    overflow_size = overflow_shelf_queue.qsize()
    waste_size = len(waste_array)

    print('hot_size', hot_size)
    print('cold_size', cold_size)
    print('frozen_size', frozen_size)
    print('overflow_size', overflow_size)
    print('waste_size', waste_size)
    print('total', hot_size + cold_size + frozen_size + overflow_size + waste_size)
    print('#########')

def parse_json_order(order):
    name = order["name"]
    temp = order["temp"]
    shelfLife = order["shelfLife"]
    decayRate = order["decayRate"]

    o = Order(name, temp, shelfLife, decayRate)
    # print(o)

    return o

def queue_order(json_order, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array):

    order = parse_json_order(json_order)
    order.set_order_time()
    # print(order)

    if "frozen" == json_order["temp"]:
        # print('frozen', frozen_shelf_queue)
        if frozen_shelf_queue.qsize() < 15:
            # print('frozen_shelf_queue')
            frozen_shelf_queue.put(order)
        else:
            if overflow_shelf_queue.qsize() < 20:
                # print('overflow_shelf_queue')
                order.enable_overflow()
                overflow_shelf_queue.put(order)
            else:
                # print('waste_shelf_queue')
                waste_array.append(order)
    elif "cold" == json_order["temp"]:
        # print('cold')
        if cold_shelf_queue.qsize() < 15:
            cold_shelf_queue.put(order)
        else:
            if overflow_shelf_queue.qsize() < 20:
                order.enable_overflow()
                overflow_shelf_queue.put(order)
            else:
                waste_array.append(order)
    elif "hot" == json_order["temp"]:
        # print('hot')
        if hot_shelf_queue.qsize() < 15:
            hot_shelf_queue.put(order)
        else:
            if overflow_shelf_queue.qsize() < 20:
                order.enable_overflow()
                overflow_shelf_queue.put(order)
            else:
                waste_array.append(order)
    else:
        print('Error: There is an unaccounted order temperature.')

def add_seconds(tm, secs):
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate.time()

def produce_orders(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, orders_thread, waste_array, event):
    order_file_queue = orders_thread.get()

    print("Number of Order Left", order_file_queue.qsize())

    start = time.time()
    while True:
        elapsed = time.time() - start
        # print(elapsed)
        if elapsed >= 1.0:
            start = time.time()
            order_count = np.random.poisson(3.25)
            # print(order_count, order_file_queue.qsize())
            for i in range(1, order_count + 1):
                if order_file_queue.qsize() > 0:
                    order = order_file_queue.get()
                    print("Number of Order Left", order_file_queue.qsize())

                    queue_order(order, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array)
                    # print("queued order " + str(order))

                    update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array)

                    # finished, summon driver
                    start_time = datetime.datetime.now().time()
                    seconds_to_drive = random.randint(2, 10)
                    # print('start_time', start_time)
                    arrive_time = add_seconds(start_time, seconds_to_drive)
                    # print('arrive_time', arrive_time)
                    driver_queue.put(arrive_time)


def consume_orders(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, waste_array, event):
    while True:
        current_time = time.time()
        if current_time >= driver_queue.peek():
            driver_queue.get()
            # Driver Arrived

            min_queue = None
            if not hot_shelf_queue.empty():
                min_queue = hot_shelf_queue
            elif not cold_shelf_queue.empty():
                min_queue = cold_shelf_queue
            elif not frozen_shelf_queue.empty():
                min_queue = frozen_shelf_queue
            elif not overflow_shelf_queue.empty():
                min_queue = overflow_shelf_queue

            if None != min_queue:

                if min_queue != overflow_shelf_queue:
                    if min_queue.peek() > overflow_shelf_queue.peek():
                        min_queue = overflow_shelf_queue
                else:
                    if min_queue != hot_shelf_queue:
                        if min_queue.peek() > hot_shelf_queue.peek():
                            min_queue = hot_shelf_queue

                    if min_queue != cold_shelf_queue:
                        if min_queue.peek() > cold_shelf_queue.peek():
                            min_queue = cold_shelf_queue

                    if min_queue != frozen_shelf_queue:
                        if min_queue.peek() > frozen_shelf_queue.peek():
                            min_queue = frozen_shelf_queue

                order = min_queue.get()
                # print("sent order " + str(order))
                update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array)

def cleanup_shelf(pq, waste_array):
    cleanup_list = []
    for i in range(len(pq.queue)):
        item = pq.queue[i]
        if item.calculate_value() <= 0:
            cleanup_list.append(i)

    for i in cleanup_list:
        waste_array.append(pq.queue[i])
        del pq.queue[i]

    if len(cleanup_list) > 0:
        return True
    return False

def cleanup_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, event):
    while True:
        should_update_display = False

        should_update_display = should_update_display or cleanup_shelf(hot_shelf_queue, waste_array)
        should_update_display = should_update_display or cleanup_shelf(cold_shelf_queue, waste_array)
        should_update_display = should_update_display or cleanup_shelf(frozen_shelf_queue, waste_array)
        should_update_display = should_update_display or cleanup_shelf(overflow_shelf_queue, waste_array)

        if True == should_update_display:
            update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array)


def main():
    pool = ThreadPool(processes=1)
    orders_thread = pool.apply_async(setup_orders)

    driver_queue = PriorityQueue()

    hot_shelf_queue = PriorityQueue()
    cold_shelf_queue = PriorityQueue()
    frozen_shelf_queue = PriorityQueue()
    overflow_shelf_queue = PriorityQueue()
    waste_array = []

    event = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(produce_orders, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, orders_thread, waste_array, event)
        # executor.submit(consume_orders, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, waste_array, event)
        executor.submit(cleanup_shelves, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, event)

if __name__ == "__main__":
    main()

