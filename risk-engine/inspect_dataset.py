import pandas as pd


file_path = "data/transaction_dataset.csv"

df = pd.read_csv(file_path)

print("\n===== DATASET INFO =====")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\n===== COLUMNS =====")

for column in df.columns:
    print(column)

print("\n===== FIRST 5 ROWS =====")

print(df.head())

print("\n===== DATA TYPES =====")

print(df.dtypes)

print("\n===== MISSING VALUES =====")

print(df.isnull().sum())