import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, String, Time
from sqlalchemy.orm import relationship

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
    reg_no = Column(String, index=True, unique=True)
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
    code = Column(String, index=True, unique=True)
    starts_at = Column(Time)
    ends_at = Column(Time)

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    student_id = Column(String,ForeignKey("students.id"))
    students = relationship("Student")
    unit_id = Column(String,ForeignKey("units.id"))
    units = relationship("Unit")
    time_taken = Column(TIMESTAMP, default=datetime.now, nullable=False)