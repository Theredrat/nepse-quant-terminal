import csv
with open("sharehub_data/NICL_brokers.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        print(f"Row {i+1}: Rank={repr(row.get('Rank',''))}, Name={row.get('Broker Name','')}, Hold={row.get('Hold Vol','')}")
        if i >= 4:
            break
