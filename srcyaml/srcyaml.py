import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Union

import yaml

from pydantic import parse_obj_as
from report import SimpleReportCreator, SimpleReportCreatorCallback
from report.g2_105.report_g2_105 import ReportG2105, ReportTitleG2105
from report.utils.hashmaker import HashMaker
from tqdm import tqdm
from loguru import logger

from srcyaml.standard import DocG2105
from srcyaml.standard import Preprocess
from srcyaml.blocks.preprocess import File, TlmProc, Tlmpr, BasePreProcess
#from mputilsyaml.blocks.section import SectionLoop

from collections import OrderedDict
#from shtatgraph.core.components.graphs import Graphs
#from shtatgraph.core.components.models import HiddenShtatConfig
#from shtatgraph.runner import silent_run
import datetime


class SimpleReportCreatorYaml(SimpleReportCreator):
    def __init__(self, callback: SimpleReportCreatorCallback):
        super().__init__(None, callback)
        self.__strict = False
        self.__doc: Optional[Dict] = None
        self.__options = None
        self.__hm: HashMaker = None
        self.tmp = None
        self.times: Dict[str, datetime.datetime] = OrderedDict()

    def __subprocess(self, pp: BasePreProcess, files: List[File], pbar: tqdm):
        procs = []
        params = []
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None

        rebuild_all = pp.rebuild(self.__hm)
        for file in files:
            if file.folders:
                if file.outputs:
                    for folder, output in zip(file.folders, file.outputs):
                        name = Path(f'{folder}/{file.name}').absolute().as_posix()
                        if rebuild_all or not self.__hm.compare_file(Path(name)):
                            out_name = (output / file.name.stem).absolute().as_posix()
                            params = pp.cmd(input=name, output=Path(out_name))
                            p = subprocess.Popen(params, stdout=subprocess.PIPE, startupinfo=startupinfo)
                            self.__hm.save()
                            procs.append((p, name))
                        else:
                            pbar.write(f'\nSkip another subprocess ({file})')
                            pbar.update()

                else:
                    for folder in file.folders:
                        name = Path(f'{folder}/{file.name}').absolute().as_posix()
                        if not Path(self.tmp / folder).absolute().exists():
                            Path(self.tmp / folder).absolute().mkdir(parents=True)
                        out_name = (self.tmp / folder / file.name.stem).absolute().as_posix()
                        params = pp.cmd(input=name, output=Path(out_name))
                        p = subprocess.Popen(params, stdout=subprocess.PIPE, startupinfo=startupinfo)
                        procs.append((p, name))
            else:
                name = file.name.absolute().as_posix()

                (self.tmp / file.name.parent).absolute().mkdir(parents=True, exist_ok=True)
                out_name = (self.tmp / file.name.stem).absolute().as_posix()
                params = pp.cmd(input=name, output=out_name)
                p = subprocess.Popen(params, stdout=subprocess.PIPE, startupinfo=startupinfo)
                procs.append((p, name))
        while procs:
            failed = []
            for p, name in procs:
                str = p.stdout.read()
                if p.poll() is not None:
                    if p.returncode:
                        failed.append(name)
                        self.__hm.remove(name)
                    p.stdout.close()
                    procs.remove((p, name))
                    pbar.update()
            if failed:
                self.__hm.save()
                failed_str = 'Failed process:'
                for name in failed:
                    failed_str += f'\t{name}\n'
                raise Exception(failed_str)

    def __preprocess(self, pp: Preprocess):
        try:
            pbar = tqdm(total=pp.amount, desc='preprocess', leave=False)

            for item in pp.items:
                # TODO: depend on
                print(item.name)
                item.make()
                pbar.update()

            # if pp.subprocess:
            #     for item in pp.subprocess.depend_on('before'):
            #         self.add_time(f'preprocess.subprocess.[{item.cmd}]')
            #
            #         procs = item.process()
            #         while procs:
            #             for proc in procs:
            #                 if proc.poll() is not None:
            #                     procs.remove(proc)
            #                     pbar.update()
            # if pp.joiner:
            #     self.add_time(f'preprocess.joiner')
            #     joiner = mp.joiner.Joiner()
            #     for file in pp.joiner.process:
            #         if file.outputs:
            #             for folder, output in zip(file.folders, file.outputs):
            #                 kts = joiner.list_kt_folders(folder)
            #                 rebuild = False
            #                 for kt in kts:
            #                     if not self.__hm.compare_file(Path(kt) / 'spool/telem.hex'):
            #                         rebuild = True
            #
            #                 if rebuild:
            #                     joiner.join(root=folder, output_path=output)
            #                     self.__hm.save()
            #                 else:
            #                     pbar.write(f'Joiner skips "{Path(kt)}"')
            #                 pbar.update()
            #         else:
            #             for folder in file.folders:
            #                 kts = joiner.list_kt_folders(folder)
            #                 rebuild = False
            #                 for kt in kts:
            #                     if not self.__hm.compare_dir(Path(kt)):
            #                         rebuild = True
            #                 if rebuild:
            #                     joiner.join(root=folder, output_path=self.tmp / folder)
            #                     self.__hm.save()
            #                 else:
            #                     pbar.write(f'Joiner skips "{Path(kt)}"')
            #                 pbar.update()
            #     if pp.subprocess:
            #
            #         for item in pp.subprocess.depend_on('joiner'):
            #             self.add_time(f'preprocess.subprocess.[{item.cmd}]')
            #             procs = item.process()
            #             while procs:
            #                 for proc in procs:
            #                     if proc.poll() is not None:
            #                         procs.remove(proc)
            #                         pbar.update()
            #
            # if pp.tlmproc:
            #     self.add_time(f'preprocess.tlmproc')
            #     self.__subprocess(pp.tlmproc, pp.tlmproc.process, pbar)
            #     if pp.subprocess:
            #         for item in pp.subprocess.depend_on('tlmproc'):
            #             procs = item.process()
            #             while procs:
            #                 for proc in procs:
            #                     if proc.poll() is not None:
            #                         procs.remove(proc)
            #                         pbar.update()
            #
            # if pp.tlmpr:
            #     self.add_time(f'preprocess.tlmpr')
            #     self.__subprocess(pp.tlmpr, pp.tlmpr.process, pbar)
            #     if pp.subprocess:
            #         for item in pp.subprocess.depend_on('tlmpr'):
            #             procs = item.process()
            #             while procs:
            #                 for proc in procs:
            #                     if proc.poll() is not None:
            #                         procs.remove(proc)
            #                         pbar.update()
            # if pp.shtatgraph:
            #     self.add_time(f'preprocess.shtatgraph')
            #     for file in pp.shtatgraph.process:
            #         if file.outputs:
            #             raise NotImplementedError('Чуть позже...')
            #         else:
            #             for folder in file.folders:
            #                 # if not self.__hm.compare_dir(Path(folder)):
            #                 silent_run(config_path=file.name, custom_graphs=Graphs(), custom_spool=folder,
            #                            output_folder=self.tmp / folder / 'pics')
            #                     # self.__hm.save()
            #                 # else:
            #                 #     pbar.write(f'shtatgraph skips "{Path(folder)}"')
            #
            # if pp.subprocess:
            #     for item in pp.subprocess.depend_on('after'):
            #         self.add_time(f'preprocess.subprocess.[{item.cmd}]')
            #         procs = item.process()
            #         while procs:
            #             for proc in procs:
            #                 if proc.poll() is not None:
            #                     procs.remove(proc)
            #                     pbar.update()

        except Exception as ex:
            if self.callback.exception(ex):
                raise

    # def __title(self, doc: blocks.Title):
    #     #title = ReportTitle(doc.header, doc.subheader, doc.number)
    #     if isinstance(super().report, ReportG2105):
    #         title = ReportTitleG2105(doc.header, doc.subheader)
    #     else:
    #         title = ReportTitleCommon()
    #     self.report.append(title)
    #     title.approvedBy(doc.approved.position, doc.approved.name)
    #     for agree in doc.agreed:
    #         title.appendAgreedBy(agree.position, agree.name)
    #     for designed in doc.designed:
    #         title.appendDesignedBy(designed.position, designed.name)
    #     return title

    # def __file(self, item: blocks.SectionFile):
    #     part = None
    #     if item.name.suffix != '.json':
    #         if item.folders:
    #             for folder in item.folders:
    #                 _out_path = self.tmp / folder / item.name.parent
    #                 _out_path.mkdir(parents=True, exist_ok=True)
    #                 part = ReportText((folder / item.name).as_posix(), landscape=item.landscape,
    #                                   font_size=item.font_size,
    #                                   out_path=_out_path, root_path=self.tmp)
    #                 self.report.add_part(part)
    #             part = None
    #         else:
    #             _out_path = self.tmp / item.name.parent
    #             _out_path.mkdir(parents=True, exist_ok=True)
    #             part = ReportText(item.name.as_posix(), landscape=item.landscape, font_size=item.font_size,
    #                               out_path=_out_path, root_path=self.tmp)
    #             self.report.add_part(part)
    #     else:
    #         if item.folders:
    #             for folder in item.folders:
    #                 part = mp.Utils.parse_telem_json((folder / item.name).as_posix(), encoding=item.encoding)
    #                 self.report.add_part(part)
    #             part = None
    #         else:
    #             part = mp.Utils.parse_telem_json(item.name.as_posix(), encoding=item.encoding)
    #     return part
    #
    # def __image(self, item: blocks.SectionImage):
    #     if item.folders:
    #         for folder in item.folders:
    #             (self.tmp / folder / item.name.parent).mkdir(parents=True, exist_ok=True)
    #             shutil.copy2(item.name, self.tmp / folder / item.name)
    #             part = ReportImage((self.tmp / folder / item.name).as_posix(),
    #                                caption=item.caption, root_path=self.tmp / folder)
    #             self.report.add_part(part)
    #         return None
    #     (self.tmp / item.name.parent).mkdir(parents=True, exist_ok=True)
    #     shutil.copy2(item.name, self.tmp / item.name)
    #     part = ReportImage((self.tmp / item.name).as_posix(),
    #                        caption=item.caption, root_path=self.tmp)
    #     return part
    #
    # def __shtatgraph(self, item: blocks.SectionShtatGraph):
    #     if item.folders:
    #         raise NotImplementedError(' это тоже чуточку позже...')
    #     # with item.name.open('r', encoding='utf8') as rf:
    #     #     _j = json.load(rf)[0]
    #     #     shtatconfig = parse_obj_as(HiddenShtatConfig, _j)
    #     #     report.add_part(mp.Utils.parse_telem_json(item.name, encoding='utf8'))
    #
    # def __section(self, items: List, pbar: tqdm):
    #     for item in items:
    #         try:
    #             part: Optional[JSONCommon] = None
    #             if item.key == 'loop':
    #                 item: SectionLoop
    #                 self.__section(item.items, pbar)
    #             elif item.key == 'file':
    #                 item: blocks.SectionFile
    #                 self.__file(item)
    #             elif item.key == 'image':
    #                 item: blocks.SectionImage
    #                 part = self.__image(item)
    #             elif item.key == 'graph':
    #                 item: blocks.SectionGraph
    #                 print(item)
    #
    #             elif item.key == 'table':
    #                 item: blocks.SectionTable
    #                 if item.folders:
    #                     for folder in item.folders:
    #                         input_file = folder / item.name
    #                         Path(f'{self.tmp}/{folder}/{item.name.parent}').mkdir(parents=True, exist_ok=True)
    #                         output_file = Path(f'{self.tmp}/{folder}/{item.name.stem}.json').absolute()
    #                         if item.name.suffix == '.csv':
    #                             j = JSONizer()  # TODO: refactor this
    #                             output = j.from_csv(input_file=input_file, output_file=output_file,
    #                                                 sep=';', with_column_names=True,
    #                                                 encoding=item.encoding)
    #                         elif item.name.suffix == '.json':
    #                             output = input_file
    #                         part = mp.Utils.parse_telem_json(output, encoding='utf-8')
    #                         part.title = item.caption
    #                         part.landscape = item.landscape
    #                         self.report.add_part(part)
    #                     part = None
    #                 else:
    #                     input_file = item.name
    #                     output_file = Path(f'{self.tmp}/{item.name.stem}.json').absolute()
    #                     if item.name.suffix == '.csv':
    #                         j = JSONizer()  # TODO: refactor this
    #                         output = j.from_csv(input_file=input_file, output_file=output_file,
    #                                             sep=';', with_column_names=True,
    #                                             encoding=item.encoding)
    #                     elif item.name.suffix == '.json':
    #                         output = input_file
    #                     part = mp.Utils.parse_telem_json(output, encoding='utf-8')
    #                     part.title = item.caption
    #                     part.landscape = item.landscape
    #
    #             elif item.key == 'appendix':
    #                 item: blocks.SectionAppendix
    #                 part = ReportAppendix(item.name, item.ref)
    #             elif item.key == 'shtatgraph':
    #                 item: blocks.SectionShtatGraph
    #                 part = self.__shtatgraph(item, self.report)
    #
    #             else:
    #                 print(f'Unknown param {item}')
    #             if part:
    #                 self.report.add_part(part)
    #             pbar.update()
    #             if self.__callback:
    #                 self.__callback.update(pbar.pos)
    #         except Exception as ex:
    #             if not self.__strict:
    #                 raise
    #             print(ex)
    #             pbar.update()

    def set_remote_server(self, *, host: str, port: int):
        from mputils.nettools import NetTools
        NetTools.set_processing_server(server=host, port=port)
    def add_time(self, key: str):
        if key in self.times:
            logger.warning(f'В times уже есть такой ключ: ({key}: {self.times[key]})')
        self.times[key] = datetime.datetime.now()

    def print_times(self):
        times = list(self.times.items())
        for i, (stage, t) in enumerate(times):
            if i:
                print(f'{stage: <30}{t - times[i-1][1]}')
            else:
                print(f'{stage}: {t}')
        print(f'END at {datetime.datetime.now()}')
        print(f'TOTAL TIME ELAPSED: {datetime.datetime.now() - times[0][1]}')

    def load(self, filename: Union[str, Path], remote: bool = False) -> bool:
        self.add_time('start')
        filename = Path(filename)
        with filename.open("r", encoding='utf-8') as stream:
            try:
                self.__doc = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                return False

        if 'report' not in self.__doc:
            self.callback.error(f'no report tag found')
            return False
        doc_report = self.__doc['report']
        if 'standard' not in doc_report:
            self.callback.error(f'no standard tag found')
            return False

        standards = {'g2-105': { 'report': ReportG2105, 'pedantic': DocG2105}, 'g7-32': None}
        if doc_report['standard'] not in standards:
            self.callback.error(f"unknown standard:{doc_report['standard']}")
            return False
        # report: ReportCommon
        # report = standards[doc_report['standard']]['report']()
        pedanticDoc = standards[doc_report['standard']]['pedantic']
        doc: pedanticDoc = parse_obj_as(pedanticDoc, self.__doc['report'])

        os.chdir(filename.parent)
        self.tmp = Path(f'.{filename.stem}garbage')
        if not self.tmp.exists():
            self.tmp.mkdir()

        self.__hm = HashMaker(path=self.tmp)

        #doc: blocks.Doc = parse_obj_as(blocks.Doc, self.__doc['report'])
        if not doc.out_path:
            doc.out_path = filename.parent

        # self.add_time('preprocess start')
        if doc.preprocess:
            self.callback.total = doc.preprocess.amount
            self.__preprocess(doc.preprocess)

        self.set_report(doc.make_document())
        self.generate_pdf()

        # if doc.title:
        #     self.__title(doc.title)

        # referat = ReportReferat(doc.referat) if doc.referat else None
        # doc.out_path.mkdir(exist_ok=True)
        # total = doc.amount
        #
        # if self.__callback:
        #     self.__callback.max(total)
        #
        # self.add_time('compile sections start')
        # pbar = tqdm(total=total, desc='sections process', position=0, leave=True)
        # for section in doc.sections:
        #     self.__section(section.items, pbar)
        # pbar.close()
        # self.add_time('generate latex file start')
        # ltx = self.report.generate()
        # line, res_filename = mp.Utils.generate_latex_wrap(''.join(ltx), title=title, referat=referat, filename=self.tmp / doc.name,
        #                                                   landscape=False, eskdx_options=doc.options.eskd_options)
        # self.add_time('generate pdf file start')
        #
        # mp.Utils.generate_pdf(res_filename, folder_map=self.tmp, silent=False, remote=remote)
        # (self.tmp / f'{doc.name}.pdf').replace(f'{doc.name}.pdf')
        # self.add_time('END')
        # self.print_times()
        #src.generate_pdf()
        return True
