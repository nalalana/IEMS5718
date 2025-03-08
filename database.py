from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import urllib
import pyodbc

app = FastAPI()





params = urllib.parse.quote_plus(r'Driver={ODBC Driver 18 for SQL Server};Server=tcp:iems5718shop.database.windows.net,1433;Database=shop;Uid=nalalana;Pwd={240423Xdw};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
conn_str = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
engine = create_engine(conn_str,echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy base
Base = declarative_base()

# Database Models
class Category(Base):
    __tablename__ = "categories"
    catid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)

class Product(Base):
    __tablename__ = "products"
    pid = Column(Integer, primary_key=True, index=True)
    catid = Column(Integer, index=True)
    name = Column(String(255), index=True)
    price = Column(Float)
    image = Column(String)
    description = Column(String)

# Create tables if not exist
# Base.metadata.create_all(bind=engine)

# Pydantic Models for API
class CategoryCreate(BaseModel):
    name: str

class ProductCreate(BaseModel):
    catid: int
    name: str
    price: float
    image: str
    description: str


