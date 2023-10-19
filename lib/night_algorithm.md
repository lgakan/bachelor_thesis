# Night Algorithm

## Input data

* Maximum energy value in storage: `max_b`.
* Minimum energy value in storage: `min_b`.
* Energy storage state: `start_b`.
* Buying/selling prices for each hour `prices`.
* Energy balances for each hour `hourly_balances` (`production` - `consumption`).

## Output data

* Updated `hourly_balances` array.

## Pseudocode

1. We iterate through the `hourly_balances` array. For the `i`-th balance, we perform steps `2` to `9`.
2. We are checking if the energy bank level will drop below 0 after adding the `i`-th balance.
    1. If not, **_End of iteration_** \
       This means that there was no need to purchase energy from the grid.
    2. If yes, we proceed to point 3.\
       This means that from the beginning of the algorithm until the `i`-th balance, all the energy from the energy
       bank has been used up (dropped below 0). The algorithm's task is to optimize the usage of the energy storage
       so that its charge level drops to a minimum of 0.\
       It achieves this by selecting the cheapest hours and purchasing the appropriate amount of energy during those
       hours.
3. We create an array `inner_balances` that contains `hourly_balances` values from the beginning up to the `i`-th
   balance.
4. We calculate the value of `extra`. This is the amount by which the energy bank should be unloaded so that its charge
   level decreases to a maximum of 0.\
   The determination is based on the `inner_balances` array.
5. We create an `idx_order` array that contains the indices of balance prices from the `inner_balances` array, sorted
   from
   lowest to highest.
6. We iterate through the `idx_order` array. For the `j`-th hour:
7. We are checking if the currently cheapest hour is the one with the balance from the last position of
   the `inner_balances` array.
    1. If yes, we update the `hourly_balances` array and conclude the iteration.
    2. If not, we proceed to point 8.
8. We are checking if the balance from `inner_balances` at the `j`-th index is negative.
    1. If not, we finsh current iteration.
    2. If yes, we proceed to point 9.
9. We are checking if the balance from the `inner_balances` at the `j`-th index can be reduced by `extra`.
    1. If yes, we decrease it, reset `extra`, update `hourly_balances`, and end the iteration.
    2. If not, we decrease `extra` by the value of this balance, set the balance itself to 0, update `inner_balances`,
       and continue.

## Example

### Input

`min_b` = 0.0\
`max_b` = 3.0\
`start_b` = 1.44\
`prices` = [158.49, 296.28, 231.38, 250.87, 230.48]\
`hourly_balances` = [-0.85, -0.53, 0.1, -0.5, 0.1]

_1st iteration `i`=0_\
_step 2_\
1.44 - 0.85 = 0.65\
0.65 - 0.53 = 0.12\
0.12 + 0.1 = 0.22\
0.22 - 0.5 = -0.28 &rarr; `-0.28 < 0.0`

_step 3_\
`extra` = -0.28

_step 4_\
`inner_balances` = [-0.85, -0.53, 0.1, -0.5]

_step 5_\
`idx_order` = [0, 2, 3, 1]

_step 6_\
For `j` = 0\
`idx` = `idx_order[j]`= 0\
`inner_balances[idx]` = -0.85

_step 7_\
`j` = 0, so the cheapest balance is the first (not last) one. It's `false`

_step 8_\
-0.85 &lt; 0.0 &rarr; It's `true`

_step 9_\
`inner_balances[idx]` = -0.85
`extra` = -0.28\
It's possible so it's `true`\
`extra` = -0.28\
`hourly_balances` = [-0.57, -0.53, 0.1, -0.5, 0.1]
---

_2nd iteration `i`=1_\
1.44 - 0.53 = 0.93\
0.93 - 0.53 = 0.4\
0.4 + 0.1 = 0.5\
0.5 - 0.5 = 0.0\
0.0 + 0.1 = 0.1\
*_The value did not drop below 0 at any point, which concludes the algorithm's operation._*
