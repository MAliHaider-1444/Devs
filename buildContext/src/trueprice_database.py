import os
import sqlalchemy as sa
import pandas as pd

# PGUSER=docker PGPASSWORD=docker DATABASE=localhost python3 ./buildContext/src/trueprice_database.py
def get_all_data():
    database = os.environ["DATABASE"]
    pgpassword = os.environ["PGPASSWORD"]
    pguser = os.environ["PGUSER"]
    connection = f"postgresql://{pguser}:{pgpassword}@{database}:5432/trueprice"
    print(f"using {connection}")
    engine = sa.create_engine(connection)
    r = pd.read_sql(sa.text("SELECT * FROM trueprice.data"), engine)
    return r

if __name__ == "__main__":
    get_all_data()