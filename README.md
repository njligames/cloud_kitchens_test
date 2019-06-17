### Instructions on how to run and test the code.

# Please open a terminal (code was developed on a mac)

# How to run:
    1. Setup the python environment
        `source bin/activate`
    2. Run the code
        `python main.py`

# Description of how and why I chose to handle moving orders to and from the overflow shelf
    1. Each shelf (hot, cold, frozen, overflow), were implemented as a priority queue. The drivers dispatched are also implemented as a priority queue.
    2. The orders are placed on one thread and consumed on another thread.
    3. When an order is received, it is added to either one of the hot, cold or frozen shelves, unless they are full.  If the hot, cold or frozen shelves are full, the order is added to the overflow shelf unless it is full, then it would be marked as waste.
    4. When an order is placed, a driver is dispatched with a random time between 2 and 10 seconds and placed into the driver priority queue.
    5. Once the earliest driver arrives, it then gets the order from the shelf queue with the lowest 'value_decay_amount'.
        The 'value_decay_amount' is derived from the value function, where the order age equals the shelf life and the decay rate is taking into account if the order is on the overflow shelf.
        The value function is:
            value = ([self life] - [order age] - ([decay rate] * [order age]))
        The value_decay_amount is:
            if is on overflow:
                value = abs( - ([decay rate] * 2 * [order age]))
            else
                value = abs( - ([decay rate] * [order age]))


