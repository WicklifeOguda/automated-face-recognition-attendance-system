import uuid

from sqlalchemy import Column, String

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
