import re
from pathlib import Path
from typing import Optional, List, Dict, Union

from pydantic import BaseModel, Extra
from report.utils.hashmaker import HashMaker
from report.utils.report_format import ReportFileFormat
from srcgraph import SrcGraph, SrcImageLine, SrcImageSubplots


class File(BaseModel):
    name: Path
    folders: Optional[List[Path]]
    outputs: Optional[List[Path]]

    def __init__(self, *, raw_sections: Dict, global_var: Union[Dict, List], **data):
        items = {}
        for key, item in raw_sections.items():
            items[key] = self.replace_item(item, global_var)

        if 'outputs' in items and items['outputs']:
            if not items['folders']:
                raise Exception('if you use outputs, you need folders')
            if len(items['folders']) != len(items['outputs']):
                raise Exception(f'length folders must same as length outputs')

        super().__init__(**items)

    def replace_item(self, item, global_vars: Union[Dict, List]):
        if isinstance(item, list):
            newitems = []
            for value in item:
                #first = re.findall(re.compile('\$globals.(.*)'), value)
                first = re.findall(re.compile('\$(.*)'), value)
                if not first:
                    newitems.append(value)
                    continue
                second = first[0].split('.')
                iterators = global_vars[second[0]]
                for it in iterators:
                    slash = second[1].split('/', maxsplit=1)
                    if len(slash) > 1:
                        v = f'{it[slash[0]]}/{slash[1]}'
                    else:
                        v = it[second[1]]
                    newitems.append(v)
            item = newitems
        return item

    @property
    def amount(self):
        return len(self.folders) if self.folders else 1


class BasePreProcess(BaseModel, extra=Extra.forbid):
    name: str #= Field()
    process: List[File]
    depend_on: Optional[str] = 'after'
    iterator: Optional[str]

    def __init__(self, *, raw_sections: Dict, global_vars: Dict, **data):
        values = {'process': []}

        global_var = None
        if 'iterator' in raw_sections:
            global_var = re.findall(re.compile('\$globals.(.*)'), raw_sections['iterator'])
            global_var = global_vars[global_var[0]]

        for key, item in raw_sections.items():
            if 'process' in key:
                for j in item:
                    values[key].append(File(raw_sections=j, global_var=global_var))
            else:
                values[key] = item
        super().__init__(**values)

    def cmd(self, *args, **kwargs):
        raise NotImplemented

    def make(self, tmp_folder, hasher: HashMaker):
        raise NotImplemented
    # def rebuild(self, hasher: HashMaker):
    #     return False

    @property
    def amount(self):
        return sum([x.amount for x in self.process])


class Joiner(BasePreProcess):
    process: List[File]
    regex: Optional[str]

    # def __init__(self, *, raw_sections: Dict, **data):
    #     #for key, item in raw_sections.items():

    def cmd(self):
        pass


class Converter(BasePreProcess):
    headers: dict

    def make(self, tmp_folder, hasher: HashMaker):
        converter = ReportFileFormat()
        for item in self.process:
            header = self.headers[item.name.name]
            if not hasher.compare_file(item.name):
                converter.from_csv(item.name, sep=';', header=header, with_column_names=True,
                                   output_file=tmp_folder / f'{item.name}.json')
        hasher.save()

    def cmd(self, *args, **kwargs):
        pass


class GraphConfig(BaseModel):
    type: str = 'line'
    xaxis: str
    reference: str
    line_shape_column: Optional[dict]


class Graph(BasePreProcess):
    configs: List[GraphConfig]

    def cmd(self):
        pass

    def make(self, tmp_folder, hasher: HashMaker):
        src_graph = SrcGraph('conf.json', '.')
        for idx, item in enumerate(self.process):
            image = None
            if self.configs[idx].type == 'line':
                image = SrcImageLine(item.name, self.configs[idx].reference, self.configs[idx].xaxis)
            elif self.configs[idx].type == 'subplots':
                line_shape = self.configs[idx].line_shape_column if self.configs[idx].line_shape_column else {}
                image = SrcImageSubplots(item.name, self.configs[idx].reference, self.configs[idx].xaxis,
                                         line_shape=line_shape)
            if image:
                src_graph.append(image, True)
        src_graph.save()


class Preprocess(BaseModel):
    items: Optional[List[BasePreProcess]]

    def __init__(self, *, raw_sections: List, global_vars: Dict, **data):
        types = {
            'joiner': Joiner,
            'graph': Graph,
            'convert': Converter
            #'subprocess': SubProcess
        }

        values = {'items': []}
        for item in raw_sections:
            key = item.keys()
            key = list(key)[0]
            _item = item[key]
            values['items'].append(types[key](raw_sections=_item, global_vars=global_vars))

        super().__init__(**values)

    @property
    def amount(self):
        ret = 0
        for item in self.items:
            ret += item.amount
        return ret

    # @property
    # def items(self):
    #     return self.items
