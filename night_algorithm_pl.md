# Night Algorithm
## Dane Wejściowe
* Maksymalna wartość energii w magazynie: `min_b`.
* Minimalna wartość energii w magazynie:  `max_b`.
* Stan magazynu energii: `start_b`.
* Ceny kupna/sprzedaży dla każdej godziny: `prices`.
* Bilanse energetyczne dla każdej godziny (produkcja - konsumpcja):  `hourly_balances`.
## Dane Wyjściowe
* Zaktualizowana tablica `hourly_balances`.

## Pseudokod
1. Przechodzimy po tablicy `hourly_balances`. Dla `i`-tego bilansu wykonujemy punkty `2` - `9`.
2. Sprawdzamy czy poziom naładowania magazynu po dodaniu `i`-tego bilansu spadnie poniżej 0.
   1. Jeśli nie, **_KONIEC ALGORYTMU_** \
Oznacza to że nie było potrzeby zakupu energii z sieci. 
   2. Jeśli tak, przechodzimy do pkt. 3. \
Oznacza to, że  w okresie od początku algorytmu do `i`-tego bilansu zużyto całą energię z magazynu energii. \
Algorytm ma za zadnie zoptymalizować miejsca korzystania z magazynu tak, aby poziom jego naładowania spadł maksymalnie do 0. \
Osiąga to za pomocą wybrania najtańszych godzin i kupowania w nich odpowiedniej ilości energii.
3. Obliczamy wartość `extra`. Jest to wartość jaką należy zabrać z `i`-tego bilansu tak aby poziom naładowania magazynu spadł maksymalnie do 0.
4. Tworzymy tablice `inner_balances` która zawiera wartości `hourly_balances` od początku do `i`-tego bilansu.
5. Wyznaczamy tablice `idx_order`, która zawiera indeksy cen bilansów z tablicy `inner_balances`, posortowane od najniższej do najwyższej.
6. Przechodzimy po tablicy `idx_order`. Dla `j`-tego bilasnu:
7. Sprawdzamy czy obecnie najtańszą godziną jest ta z bilansem z ostatniego elementu tablicy `inner_balances`.
    2. Jeśli tak, aktualizujemy tablice `hourly_balances` i kończymy iteracje.
    1. Jeśli nie, przechodzimy do pkt. 8.
8. Sprawdzamy czy dla bilans z `inner_balances` o `j`-tym indeksie jest ujemny.
   1. Jeśli nie, idziemy dalej.
   2. Jeśli tak, przechodzimy do pkt. 9.
9. Sprawdzamy czy bilans z `inner_balances` o `j`-tym indeksie można obniżyć o `extra`.
   1. Jeśli tak, obniżamy go, zerujemy `extra`, aktualizujemy `hourly_balances` i kończymy iteracje
   2. Jeśli nie, obniżamy `extra` o wartość tego bilansu, sam bilans zmieniamy na 0, aktualizujemy `inner_balances` i idziemy dalej

## Przykład
`min_b` = 0.0\
`max_b` = 3.0\
`start_b` = 1.44\
`prices` = [158.49, 296.28, 231.38, 250.87, 230.48]\
`hourly_balances` = [-0.85, -0.53, 0.1, -0.5, 0.1]
### 1 iteracja `i` = 0
_step 2_\
1.44 - 0.85 = 0.65\
0.65 - 0.53 = 0.12\
0.12 + 0.1 = 0.22\
0.22 - 0.5 = -0.28 -> `-0.28 < 0.0`\

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
 -0.85 < 0.0 -> It's `true`

_step 9_\
`inner_balances[idx]` = -0.85
`extra` = -0.28\
It's possible so it's `true`\
`extra` = -0.28\
`hourly_balances` = [-0.57, -0.53, 0.1, -0.5, 0.1]
---
### 2 iteracja `i` = 1
1.44 - 0.53 = 0.93\
0.93 - 0.53 = 0.4\
0.4 + 0.1 = 0.5\
0.5 - 0.5 = 0.0\
0.0 + 0.1 = 0.1\
*_The value did not drop below 0 at any point, which concludes the algorithm's operation._*
