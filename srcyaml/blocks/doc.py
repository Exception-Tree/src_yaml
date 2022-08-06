import re
from pathlib import Path
from typing import List, Dict, Optional

from pydantic import BaseModel

from srcyaml import blocks


class Person(BaseModel):
    name: str
    position: str


class Title(BaseModel):
    header: str
    subheader: str
    number: str
    approved: Person
    agreed: List[Person]
    designed: List[Person]


class DocOptions(BaseModel):
    eskd_options: str = ''
    mode: str = ''

    def is_strict_mode(self):
        return self.mode == 'strict'


class Doc(BaseModel):
    name: str = 'gen'
    options: Optional[DocOptions]
    globals: Optional[Dict]
    sections: Optional[List[blocks.Section]] = []
    title: Optional[Title]
    referat: Optional[Path]
    out_path: Optional[Path]
    preprocess: Optional[blocks.Preprocess]  # TODO: Preprocess class

    @property
    def out_tex_file(self):
        return self.out_path / f'{self.name}'

    @property
    def out_pdf_file(self):
        return self.out_path / f'{self.name}.pdf'

    @property
    def amount(self):
        return sum([x.amount for x in self.sections])

    def __init__(self, **data):
        filtered = {'sections': [], 'options': {}}
        global_vars = {}
        if 'globals' in data:
            global_vars = data['globals']

        for key, value in data.items():
            if 'section' in key:
                res = re.findall(re.compile('section(\d+)'), key)
                sort = int(res[0])
                filtered['sections'].append(blocks.Section(raw_sections=value, global_vars=global_vars, sort=sort))
            elif 'preprocess' in key:
                filtered[key] = blocks.Preprocess(raw_sections=value, global_vars=global_vars)
                filtered[key].sort_by_depend()
            else:
                filtered[key] = value
        filtered['sections'].sort(key=lambda x: x.sort)
        super().__init__(**filtered)

