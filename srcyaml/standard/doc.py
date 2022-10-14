from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from srcyaml.standard import Preprocess


class Doc(BaseModel):
    out_path: Optional[Path]
    preprocess: Optional[Preprocess]

    def __init__(self, **data):
        values = {}

        global_vars = {}
        if 'globals' in data:
            global_vars = data['globals']

        for key, item in data.items():
            if 'preprocess' in key:
                values[key] = Preprocess(raw_sections=item, global_vars=global_vars)
            else:
                values[key] = item

        super().__init__(**values)

    def make_document(self):
        raise NotImplemented
