import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Union

#from mputils.hashmaker import HashMaker
from pydantic import BaseModel, Extra, Field


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


class Process(BaseModel):
    cmd: List[str]
    depend_on: Optional[str] = 'after'
    hash_by: Optional[List[str]]
    items: List[Dict]

    def __init__(self, *, raw_sections: Dict, global_vars: Dict, **data):
        values={'items':[]}
        for key, item in raw_sections.items():
            if 'items' in key:
                for i in item:
                    values[key].append(i)
            else:
                values[key] = item
        super().__init__(**values)

    @property
    def amount(self):
        return len(self.items)

    def process(self):
        proc_list = []
        for item in self.items:
            args = []
            for cmd_item in self.cmd:
                if cmd_item[0] == '$':
                    args.append(item[cmd_item[1:]])
                else:
                    args.append(cmd_item)
            p = subprocess.Popen(args)
            proc_list.append(p)
        return proc_list


class SubProcess(BaseModel):
    process: List[Process]

    def __init__(self, *, raw_sections: Dict, global_vars: Dict, **data):
        types = {
            'process': Process
        }
        values = []
        for item in raw_sections:
            for key, value in item.items():
                values.append(types[key](raw_sections=value, global_vars=global_vars))
        super().__init__(process=values)

    @property
    def amount(self):
        return sum([x.amount for x in self.process])

    def depend_on(self, name):
        values = []
        for item in self.process:
            if item.depend_on == name:
                values.append(item)
        return values


class GraphModel(BasePreProcess):
    process: List[File]


class TlmProc(BasePreProcess):
    exe_path: str
    process: List[File]

    @property
    def exe(self):
        return f'{self.exe_path}/tlmfileproc.exe'

    def cmd(self, input: Path, output: Path):
        return [self.exe, '-f', input, '-o', f'{output}.json', '--json']

    # def rebuild(self, hasher: HashMaker):
    #     if not hasher.compare_file(self.exe_path / 'tlmfileproc.exe'):
    #         hasher.save()
    #         return True
    #     return False


class Tlmpr(BasePreProcess):
    exe_path: Path
    xml: Path
    process: List[File]

    def cmd(self, input: Path, output: Path):
        return [Path(f'{self.exe_path}/tlmPr.exe').absolute(), '-d', input, '-o', output.parent, '-m', self.xml, '-v']

    # def rebuild(self, hasher: HashMaker):
    #     if not hasher.compare_file(self.xml) or not hasher.compare_file(self.exe_path / 'tlmPr.exe'):
    #         hasher.save()
    #         return True
    #     return False


class Preprocess(BaseModel):
    joiner: Optional[Joiner]
    graph: Optional[GraphModel]
    subprocess: Optional[SubProcess]
    customs: Optional[List[BasePreProcess]]

    items: Optional[List[BasePreProcess]]

    def __init__(self, *, raw_sections: List, global_vars: Dict, **data):
        types = {
            'joiner': Joiner,
            'graph': GraphModel,
            'subprocess': SubProcess
        }
        
        values = {'items': []}
        for item in raw_sections:
            key = item.keys()
            key = list(key)[0]
            _item = item[key]
            values['items'].append(types[key](raw_sections=_item, global_vars=global_vars))

        # for key, item in raw_sections.items():
        #     values[key] = types[key](raw_sections=item, global_vars=global_vars)
        #     values[key].name = types[key]
        super().__init__(**values)

    def append_custom(self, item: BasePreProcess):
        self.customs.append(item)

    def sort_by_depend(self):
        def sort_by_depend(left, right):
            return True
        #self.items.sort(key=sort_by_depend)
        firsts = []
        lasts = []
        others = []
        for index, item in enumerate(self.items):
            if item.name == 'first':
                firsts.append(item)
            elif item.name == 'last':
                lasts.append(item)
            else:
                others.append(item)

        self.items = firsts+others+lasts
        #for item in others:

    @property
    def amount(self):
        ret = 0
        for item in self.items:
            ret += item.amount
        return ret
