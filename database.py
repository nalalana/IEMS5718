from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import urllib
import pyodbc
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from passlib.context import CryptContext
from pydantic import BaseModel

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)

# 用于注册和登录
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# 工具函数
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


class Order(Base):
    __tablename__ = "orders"
    
    orderid = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="pending")  # pending, paid, completed, cancelled
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    digest = Column(String(255))
    paypal_transaction_id = Column(String(255), nullable=True)

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    orderid = Column(Integer, ForeignKey("orders.orderid"))
    pid = Column(Integer, ForeignKey("products.pid"))
    quantity = Column(Integer)
    price = Column(Float)  # 记录购买时的价格


