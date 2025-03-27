from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = "mssql+pyodbc://GroupX:CepK837+Gy@mcruebs04.isad.isadroot.ex.ac.uk/BEMM459_GroupX?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(DATABASE_URL, connect_args={"driver": "ODBC Driver 17 for SQL Server"})

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
