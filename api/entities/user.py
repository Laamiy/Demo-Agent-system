# api/models.py (or wherever your models live)
from api.deps.core import Base
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text
from typing import List

class User(Base):
    __tablename__ = "users"
    
    uid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    rides: Mapped[List["Ride"]] = relationship("Ride", back_populates="user")  # <-- added

class Order(Base):
    __tablename__ = "orders"
    
    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.uid"), nullable=False)
    item: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    total: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="MGA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="orders")

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cuisine: Mapped[str] = mapped_column(String(50), nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_time: Mapped[str] = mapped_column(String(20), default="30 min")
    menu: Mapped[str] = mapped_column(Text, default="[]")

class Ride(Base):
    __tablename__ = "rides"
    
    ride_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.uid"), nullable=True)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    pickup: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="confirmed")
    price: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="MGA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="rides")