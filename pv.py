class Pv:
    def __init__(self, production: float = 0.0):
        self._production = production

    def get_current_production(self):
        with open("lib/energy_production.csv", 'r') as f:
            self._production = f.readline()
            return self._production
