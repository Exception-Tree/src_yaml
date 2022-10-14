from typing import Optional, List, Literal

from pydantic import BaseModel

from srcyaml.standard.section import Item, Section, Main, File, Image


class Person(BaseModel):
    position: str
    name: str


class TitleG2105(BaseModel):
    name: str
    company: str
    #approved: Person
    #agreed: List[Person]
    #designed: List[Person]


class AppendixG2105(Section):
    type: Literal['обязательное','информационное']
    caption: str
    reference: str
    #items: Optional[List[Item]]

    # def __init__(self, **data):
    #     values = {'items': []}
    #     for key, item in data.items():
    #         if 'items' in key:
    #
    #             # for i in item:
    #             #     if 'file' in i:
    #             #         values['items'].append(File(**i['file']))
    #             #     elif 'image' in i:
    #             #         values['items'].append(Image(**i['image']))
    #         else:
    #             values[key] = item
    #
    #     super().__init__(**values)

class MainG2105(Main):
    title: Optional[TitleG2105]
    appendixes: Optional[List[AppendixG2105]]

    def __init__(self, **data):
        values = {'sections': [], 'appendixes': []}
        for key, item in data.items():
            if 'sections' in key:
                for skey, sitem in item.items():
                    if 'section' in skey:
                        values['sections'].append(Section(items=sitem))
                    elif 'appendix' in skey:
                        values['appendixes'].append(AppendixG2105(**sitem))
            else:
                values[key] = item
        super().__init__(**values)
