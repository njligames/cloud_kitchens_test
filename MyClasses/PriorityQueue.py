class PriorityQueue(object):
    def __init__(self):
        self.queue = []

    def __str__(self):
        return ' '.join([str(i) for i in self.queue])

    # for checking if the queue is empty
    def empty(self):
        return len(self.queue) == []

    def qsize(self):
        return len(self.queue)

    # for inserting an element in the queue
    def put(self, data):
        self.queue.append(data)

    # for popping an element based on Priority
    def get(self):
        try:
            min = 0
            for i in range(len(self.queue)):
                if self.queue[i] < self.queue[min]:
                    min = i
            item = self.queue[min]
            del self.queue[min]
            return item
        except IndexError:
            print()
            exit()

    def peek(self):
        try:
            min = 0
            for i in range(len(self.queue)):
                if self.queue[i] < self.queue[min]:
                    min = i
            item = self.queue[min]
            return item
        except IndexError:
            print()
            exit()

    def __str__(self):
        return str(self.queue)
