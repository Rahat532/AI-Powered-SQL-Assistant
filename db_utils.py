import pandas as pd
import sqlite3

DB_PATH = "uploaded.db"

def save_csv_to_db(df: pd.DataFrame, table_name: str):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    return table_name, df.columns.tolist()
