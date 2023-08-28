class EnergyBank:
    def __init__(self, level: float = 50.0):
        self._level = level

    def get_bank_level(self):
        return self._level
