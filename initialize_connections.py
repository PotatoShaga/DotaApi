from dotenv import load_dotenv
load_dotenv()
import os
from sqlalchemy import create_engine

# Add these parameters to your connection string
def initialize_engine():
    mysql_password = os.getenv("MYSQL_PASSWORD")
    connection_string = f"mysql+mysqlconnector://root:{mysql_password}@localhost:3306/dotaapi"
    engine = create_engine(connection_string, echo=False)

if __name__ == "__main__":
    initialize_engine()