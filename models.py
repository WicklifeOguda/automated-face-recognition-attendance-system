import uuid

from sqlalchemy import Column, String

from database import Base
from my_types import StudentSchema


class Student(Base):
    __tablename__ = "students"
    __pydantic_model__ = StudentSchema

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    reg_no = Column(String, primary_key=True, index=True)
    first_name = Column(String)
    other_names = Column(String)
