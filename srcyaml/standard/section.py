from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, Extra


class Item(BaseModel):
    pass


class File(Item):
    filename: Path = Field(alias="name")


class Image(File):
    caption: str
    reference: str


class Section(BaseModel, extra=Extra.forbid):
    items: Optional[List[Item]]

    def __init__(self, **data):
        values = {'items': []}
        for key, item in data.items():
            if 'items' in key:
                for _item in data['items']:
                    if 'file' in _item:
                        value = File(**_item['file'])
                    elif 'image' in _item:
                        value = Image(**_item['image'])
                    else:
                        value = _item
                    values['items'].append(value)
            else:
                values[key] = item

        super().__init__(**values)

class SectionLoop(Section):
    pass


class Main(BaseModel):
    sections: Optional[List[Item]]
