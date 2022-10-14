import copy
import re
from pathlib import Path
from typing import List, Optional, Dict, Literal

from pydantic import BaseModel, parse_obj_as, validator, ValidationError


class BaseSection(BaseModel):
    inside_loop: bool = False


class SectionType(BaseModel):
    name: Path
    key: str
    ref: Optional[str]
    folders: Optional[List] = None
    use_in: Optional[List[str]]
    landscape: bool = False
    encoding: str = 'utf-8'

    @property
    def amount(self):
        return 1


class SectionImage(SectionType):
    key = 'image'
    caption: str


class SectionTable(SectionType):
    key = 'table'
    caption: str
    with_header: Optional[bool]



class SectionGraph(SectionType):
    key = 'graph'
    caption: str


class SectionFile(SectionType):
    key = 'file'
    tmp: bool = False
    font_size: Literal['small', 'normal', 'large'] = 'normal'

    @validator('name')
    def check_file_extentions(cls, v: Path):
        extentions = ['.md', '.json', '.csv']
        if v.suffix not in extentions:
            raise ValueError(
                f'В поле "name" элемента типа "file" допустимы следующие типы файлов: {", ".join(extentions)} '
                f'(Текущее значение: "{v}")')
        return v

    def __init__(self, *strings, **data):
        if strings:
            name = strings[0]
            assert isinstance(name, str)
            data['name'] = name
        super().__init__(**data)


class SectionShtatGraph(SectionType):
    key = 'shtatgraph'
    name: Path
    folders: Optional[List] = None


class SectionAppendix(SectionType):
    key = 'appendix'
    name: str


class BaseSection(BaseModel):
    items: Optional[List[SectionType]] = []
    types: Dict = {}

    @property
    def amount(self):
        return sum([x.amount for x in self.items])

    def __init__(self, *, raw_sections: Dict, types: Dict, global_vars: Dict, **data):
        _sections = []

        for key, value in raw_sections.items():
            if key == 'items':
                for dict_item in value:
                    name, item = list(dict_item.items())[0]
                    if name == 'loop':
                        _sections.append(types[name](raw_sections=item, global_vars=global_vars))
                    else:
                        _sections.append(parse_obj_as(types[name], item))
                    #_sections = value

        # for name, item in [list(x.items())[0] for x in raw_sections]:
        #     if name == 'loop':
        #         _sections.append(types[name](raw_sections=item, global_vars=global_vars))
        #     else:
        #         _sections.append(parse_obj_as(types[name], item))
        super().__init__(items=_sections, types=types, **data)


class Section(BaseSection):
    items: List[SectionType]

    def __init__(self, *, raw_sections: List[Dict], **data) -> None:
        """My custom init!"""
        types = {'loop': SectionLoop, **TYPES}
        super().__init__(raw_sections=raw_sections, types=types, **data)


def replace_globals(item, replacers: Dict, keyword: str):
    def parse_string(it: str):
        keywords = re.findall(re.compile(f'\${keyword}(\.[.\w]+)'), it)
        for k in keywords:
            word = {**replacers}
            try:
                for y in [i for i in k.split('.') if i]:
                    word = word[y]
            except Exception as e:
                print(e)
                word = 'FAILED'
            it = it.replace(f'${keyword}{k}', word)
        return it

    if isinstance(item, str):
        item = parse_string(item)
    elif isinstance(item, dict):
        for key, value in item.items():
            item[key] = replace_globals(item[key], replacers, keyword)
    elif isinstance(item, list):
        item = [replace_globals(foo, replacers, keyword) for foo in item]
    return item


class SectionLoop(SectionType, BaseSection):
    key: Optional[str] = 'loop'
    name: Optional[str]
    iterator: Dict

    @property
    def amount(self):
        return sum([x.amount for x in self.items])

    def __init__(self, *, raw_sections: Dict, global_vars: Dict, **data) -> None:
        key, global_val = list(raw_sections['iterator'].items())[0]
        global_val = re.findall(re.compile('\$globals.(.*)'), global_val)
        if len(global_val) == 0:
            raise Exception("Atata")
        new_items = []
        if not global_val[0] in global_vars.keys():
            raise Exception(f"'{global_val[0]}' missed in report.globals")
        if global_vars[global_val[0]]:
            for mode in global_vars[global_val[0]]:
                items = copy.deepcopy(raw_sections['items'])
                for item in items:
                    ret = replace_globals(item, mode, keyword=key)
                    new_items.append(ret)

                # for item in [x for x in raw_sections['items'] if 'iterator' not in x]:
                #     #ret = {**item}
                #     ret = item.copy()
                #     new_items.append(replace_globals(ret, mode, keyword=key))

        super().__init__(raw_sections=new_items, iterator=raw_sections['iterator'], types=TYPES, key='loop',
                         global_vars=global_vars, **data)


TYPES = {
    'image': SectionImage,
    'file': SectionFile,
    'appendix': SectionAppendix,
    'shtatgraph': SectionShtatGraph,
    'table': SectionTable
}

if __name__ == '__main__':
    mode = {"name": 'NAME', "ref": 'New Ref', "fort54": "some complex param",
            "bar": {'foo': "Nested"}}
    strings = {
        "$mode.name": "NAME",
        "$mode.name $mode.name": "NAME NAME",
        "$mode.name.fjekf": "FAILED",
        "$mode.ref": "New Ref",
        "$mode.ref/slash": "New Ref/slash",
        "$mode.bar.foo": "Nested",
        "$mode.bar.foo $mode.bar.foo": "Nested Nested",
        "$mode.fort54": "some complex param",
    }
    for st in strings:
        a = {'q': {'n': st}, 'rce': [12345, '123545', {'omg': "$mode.name"}]}
        print('Было:  ', a)
        b = replace_globals(a, mode, 'mode')
        print("Стало: ", a, '\n')
        assert a['q']['n'] == strings[st]
