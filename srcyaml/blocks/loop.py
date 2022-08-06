from pydantic import BaseModel


class Loop(BaseModel):
    iterator: Dict
    process: Section
    pass