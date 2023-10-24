class EnergyBank:
    """
    A class representing an energy bank

    Attributes:
        capacity (float): Energy bank capacity expressed in kWh.
        lvl (float): Current energy bank level expressed in kWh.
        efficiency (int): The efficiency of energy bank expressed in percentages.
    """

    def __init__(self,
                 capacity: float = 3.0,
                 min_lvl: float = 0.0,
                 lvl: float = 1.0,
                 efficiency: int = 100):     # TODO: Not implemented!
        self.capacity = capacity
        self.min_lvl = min_lvl
        self._lvl = lvl
        self.efficiency = efficiency

    @property
    def lvl(self):
        return self._lvl

    @lvl.setter
    def lvl(self, new_lvl):
        self._lvl = round(new_lvl, 2)

    def manage_energy(self, input_energy: float) -> float:
        if input_energy < 0:
            return round(self._release_energy(input_energy), 2)
        else:
            return round(self._store_energy(input_energy), 2)

    def _store_energy(self, given_energy: float) -> float:
        if given_energy < 0:
            raise Exception(f"Energy: {given_energy} < 0")
        empty_space = self.capacity - self._lvl
        if empty_space >= given_energy:
            self._lvl += given_energy
            return 0.0
        else:
            self._lvl += empty_space
            return given_energy - empty_space

    def _release_energy(self, request_energy: float) -> float:
        if request_energy > 0:
            raise Exception(f"Energy: {request_energy} > 0")
        if abs(request_energy) <= self._lvl:
            self._lvl += request_energy
            return 0.0
        else:
            rest_energy = request_energy + self._lvl
            self._lvl = 0.0
            return rest_energy
