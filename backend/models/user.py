"""
User model for SQLAlchemy.
"""

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.sql import expression

from ..core.db import Base

class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, server_default=expression.true(), nullable=False)
    is_superuser = Column(Boolean, server_default=expression.false(), nullable=False)