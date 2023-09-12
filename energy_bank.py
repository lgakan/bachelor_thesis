class EnergyBank:
    """
    A class representing an energy bank

    Attributes:
        capacity (float): Energy bank capacity expressed in kWh.
        lvl (float): Current energy bank level expressed in percentages.
        efficiency (int): The efficiency of energy bank expressed in percentages.
    """

    def __init__(self, capacity: float = 10.0,
                 lvl: float = 30.0,
                 efficiency: int = 100):                 # TODO: Not implemented!
        self.capacity = capacity
        self._lvl = lvl
        self.efficiency = efficiency

    def get_lvl(self):
        return self._lvl

    def store_energy(self, given_energy):
        empty_space = self.capacity - self._lvl
        if empty_space <= given_energy:
            self._lvl += given_energy
            return 0
        else:
            self._lvl += empty_space
            return given_energy - empty_space

    def release_energy(self, request_energy):
        if request_energy <= self._lvl:
            self._lvl -= request_energy
            return 0
        else:
            rest_energy = request_energy - self._lvl
            self._lvl = 0
            return rest_energy
