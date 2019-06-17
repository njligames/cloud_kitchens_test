import time

class Order:
    def __init__(self, name, temp, shelfLife, decayRate):
        self.name = name
        self.temp = temp
        self.shelfLife = shelfLife
        self.decayRate = decayRate
        self.orderTime = None #time.time()
        self.overFlow = False
        self.normalizedValue = 0

    def get_temp(self):
        return self.temp

    def mark_sent(self):
        self.normalizedValue = self.calculate_normalized()
        return self.normalizedValue

    def get_normalized_value(self):
        return self.normalizedValue

    def reset_sent(self):
        self.normalizedValue = 0

    def set_order_time(self):
        self.orderTime = time.time()

    def enable_overflow(self, overflow=True):
        self.overFlow = overflow

    def calculate_value(self):
        orderAge = time.time() - self.orderTime

        value = (self.shelfLife - orderAge) - (self.get_decay_rate() * orderAge)
        return value

    def calculate_normalized(self):
        return self.calculate_value() / self.shelfLife

    def get_decay_rate(self):
        decayRate = self.decayRate
        if(self.overFlow):
            decayRate *= 2
        return decayRate

    def value_decay_amount(self):
        # Derived from value function.
        # value = ([self life] - [order age] - ([decay rate] * [order age]))
        # Where the order age equals the shelf life
        # Returns how much this order will decay.

        v = (self.get_decay_rate() * self.shelfLife)
        return v

    # Since decayRate is 0 < decayRate <= 1, the
    #   closer value_decay_amount is to zero, the faster it decays.
    def lowest_value_decay(self, other):
        vd = self.value_decay_amount()
        other_vd = other.value_decay_amount()

        # Whichever one is closer to zero has the highest value decay.
        if vd < other_vd:
            return self
        return other

    def __str__(self):
        return self.name

    def get_name(self):
        return self.name

    def __gt__(self, other):
        if(self.value_decay_amount() > other.value_decay_amount()):
            return True
        else:
            return False

    def __lt__(self, other):
        if(self.value_decay_amount() < other.value_decay_amount()):
            return True
        else:
            return False

    def __ge__(self, other):
        if(self.value_decay_amount() >= other.value_decay_amount()):
            return True
        else:
            return False

    def __le__(self, other):
        if(self.value_decay_amount() <= other.value_decay_amount()):
            return True
        else:
            return False

    def __eq__(self, other):
        if(self.value_decay_amount() == other.value_decay_amount()):
            return True
        else:
            return False

    def __ne__(self, other):
        if(self.value_decay_amount() != other.value_decay_amount()):
            return True
        else:
            return False
