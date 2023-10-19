# Day Algorithm:
## Dane Wejściowe
* Maksymalna wartość energii w magazynie: `min_b`
* Minimalna wartość energii w magazynie:  `max_b`
* Stan magazynu energii: `start_b`
* Ceny kupna/sprzedaży dla każdej godziny: `prices`
* Bilanse energetyczne dla każdej godziny (produkcja - konsumpcja):  `hourly_balances`
## Dane Wyjściowe 
* Zaktualizowana tablica `hourly_balances`

## Pseudokod
1. Obliczenie wstępego końcowego stanu magazynu `predicted_b` # Obliczenie poziomu magazynu energii gdyby wszystkie bilanse były pokryte z magazynu
2. Sprawdzenie czy `predicted_b` jest większy od `max_b`.\
Jeśli tak to oznacza to że nie trzeba kupować nigdzie energii, aby algorytm zakończył prace z pełnym magazynem `KONIEC`
3. Sprawdzenie czy uzyskanie max_b jest możliwe # Czy dodanie wszystkich nieujemnych wartości z `hourly_balances` do `start_b` da wartość >= `max_b`\
   Jeśli nie to wszystkie ujemne wartości z `hourly_balances` są zamieniane na 0.0 `KONIEC`
4. Obliczamy `need`. Oznacza maksymalną sumaryczną wartość jaką trzeba uzyskać z manipulacji wartościami `hourly_balances` żeby osiągnąć na koniec `max_b`  (`hourly_balances` = `max_b` - `predicted_b`)
5. Tworzymy tablice `idx_order` która zawiera indeksy ujemnych wartosci `hourly_balances` posortowane tak, aby ceny w tych godzinach były od najmniejszej do największej
6. Iterujemy po `idx_order`
7. Dla `i`-tej ujemnej wartości `hourly_balances` iterując w kolejności `idx_order`:
   1. Jeśli `need` <= 0.0 `KONIEC` 
   2. Obliczamy `new_b`\
Jest to `predicted_b` biorąca pod uwagę wartości do i-tej wartości `hourly_balances` 
   3. Aktualizujemy `hourly_balances`


## Jak wygląda akutalizacja `hourly_balances`?
1. Obliczamy `positive_balances`\
Sa to tylko dodatnie wartości `hourly_balances`
2. Jeśli `new_b` + `sum(positive_balances)` jest mniejszy od `max_b` to każda ujenmna wartość z `hourly_balances` zamieniana jest na 0.0 oraz`need` o jest o tyle obniżany
3. Jeśli zastąpienie rozważanej `i`-tej ujemnej wartości w `hourly_balances` na 0.0 nie wpływa na `predicted_b` to przechodzimy do następnej iteracji. 
4. Jeśli `need` <= `i`-ta wartość to `current_need` = `need`.\
Jeśli nie to `current_need` = `i`
5. `i` = `i`- `current_need`
6. `need` = `need` - `current_need`


## Przykład
### Dane Wejsciowe:
`min_b` = 0.0\
`max_b` = 3.0\
`start_b` = 0.88\
`prices` = [251.49, 147.28, 284.38, 213.87, 115.48]\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, -0.6]

### step_1
0.88 + (-0.88) = 0.0\
0.0 + 1.36 = 1.36\
1.36 + 0.85 = 2.21\
2.21 + (-0.32) = 1.89\
1.89 + (-0.6) = 1.29\
`predicted_b` = 1.29

### step_2
`predicted_b` <= `max_b`\
1.29 <= 3.0

### step_3
0.88 + 1.36 + 0.85 = 3.09 --> *jest to możliwe*

### step_4
`need` = `max_b` - `predicted_b`\
`need` = 3.0 - 1.29 = 1.71

### step_5
`prices` = [251.49, 147.28, 284.38, 213.87, 115.48]\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, -0.6]\
`idx_order` = [4, 1, 3, 0, 2]

### step_6 i step_7
#### 1 iteracja
`i1` = 4\
`balance` = -0.6\
`price` = 115.48\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, -0.6]

`need` = 1.71 -> `need` > 0.0\
`new_b` = 0.88 + (-0.88) + 1.36 + 0.85 + (-0.32) = 1.89\
`positive_balances` = []\
`new_b` + `sum(positive_balances)` = 1.89 -> 1.89 < 3.0\
*KONIEC iteracji*\
`need` = 1.71 - 0.6 = 1.11

-------------
#### 2 iteracja 
`i2` = 3\
`balance` = -0.32\
`price` = 213.87\
`hourly_balances` = [-0.88, 1.36, 0.85, -0.32, 0.0]

`need` = 1.11 -> `need` > 0.0\
`new_b` = 0.88 + (-0.88) + 1.36 + 0.85 = 2.21\
`positive_balances` = []\
`new_b` + `sum(positive_balances)` = 2.21 -> 2.21 < 3.0\
*KONIEC iteracji*\
`need` = 1.11 - 0.32 = 0.79

-------------
#### 3 iteracja 
`i3` = 0\
`balance` = -0.88\
`price` = 251.49\
`hourly_balances` = [-0.88, 1.36, 0.85, 0.0, 0.0]

`need` = 0.79 -> `need` > 0.0\
`new_b` = 0.88\
`positive_balances` = [1.36, 0.85]\
`new_b` + `sum(positive_balances)` = 0.88 + 2.21 = 3.09\
`old_predicted_b` = 0.88 + (-0.88) + 1.36 + 0.85 + 0.0 + 0.0 = 2.21\
`new_predicted_b` = 0.88 + 0.0 + 1.36 + 0.85 + 0.0 + 0.0 = 3.0\
`new_predicted_b` != `old_predicted_b`\
`current_need` = 0.79\
*`need` < `balance`*
#### Uaktualniamy need i hourly_balances
`need` = `need` - `current_need` = 0.79 - 0.79 = 0.0\
`hourly_balances` = [-0.11, 1.36, 0.85, 0.0, 0.0] # 0.88 - 0.79 = 0.11
