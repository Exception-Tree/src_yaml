from pathlib import Path
from typing import Optional, List, Literal, Union

from pydantic import BaseModel, Field, Extra


class Item(BaseModel):
    filename: Path = Field(alias="name")


class Image(Item):
    caption: str
    reference: str
    place: Optional[Literal['top', 'bottom', 'center', 'here']] = 'here'


class Table(Item):
    pass


class File(Item):
    items: Optional[List[Union[Image, Table]]]

    def __init__(self, **data):
        values = {'items': []}
        for key, item in data.items():
            if 'items' in key:
                for val in item:
                    if 'image' in val:
                        values['items'].append(Image(**val['image']))
            else:
                values[key] = item
        super().__init__(**values)

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
    sections: Optional[List[Section]]
