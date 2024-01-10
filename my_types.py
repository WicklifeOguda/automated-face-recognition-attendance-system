from pydantic import BaseModel, Field


class StudentSchema(BaseModel):
    id: str = Field(primary_key=True, title="StudentId")
    reg_no: str = Field(title="StudentRegNo")
    first_name: str = Field(title="StudentFirstName")
    other_names: str = Field(title="StudentOtherNames")

    class Config:
        from_attributes = True
