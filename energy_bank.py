class EnergyBank:
    """
    A class representing an energy bank

    Attributes:
        capacity (float): Energy bank capacity expressed in kWh.
        lvl (float): Current energy bank level expressed in %.
    """
    def __init__(self, capacity: float = 10.5, lvl: float = 0.0):
        self.capacity = capacity
        self.lvl = lvl
