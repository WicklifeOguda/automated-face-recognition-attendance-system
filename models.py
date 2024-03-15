import uuid

from sqlalchemy import Column, String, Time

from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    reg_no = Column(String, index=True)
    first_name = Column(String)
    other_names = Column(String)


class Unit(Base):
    __tablename__ = "units"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    name = Column(String)
    code = Column(String, index=True)
    starts_at = Column(Time)
    ends_at = Column(Time)
