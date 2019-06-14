
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

def queue_order(json_order, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array):

    order = parse_json_order(json_order)
    order.set_order_time()

    if "frozen" == json_order["temp"]:
        if frozen_shelf_queue.qsize() < 15:
            print('Added `' + str(order) + '` to the Frozen shelf')
            frozen_shelf_queue.put(order)
        else:
            if overflow_shelf_queue.qsize() < 20:
                print('Added `' + str(order) + '` to the Overflow shelf')
                order.enable_overflow()
                overflow_shelf_queue.put(order)
            else:
                print('Wasted `' + str(order) + '` during PRODUCTION')
                waste_array.append(order)
    elif "cold" == json_order["temp"]:
        if cold_shelf_queue.qsize() < 15:
            print('Added `' + str(order) + '` to the Cold shelf')
            cold_shelf_queue.put(order)
        else:
            if overflow_shelf_queue.qsize() < 20:
                print('Added `' + str(order) + '` to the Overflow shelf')
                order.enable_overflow()
                overflow_shelf_queue.put(order)
            else:
                print('Wasted `' + str(order) + '` during PRODUCTION')
                waste_array.append(order)
    elif "hot" == json_order["temp"]:
        if hot_shelf_queue.qsize() < 15:
            print('Added `' + str(order) + '` to the Hot shelf')
            hot_shelf_queue.put(order)
        else:
            if overflow_shelf_queue.qsize() < 20:
                print('Added `' + str(order) + '` to the Overflow shelf')
                order.enable_overflow()
                overflow_shelf_queue.put(order)
            else:
                print('Wasted `' + str(order) + '` during PRODUCTION')
                waste_array.append(order)
    else:
        print('Error: There is an unaccounted order temperature.')

def add_seconds(tm, secs):
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate.time()

def produce_orders(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, driver_queue, orders_thread, waste_array, sent_array, event):
    order_file_queue = orders_thread.get()

    print("Number of Order Start", order_file_queue.qsize())

    start = time.time()
    while not event.is_set() or order_file_queue.qsize() > 0:
        # print("producing")

        elapsed_seconds = time.time() - start
        # print(elapsed_seconds)

        if elapsed_seconds >= 1.0:
            start = time.time()
            order_count = np.random.poisson(3.25)
            # print(order_count, order_file_queue.qsize())
            for i in range(1, order_count + 1):

                if order_file_queue.qsize() > 0:
                    order = order_file_queue.get()
                    print("Number of Order Left", order_file_queue.qsize())

                    queue_order(order, hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array)
                    # print("queued order " + str(order))

                    update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue)

                    # print('updated display')
                    # finished, summon driver
                    start_time = datetime.datetime.now()
                    # print('start_time', start_time)
                    seconds_to_drive = random.randint(2, 10)
                    # print('seconds_to_drive', seconds_to_drive)
                    arrive_time = start_time + datetime.timedelta(seconds=seconds_to_drive)
                    # arrive_time = add_seconds(start_time, seconds_to_drive)
                    # print('arrive_time', arrive_time)
                    driver_queue.put(arrive_time)
                    # print("driver_queue.qsize()", driver_queue.qsize())

    print("exiting produce_orders")

def cleanup_shelf(pq, waste_array):
    cleanup_list = []
    for i in range(len(pq.queue)):
        item = pq.queue[i]
        if item.calculate_value() <= 0:
            cleanup_list.append(i)

    for i in cleanup_list:
        order = pq.queue[i]
        print('Wasted `' + str(order) + '` during CLEANUP')
        waste_array.append(order)
        del pq.queue[i]

    if len(cleanup_list) > 0:
        return True
    return False

def adjust_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue, order_removed):
    shelves = [hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue]

    # put_queue = None
    # for shelf in shelves:
    #     if shelf is not None and order_removed is not None:
    #         if shelf.get_name() == order_removed.get_name():
    #             put_queue = shelf

    # if put_queue is not None:
    #     pass

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
        # print("consuming: " + str(driver_queue.qsize()))

        cleanup_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue)

        if driver_queue.qsize() > 0:
            current_time = datetime.datetime.now()
            first_available_time = driver_queue.peek()

            # print("time", current_time, first_available_time)

            if current_time >= first_available_time:
                driver_queue.get()
                # Driver Arrived
                # print('driver arrived', driver_queue.qsize())

                # Find the order with the lowest value_decay_amount
                min_queue = None
                queue_list = []
                if hot_shelf_queue.qsize() > 0:
                    # print("hot_shelf_queue.qsize()", hot_shelf_queue.qsize())
                    min_queue = hot_shelf_queue
                    queue_list.append(hot_shelf_queue)

                if cold_shelf_queue.qsize() > 0:
                    # print("cold_shelf_queue.qsize()", cold_shelf_queue.qsize())
                    min_queue = cold_shelf_queue
                    queue_list.append(cold_shelf_queue)

                if frozen_shelf_queue.qsize() > 0:
                    # print("frozen_shelf_queue.qsize()", frozen_shelf_queue.qsize())
                    min_queue = frozen_shelf_queue
                    queue_list.append(frozen_shelf_queue)

                if overflow_shelf_queue.qsize() > 0:
                    # print("overflow_shelf_queue.qsize()", overflow_shelf_queue.qsize())
                    min_queue = overflow_shelf_queue
                    queue_list.append(overflow_shelf_queue)

                if min_queue is not None:
                    if len(queue_list) > 0:
                        min_queue = min_queue.min(queue_list)

                    order = min_queue.get()
                    normalized_value = order.mark_sent()

                    if overflow_shelf_queue != min_queue:
                        adjust_shelves(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue, order)

                    # print("got order", str(order))
                    sent_array.append(order)
                    print("Sent `" + str(order) + "` with Normalized Value = " + str(normalized_value))

                    update_display(hot_shelf_queue, cold_shelf_queue, frozen_shelf_queue, overflow_shelf_queue, waste_array, sent_array, driver_queue)

    print("exited consume_orders")

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

        while True:
            can_set_event = True
            while pq in pqueues:
                if pq.pqsize() > 0:
                    can_set_event = False
            if can_set_event:
                break

        event.set()

if __name__ == "__main__":
    main()

