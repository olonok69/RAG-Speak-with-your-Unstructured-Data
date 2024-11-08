from pydantic import BaseModel, Field
from typing import List, Optional


class EntityDataExtraction(BaseModel):
    """Extract Information From Entities Sheet

    Args:
        BaseModel (_type_): _description_
    """

    Entity_Name: Optional[str] = Field(description="Name of Entity")
    Legal_Company_Type: Optional[str] = Field(description="Legal Company Type")
    Status: Optional[str] = Field(description="Status entity")
    Registration_Number_Tax_ID: Optional[int] = Field(
        description="Registration Number or Tax ID. This could be empty"
    )
    Incorporation_Date: Optional[str] = Field(
        description="The incorporation Date of the time period in ISO format."
    )
    country: Optional[str] = Field(description="Country")
    Region_State: Optional[str] = Field(description="Region / State")
    Dissolved_Date: Optional[str] = Field(
        description="The Dissolved Date of the time period in ISO format. This could be empty"
    )
    Historical: Optional[str] = Field(description="it is Historical TRUE or FALSE")
    Registered_Office_Address: Optional[str] = Field(
        description="The Registered Office Address of the company"
    )
    Main_Address_Line: Optional[str] = Field(
        description="The Main Address Line of the company"
    )
