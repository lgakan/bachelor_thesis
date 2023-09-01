import csv


with open("lib/data/Timeseries_50.080_19.937_SA2_35deg_0deg_2019_2020.csv", 'r') as f:
    csv_reader = csv.DictReader(f, delimiter=',')
    for line in csv_reader:
        print(line)
