class PriorityQueue(object):
    def __init__(self):
        self.queue = []
        self.name = "pqueue"

    def __str__(self):
        return self.name + ": " + ' '.join([str(i) for i in self.queue])

    # for checking if the queue is empty
    def empty(self):
        return self.qsize() <= 0

    def qsize(self):
        if not self.queue:
            return 0
        return len(self.queue)

    # for inserting an element in the queue
    def put(self, data):
        self.queue.append(data)

    # for popping an element based on Priority
    def get(self, special_condition=lambda a:True):

        # print("The special condition is", special_condition(1))
        try:
            min = 0
            for i in range(len(self.queue)):
                if True == special_condition(self.queue[i]):
                    if self.queue[i] < self.queue[min]:
                        min = i
            item = self.queue[min]
            del self.queue[min]
            return item
        except IndexError as err:
            print(err)
            # exit()

    def peek(self):
        try:
            min = 0
            for i in range(len(self.queue)):
                if self.queue[i] < self.queue[min]:
                    min = i
            item = self.queue[min]
            return item
        except IndexError as err:
            print(err)
            # exit()

    def set_name(self, name):
        self.name = str(name)

    def get_name(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    # All lists must not be empty.
    def min(self, pq_list):
        min_pq = self
        for pq in pq_list:
            if not pq.empty() and not min_pq.empty():
                if pq.peek() < min_pq.peek():
                    min_pq = pq
        return min_pq

    def max(self, pq_list):
        max_pq = self
        for pq in pq_list:
            if pq.peek() > max_pq.peek:
                max_pq = pq
        return max_pq

