import pytest
from scripts.system import BareSystem, PvSystem, RawFullSystem, SmartSystem, SmartSaveSystem, SystemBase
import random


class TestBareSystemCost:
    def test_positive_prices(self):
        bare_system = BareSystem()
        price, consumption = random.uniform(0.1, 500.0), random.uniform(0.1, 10.0)
        assert bare_system.calculate_cost(price, consumption) == price * consumption

    def test_negative_prices(self):
        bare_system = BareSystem()
        price, consumption = random.uniform(-500.0, -0.1), random.uniform(0.1, 10.0)
        assert bare_system.calculate_cost(price, consumption) == price * consumption


class TestPvSystemCost:
    def test_positive_prices(self):
        pv_system = PvSystem()
        price = random.uniform(0.1, 500.0)
        positive_consumption, negative_consumption = random.uniform(0.1, 10.0), random.uniform(-10.0, -0.1)
        assert pv_system.calculate_cost(price, positive_consumption) == price * positive_consumption
        assert pv_system.calculate_cost(price, negative_consumption) == price * negative_consumption

    def test_negative_prices(self):
        pv_system = PvSystem()
        price = random.uniform(-500.0, -0.1)
        positive_consumption, negative_consumption = random.uniform(0.1, 10.0), random.uniform(-10.0, -0.1)
        assert pv_system.calculate_cost(price, positive_consumption) == price * positive_consumption
        assert pv_system.calculate_cost(price, negative_consumption) == price * negative_consumption


class TestRawFullSystemCost:
    SYSTEM_INPUT = {"eb_capacity": 5.0,
                    "eb_min_lvl": 0.0,
                    "eb_start_lvl": 3.0,
                    "eb_purchase_cost": 2.0,
                    "eb_cycles": 1.0,
                    "pv_size": 5.0,
                    "load_multiplier": 1.0}

    def test_positive_prices(self):
        raw_full_system = RawFullSystem(**self.SYSTEM_INPUT)
        bank_capacity = raw_full_system.energy_bank.capacity
        price = random.uniform(0.1, 500.0)
        positive_in_range_balance, positive_out_range_balance = random.uniform(0.1, 2.0), random.uniform(5.1, 8.0)
        negative_in_range_balance, negative_out_range_balance = random.uniform(-3.0, -0.1), random.uniform(-8.0, -5.1)

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(positive_in_range_balance)
        assert raw_full_system.calculate_cost(price, positive_in_range_balance) == bank_op_cost
        assert raw_full_system.energy_bank.lvl == bank_lvl + positive_in_range_balance

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(negative_in_range_balance)
        assert raw_full_system.calculate_cost(price, negative_in_range_balance) == bank_op_cost
        assert raw_full_system.energy_bank.lvl == bank_lvl + negative_in_range_balance

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(bank_capacity - bank_lvl)
        profit = round((positive_out_range_balance - (bank_capacity - bank_lvl)), 2) * price
        assert raw_full_system.calculate_cost(price, positive_out_range_balance) == -profit + bank_op_cost
        assert raw_full_system.energy_bank.lvl == raw_full_system.energy_bank.capacity

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(bank_lvl)
        expense = round(bank_lvl + negative_out_range_balance, 2) * price
        assert raw_full_system.calculate_cost(price, negative_out_range_balance) == -expense + bank_op_cost
        assert raw_full_system.energy_bank.lvl == raw_full_system.energy_bank.min_lvl

    def test_negative_prices(self):
        raw_full_system = RawFullSystem(**self.SYSTEM_INPUT)
        bank_capacity = raw_full_system.energy_bank.capacity
        price = random.uniform(-500.0, -0.1)
        positive_in_range_balance, positive_out_range_balance = random.uniform(0.1, 2.0), random.uniform(5.1, 8.0)
        negative_in_range_balance, negative_out_range_balance = random.uniform(-3.0, -0.1), random.uniform(-8.0, -5.1)

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(positive_in_range_balance)
        assert raw_full_system.calculate_cost(price, positive_in_range_balance) == bank_op_cost
        assert raw_full_system.energy_bank.lvl == bank_lvl + positive_in_range_balance

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(negative_in_range_balance)
        assert raw_full_system.calculate_cost(price, negative_in_range_balance) == bank_op_cost
        assert raw_full_system.energy_bank.lvl == bank_lvl + negative_in_range_balance

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(bank_capacity - bank_lvl)
        expense = round((positive_out_range_balance - (bank_capacity - bank_lvl)), 2) * price
        assert raw_full_system.calculate_cost(price, positive_out_range_balance) == -expense + bank_op_cost
        assert raw_full_system.energy_bank.lvl == raw_full_system.energy_bank.capacity

        bank_lvl = raw_full_system.energy_bank.lvl
        bank_op_cost = raw_full_system.energy_bank.operation_cost(bank_lvl)
        profit = round(bank_lvl + negative_out_range_balance, 2) * price
        assert raw_full_system.calculate_cost(price, negative_out_range_balance) == -profit + bank_op_cost
        assert raw_full_system.energy_bank.lvl == raw_full_system.energy_bank.min_lvl


class TestSmartSystemCost:
    bank_start_lvl = 3.0
    SYSTEM_INPUT = {"eb_capacity": 6.0,
                    "eb_min_lvl": 0.0,
                    "eb_start_lvl": bank_start_lvl,
                    "eb_purchase_cost": 2.0,
                    "eb_cycles": 1.0,
                    "pv_size": 5.0,
                    "load_multiplier": 1.0}

    def test_positive_prices_positive_balance(self):
        smart_system = SmartSystem(**self.SYSTEM_INPUT)
        price = random.uniform(0.1, 500.0)
        rel_bal_in_range, rel_bal_out_range = random.uniform(1.1, 2.0), random.uniform(7.1, 8.0)
        pred_bal_in_range_s, pred_bal_in_range_h = random.uniform(0.1, 1.0), random.uniform(2.1, 3.0)
        pred_bal_out_range_s, pred_bal_out_range_h = random.uniform(6.1, 7.0), random.uniform(8.1, 10.0)

        # B: 3.0/6.0, R: 2.0, P: 1.0
        bank_op_cost = smart_system.energy_bank.operation_cost(pred_bal_in_range_s)
        profit = round(rel_bal_in_range - pred_bal_in_range_s, 2) * price
        assert smart_system.calculate_cost(price, pred_bal_in_range_s, rel_bal_in_range) == -profit + bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + pred_bal_in_range_s

        # B: 3.0/6.0, R: 2.0, P: 2.5
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(rel_bal_in_range)
        assert smart_system.calculate_cost(price, pred_bal_in_range_h, rel_bal_in_range) == bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + rel_bal_in_range

        # B: 3.0/6.0, R: 2.0, P: 7.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(rel_bal_in_range)
        assert smart_system.calculate_cost(price, pred_bal_out_range_s, rel_bal_in_range) == bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + rel_bal_in_range

        # B: 3.0/6.0, R: 8.0, P: 1.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(pred_bal_in_range_s)
        profit = round(rel_bal_out_range - pred_bal_in_range_s, 2) * price
        assert smart_system.calculate_cost(price, pred_bal_in_range_s, rel_bal_out_range) == -profit + bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + pred_bal_in_range_s

        # B: 3.0/6.0, R: 8.0, P: 7.0  or B: 3.0/6.0, R: 8.0, P: 9.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_free_space = smart_system.energy_bank.capacity - self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(bank_free_space)
        profit = round(rel_bal_out_range - bank_free_space, 2) * price
        assert smart_system.calculate_cost(price, pred_bal_out_range_s, rel_bal_out_range) == -profit + bank_op_cost
        assert smart_system.energy_bank.lvl == smart_system.energy_bank.capacity
        smart_system.energy_bank.lvl = self.bank_start_lvl
        assert smart_system.calculate_cost(price, pred_bal_out_range_h, rel_bal_out_range) == -profit + bank_op_cost
        assert smart_system.energy_bank.lvl == smart_system.energy_bank.capacity

    def test_positive_prices_negative_balance(self):
        smart_system = SmartSystem(**self.SYSTEM_INPUT)
        price = random.uniform(0.1, 500.0)
        rel_bal_in_range, rel_bal_out_range = random.uniform(-2.0, -1.1), random.uniform(-8.0, -7.1)
        pred_bal_in_range_s, pred_bal_in_range_h = random.uniform(-1.0, -0.1), random.uniform(-3.0, -2.1)
        pred_bal_out_range_s, pred_bal_out_range_h = random.uniform(-7.0, -6.1), random.uniform(-10.0, -8.1)

        # B: 3.0/6.0, R: -1.0, P: -2.0
        bank_op_cost = smart_system.energy_bank.operation_cost(rel_bal_in_range)
        assert smart_system.calculate_cost(price, pred_bal_in_range_h, rel_bal_in_range) == bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + rel_bal_in_range

        # B: 3.0/6.0, R: -2.0, P: -1.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(pred_bal_in_range_s)
        expense = round(rel_bal_in_range + pred_bal_in_range_s, 2) * price
        assert smart_system.calculate_cost(price, pred_bal_in_range_s, rel_bal_in_range) == -expense + bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + pred_bal_in_range_s

        # B: 3.0/6.0, R: -8.0, P: -7.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(self.bank_start_lvl)
        expense = round(rel_bal_out_range + self.bank_start_lvl, 2) * price
        assert smart_system.calculate_cost(price, pred_bal_out_range_s, rel_bal_out_range) == -expense + bank_op_cost
        assert smart_system.energy_bank.lvl == smart_system.energy_bank.min_lvl

        # B: 3.0/6.0, R: -8.0, P: -9.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(self.bank_start_lvl)
        expense = round(rel_bal_out_range + self.bank_start_lvl, 2) * price
        assert smart_system.calculate_cost(price, pred_bal_out_range_h, rel_bal_out_range) == -expense + bank_op_cost
        assert smart_system.energy_bank.lvl == smart_system.energy_bank.min_lvl

        # B: 3.0/6.0, R: -1.0, P: -8.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(rel_bal_in_range)
        assert smart_system.calculate_cost(price, pred_bal_out_range_s, rel_bal_in_range) == bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + rel_bal_in_range
        smart_system.energy_bank.lvl = self.bank_start_lvl
        assert smart_system.calculate_cost(price, pred_bal_out_range_h, rel_bal_in_range) == bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + rel_bal_in_range

        # B: 3.0/6.0, R: -8.0, P: -1.0
        smart_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = smart_system.energy_bank.operation_cost(pred_bal_in_range_s)
        expense = round(rel_bal_out_range + pred_bal_in_range_s, 2) * price
        assert smart_system.calculate_cost(price, pred_bal_in_range_s, rel_bal_out_range) == -expense + bank_op_cost
        assert smart_system.energy_bank.lvl == self.bank_start_lvl + pred_bal_in_range_s


class TestSmartSaveSystemCost:
    bank_start_lvl = 3.0
    SYSTEM_INPUT = {"eb_capacity": 5.0,
                    "eb_min_lvl": 0.0,
                    "eb_start_lvl": bank_start_lvl,
                    "eb_purchase_cost": 2.0,
                    "eb_cycles": 1.0,
                    "pv_size": 5.0,
                    "load_multiplier": 1.0}

    def test_positive_prices_positive_balance(self):
        save_system = SmartSaveSystem(**self.SYSTEM_INPUT)
        save_system.average_energy_cost = 300.0
        low_price, high_price = random.uniform(0.1, 299.0), random.uniform(300.1, 599.0)
        positive_in_range_balance, positive_out_range_balance = random.uniform(0.1, 2.0), random.uniform(5.1, 8.0)

        # Bank: 3/6, Price:LOW, Bal: 2.0
        bank_op_cost = save_system.energy_bank.operation_cost(positive_in_range_balance)
        assert save_system.calculate_cost(low_price, positive_in_range_balance) == bank_op_cost
        assert save_system.energy_bank.lvl == self.bank_start_lvl + positive_in_range_balance

        # Bank: 3/6, Price:HIGH, Bal: 2.0
        save_system.energy_bank.lvl = self.bank_start_lvl
        profit = positive_in_range_balance * high_price
        assert save_system.calculate_cost(high_price, positive_in_range_balance) == -profit
        assert save_system.energy_bank.lvl == self.bank_start_lvl

        # Bank: 3/6, Price:LOW, Bal: 7.0
        save_system.energy_bank.lvl = self.bank_start_lvl
        bank_free_space = save_system.energy_bank.capacity - save_system.energy_bank.lvl
        bank_op_cost = save_system.energy_bank.operation_cost(bank_free_space)
        profit = round(positive_out_range_balance - bank_free_space, 2) * low_price
        assert save_system.calculate_cost(low_price, positive_out_range_balance) == -profit + bank_op_cost
        assert save_system.energy_bank.lvl == save_system.energy_bank.capacity

        # Bank: 3/6, Price:HIGH, Bal: 7.0
        save_system.energy_bank.lvl = self.bank_start_lvl
        profit = positive_out_range_balance * high_price
        assert save_system.calculate_cost(high_price, positive_out_range_balance) == -profit
        assert save_system.energy_bank.lvl == self.bank_start_lvl

    def test_positive_prices_negative_balance(self):
        save_system = SmartSaveSystem(**self.SYSTEM_INPUT)
        save_system.average_energy_cost = 300.0
        low_price, high_price = random.uniform(0.1, 299.0), random.uniform(300.1, 599.0)
        negative_in_range_balance, negative_out_range_balance = random.uniform(-2.0, -0.1), random.uniform(-8.0, -5.1)

        # Bank: 3/6, Price:LOW, Bal: -2.0
        save_system.energy_bank.lvl = self.bank_start_lvl
        expense = negative_in_range_balance * low_price
        assert save_system.calculate_cost(low_price, negative_in_range_balance) == -expense
        assert save_system.energy_bank.lvl == self.bank_start_lvl

        # Bank: 3/6, Price:HIGH, Bal: -2.0
        save_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = save_system.energy_bank.operation_cost(negative_in_range_balance)
        assert save_system.calculate_cost(high_price, negative_in_range_balance) == bank_op_cost
        assert save_system.energy_bank.lvl == self.bank_start_lvl + negative_in_range_balance

        # Bank: 3/6, Price:LOW, Bal: -7.0
        save_system.energy_bank.lvl = self.bank_start_lvl
        expense = negative_out_range_balance * low_price
        assert save_system.calculate_cost(low_price, negative_out_range_balance) == -expense
        assert save_system.energy_bank.lvl == self.bank_start_lvl

        # Bank: 3/6, Price:HIGH, Bal: 7.0
        save_system.energy_bank.lvl = self.bank_start_lvl
        bank_op_cost = save_system.energy_bank.operation_cost(self.bank_start_lvl)
        expense = round(negative_out_range_balance + self.bank_start_lvl, 2) * high_price
        assert save_system.calculate_cost(high_price, negative_out_range_balance) == -expense + bank_op_cost
        assert save_system.energy_bank.lvl == save_system.energy_bank.min_lvl
