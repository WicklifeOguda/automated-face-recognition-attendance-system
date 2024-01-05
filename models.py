from sqlalchemy import Column, String

from database import Base


class Student(Base):
    __tablename__ = "students"
    reg_no = Column(String, primary_key=True, index=True)
    first_name = Column(String)
    other_names = Column(String)
