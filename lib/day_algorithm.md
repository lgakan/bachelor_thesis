# Day Algorithm

## Input Data

* Maximum energy value in storage: `max_b`.
* Minimum energy value in storage: `min_b`.
* Energy storage state: `start_b`.
* Buying/selling prices for each hour `prices`.
* Energy balances for each hour `hourly_balances` (`production` - `consumption`).

## Output data

* Updated `hourly_balances` array.

## Pseudocode

1. We calculate our prediction for the final level of energy bank `predicted_b`.\
   This is the energy bank level if all the balances were covered by it.
2. Checking if `predicted_b` &ge; `max_b`.
    1. If yes, we're done with the algorithm!\
       This means that there is no need to purchase energy anywhere for the algorithm to complete its work with the
       energy bank fully charged.
    2. If not, proceed to step 3.
3. Checking if obtaining `max_b` is possible. (Is adding all non-negative values from `hourly_balances` to `start_b`
   will be &ge; than `max_b`?)
    1. If not, all negative values from `hourly_balances` are replaced with 0.0, and the algorithm terminates.
    2. If yes, proceed to step 4.
4. We calculate the value of `need`. \
   It represents the maximum total value that needs to be achieved by manipulating the values in the `hourly_balances`
   array in
   order to reach `max_b` at the end.\
   `need` = `max_b` - `predicted_b`
5. We create an array `idx_order` that contains the indices of negative values in `hourly_balances`, sorted in such a
   way
   that prices during these hours are from the smallest to the largest.
6. We iterate through `idx_order`.
7. For the `i`-th negative value in `hourly_balances` while iterating in the `idx_order` sequence:
    1. If `need` &le; 0.0 &rarr; *End of the algorithm* .
    2. We calculate `new_b`.\
       This is `predicted_b` considering the values up to the `i`-th value in `hourly_balances`.
    3. We are updating the `hourly_balances`.

### How does the update of `hourly_balances` look?

1. We are calculating `positive_balances`.\
   These are only positive values of `hourly_balances`.
2. Check if `new_b` + `sum(positive_balances)` &lt; `max_b`,
    1. If yes, every negative value from `hourly_balances` is set to 0.0 and `need` is reduced by that amount
    2. If not, If yes, proceed to step 3.
3. If replacing the `i`-th negative value in `hourly_balances` with 0.0 doesn't affect `predicted_b`, we proceed to the
   next iteration.\
   This means that whether the energy is drawn from the energy bank or from the grid, the final level of charge in the
   energy bank will be the same.
4. We are checking if the `need` &le; `i`-th value.
    1. If yes, `current_need` = `need`.
    2. If not, `current_need` = `i`.
5. `i` = `i`- `current_need`.
6. `need` = `need` - `current_need`.

## Example

### Input:

`min_b` = 0.0\
`max_b` = 3.0\
`start_b` = 0.88\
`prices` = [251.49, 147.28, 284.38, 213.87, 115.48]\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, -0.6]

_step 1_\
0.88 + (-0.88) = 0.0\
0.0 + 1.36 = 1.36\
1.36 + 0.85 = 2.21\
2.21 + (-0.32) = 1.89\
1.89 + (-0.6) = 1.29\
`predicted_b` = 1.29

_step 2_\
`predicted_b` &le; `max_b`\
1.29 &le; 3.0

_step 3_\
0.88 + 1.36 + 0.85 = 3.09 &rarr; *It is possible*

_step 4_\
`need` = `max_b` - `predicted_b`\
`need` = 3.0 - 1.29 = 1.71

_step 5_\
`prices` = [251.49, 147.28, 284.38, 213.87, 115.48]\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, -0.6]\
`idx_order` = [4, 1, 3, 0, 2]

_step 6 and step 7_\
_1st iteration_\
`i1` = 4\
`balance` = -0.6\
`price` = 115.48\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, -0.6]

`need` = 1.71 &rarr; `need` &gt; 0.0\
`new_b` = 0.88 + (-0.88) + 1.36 + 0.85 + (-0.32) = 1.89\
`positive_balances` = []\
`new_b` + `sum(positive_balances)` = 1.89 &rarr; 1.89 &lt; 3.0\
*Iteration ends*\
`need` = 1.71 - 0.6 = 1.11

-------------
_2nd iteration_\
`i2` = 3\
`balance` = -0.32\
`price` = 213.87\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, 0.0]

`need` = 1.11 &rarr; `need` &gt; 0.0\
`new_b` = 0.88 + (-0.88) + 1.36 + 0.85 = 2.21\
`positive_balances` = []\
`new_b` + `sum(positive_balances)` = 2.21 &rarr; 2.21 &lt; 3.0\
*Iteration ends*\
`need` = 1.11 - 0.32 = 0.79

-------------
_3rd iteration_\
`i3` = 0\
`balance` = -0.88\
`price` = 251.49\
`hourly_balances` = [-0.88, 1.36, 0.85, 0.0, 0.0]

`need` = 0.79 &rarr;`need` &gt; 0.0\
`new_b` = 0.88\
`positive_balances` = [1.36, 0.85]\
`new_b` + `sum(positive_balances)` = 0.88 + 2.21 = 3.09\
`old_predicted_b` = 0.88 + (-0.88) + 1.36 + 0.85 + 0.0 + 0.0 = 2.21\
`new_predicted_b` = 0.88 + 0.0 + 1.36 + 0.85 + 0.0 + 0.0 = 3.0\
`new_predicted_b` != `old_predicted_b`\
`current_need` = 0.79\
*`need` &lt; `balance`*\
_`need` and `hourly_balances`update_\
`need` = `need` - `current_need` = 0.79 - 0.79 = 0.0\
`hourly_balances` = [-0.11, 1.36, 0.85, 0.0, 0.0] # 0.88 - 0.79 = 0.11
