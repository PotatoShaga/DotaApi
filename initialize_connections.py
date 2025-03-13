from dotenv import load_dotenv
load_dotenv()
import os
from sqlalchemy import create_engine

# Generates a engine to make connections with. Simply pass as parameter and use with
def initialize_engine():
    mysql_password = os.getenv("MYSQL_PASSWORD")
    connection_string = f"mysql+mysqlconnector://root:{mysql_password}@localhost:3306/dotaapi"
    engine = create_engine(connection_string, echo=False)
    return engine 

if __name__ == "__main__":
    initialize_engine()