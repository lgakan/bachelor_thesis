class EnergyBank:
    """
    A class representing an energy bank

    Attributes:
        capacity (float): Energy bank capacity expressed in kWh.
        lvl (float): Current energy bank level expressed in kWh.
    """
    def __init__(self,
                 capacity: float = 3.0,
                 min_lvl: float = 0.0,
                 lvl: float = 1.0,
                 purchase_cost: float = 500.0,
                 cycles_num: int = 5000):
        self.capacity = capacity
        self.min_lvl = min_lvl
        self._lvl = lvl
        self.purchase_cost = purchase_cost
        self.cycles_num = cycles_num
        self._start_cycles_num = cycles_num

    @property
    def lvl(self):
        return self._lvl

    @lvl.setter
    def lvl(self, new_lvl: float):
        if self.min_lvl <= new_lvl <= self.capacity:
            self._lvl = round(new_lvl, 2)
        else:
            raise Exception(f"Lvl: {new_lvl} must be between {self.min_lvl} and {self.capacity}")

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
            self._lvl = self.min_lvl
            return rest_energy

    def operation_cost(self, input_balance: float) -> float:
        if self.purchase_cost < 0.0 or self.cycles_num < 0:
            raise Exception(f"Purchase cost: {self.purchase_cost} and cycles: {self.cycles_num} must be greater than 0")
        single_cycle_cost = self.purchase_cost / self._start_cycles_num
        return round(abs(input_balance) / 2 * single_cycle_cost, 2)
