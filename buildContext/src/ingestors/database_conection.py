"""
Builds the connection to the database
"""
import os
import sqlalchemy as sa

class ConnectDatabase:
    """
    Makes the connection to the database postgres
    """
    def __init__(self):
        """
        credantials for the database
        """
        self.database = os.environ["DATABASE"] if "DATABASE" in os.environ else "localhost"
        self.pgpassword = os.environ["PGPASSWORD"] if "PGPASSWORD" in os.environ else "postgres"
        self.pguser = os.environ["PGUSER"] if "PGUSER" in os.environ else "postgres"

    def get_engine(self):
        """
        returns the database connection engine to the databse
        """
        
        engine = sa.create_engine(f"postgresql://{self.pguser}:{self.pgpassword}@{self.database}:5432/trueprice")
        return engine