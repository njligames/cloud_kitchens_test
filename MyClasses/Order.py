import time

class Order:
    def __init__(self, name, temp, shelfLife, decayRate):
        self.name = name
        self.temp = temp
        self.shelfLife = shelfLife
        self.decayRate = decayRate
        self.orderTime = None #time.time()
        self.overFlow = False

    def set_order_time(self):
        self.orderTime = time.time()

    def enable_overflow(self, overflow=True):
        self.overFlow = overflow

    def calculate_value(self):
        orderAge = time.time() - self.orderTime
        decayRate = self.decayRate
        if(self.overFlow):
            decayRate *= 2

        # print("orderAge", orderAge)
        value = (self.shelfLife - orderAge) - (decayRate * orderAge)
        # print('calculated value: ', value)
        return value

    def calculate_normalized(self):
        return self.calculate_value() / self.shelfLife

    def __str__(self):
        return self.name

    def __gt__(self, other):
        if(self.shelfLife > other.shelfLife):
            return True
        else:
            return False

    def __lt__(self, other):
        if(self.shelfLife < other.shelfLife):
            return True
        else:
            return False

    def __ge__(self, other):
        if(self.shelfLife >= other.shelfLife):
            return True
        else:
            return False

    def __le__(self, other):
        if(self.shelfLife <= other.shelfLife):
            return True
        else:
            return False

    def __eq__(self, other):
        if(self.shelfLife == other.shelfLife):
            return True
        else:
            return False

    def __ne__(self, other):
        if(self.shelfLife != other.shelfLife):
            return True
        else:
            return False
