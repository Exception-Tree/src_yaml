import json

from report.common.report_image_common import ReportImageCommon, ReportImageCommonParam
from report.common.report_list_common import ReportListCommon
from report.common.report_table_common import ReportTableCommon
from report.common.report_text_common import ReportTextCommon
from report.g2_105.report_appendix_g2_105 import ReportAppendixG2105
from report.g2_105.report_g2_105 import ReportG2105, ReportTitleG2105

from srcyaml.standard import Preprocess
from srcyaml.standard.doc import Doc
from srcyaml.standard.g2105.main import MainG2105
from srcyaml.standard.section import File, Image, Section, Table


class DocG2105(Doc):
    main: MainG2105

    def __init__(self, **data):
        filtered = {}

        for key, item in data.items():
            if 'main' in key:
                filtered[key] = MainG2105(**item)
            else:
                filtered[key] = item
        # global_vars = {}
        #
        # if 'globals' in data:
        #     global_vars = data['globals']
        #
        # for key, item in data.items():
        #     if 'preprocess' in key:
        #         filtered[key] = Preprocess(raw_sections=item, global_vars=global_vars)
        #     elif 'standard' in key:
        #         pass
        #     else:
        #         filtered[key] = item

        super().__init__(**filtered)

    def make_document(self):
        report = ReportG2105()
        if self.main.title:
            title = ReportTitleG2105(title=self.main.title.title, doc_name=self.main.title.name,
                                     company=self.main.title.company, signature=self.main.title.signature)
            report.append(title)
        if self.main.sections:
            sections = ReportListCommon()
            for section in self.main.sections:
                self.__make_section(sections, section)
            report.append(sections)
        if self.main.appendixes:
            for ap in self.main.appendixes:
                appendix = ReportAppendixG2105(ap.type, ap.caption, ap.reference)
                for item in ap.items:
                    val = None
                    if isinstance(item, Image):
                        item: Image
                        image_param = ReportImageCommonParam(item.width, item.height, item.place, item.landscape)
                        val = ReportImageCommon(item.filename, item.caption, item.reference, image_param)
                    elif isinstance(item, File):
                        item: File
                        val = ReportTextCommon(item.filename)
                    if val:
                        appendix.append(val)
                report.append(appendix)
        return report

    def __make_section(self, new_section: ReportListCommon, section: Section):
        for item in section.items:
            new_item = None
            if isinstance(item, Image):
                item: Image
                image_param = ReportImageCommonParam(item.width, item.height, item.place, item.landscape)
                new_item = ReportImageCommon(item.filename, item.caption, item.reference, image_param)
            elif isinstance(item, File):
                item: File
                new_item = ReportTextCommon(item.filename)
                for value in item.items:
                    if isinstance(value, Image):
                        image_param = ReportImageCommonParam(value.width, value.height, value.place, value.landscape)
                        new_item.append(ReportImageCommon(value.filename, value.caption, value.reference, image_param))
                    elif isinstance(value, Table):
                        value: Table
                        with open(value.filename, encoding=value.encoding) as file:
                            json_dict = json.load(file)
                            _new_item = ReportTableCommon(json_dict, landscape=value.landscape)
                            if value.title:
                                _new_item.title = value.title
                            _new_item.reference = value.reference
                            new_item.append(_new_item)
            elif isinstance(item, Table):
                item: Table
                with open(item.filename, encoding=item.encoding) as file:
                    json_dict = json.load(file)
                    new_item = ReportTableCommon(json_dict, landscape=item.landscape)
                    new_item.reference = item.reference
            if new_item:
                new_section.append(new_item)
