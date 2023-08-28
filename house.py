class House:
    def __init__(self, consumption: float = 0.0):
        self._consumption = consumption

    def get_current_consumption(self):
        with open("lib/energy_usage.csv", 'r') as f:
            self._consumption = f.readline()
            return self._consumption
