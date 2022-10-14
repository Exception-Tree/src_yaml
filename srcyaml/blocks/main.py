from typing import Optional

from pydantic import BaseModel


class Person(BaseModel):
    position: str
    name: str


class TitleG2105(BaseModel):
    name: str
    company: str
    #approved: Person
    #agreed: List[Person]
    #designed: List[Person]


class MainG2105(BaseModel):
    title: Optional[TitleG2105]

    # def __init__(self, *, raw, **data):
    #     filtered = {}
    #     for key, item in raw:
    #         filtered[key] = item
    #     super().__init__(**filtered)
