import csv


with open("lib/data/energy_usage.csv", 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=',')
    # for line in csv_reader:
    #     print(line)
    #     break
    with open("xxx.csv", 'w') as new_file:
        fieldnames = ['Time', 'air_pressure[mmHg]', 'air_temperature[degree celcius]', 'relative_humidity[%]', 'wind_speed[M/S]', 'solar_irridiation[W/mÂ˛]', 'total_cloud_cover[from ten]', 'electricity_demand_values[kw]', 'heat_demand_values[kw]', 'ID']

        csv_writer = csv.DictWriter(new_file, fieldnames=fieldnames, delimiter=';')
        i = 0
        csv_writer.writeheader()
        for line in csv_reader:
            line["ID"] = i
            csv_writer.writerow(line)
            i += 1
