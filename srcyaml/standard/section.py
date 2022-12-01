from pathlib import Path
from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field, Extra


class Item(BaseModel, extra=Extra.forbid):
    filename: Path = Field(alias="name")
    encoding: Optional[str] = 'utf-8'


class Image(Item):
    caption: str
    reference: str
    landscape: Optional[int] = False
    place: Optional[Literal['top', 'bottom', 'center', 'here']] = 'here'
    width: Optional[float] = 'auto'
    height: Optional[float] = 'auto'


class Table(Item):
    landscape: Optional[int] = False


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
                    elif 'table' in _item:
                        value = Table(**_item['table'])
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
