import re
from collections.abc import Mapping

from yamale import util
from yamale.validators import Validator, Map, List

validation_schema = """
report: report(include('name'),include('title', required=False),include('globals'),include('options'),preprocess(),include('all_sections'))
#report: map(report(),preprocess(),include('name'))
---
name: str()
title:
    header: str()
    subheader: str()
    approved:
        name: str()
        position: str()
    agreed: list()
    number: str()
options:
    eskd_options: str()
globals: map()
---
all_sections: list(include('file'))
---
file: map()
"""

"""
---
name: str()
---
globals: map(required=False)
---
title:
    header: str()
    subheader: str()
    approved:
        name: str()
        position: str()
    agreed: list()
    number: str()
---    
    options:
        eskd_options: str()
    preprocess: map(include('tlmpr', required=False), include('tlmproc', required=False), include('joiner', required=False), required=False)
    section0: include('section', required=False)
    section1: include('section', required=False)
    section2: include('section', required=False)
    section3: include('section', required=False)
    section4: include('section', required=False)
    section5: include('section', required=False)
    section6: include('section', required=False)
    section7: include('section', required=False)
    section8: include('section', required=False)
    section9: include('section', required=False)
---
tlmpr:
    exe_path: str()
    xml: str()
    process: list()
---
tlmproc:
    exe_path: str()
    xml: str()
    process: list()
---    
joiner:
    process: list()
---
section: list()
"""


class MPUtilsYAMLValidationReport(Map):
    tag = 'report'

    def __init__(self, *args, **kwargs):
        self.regexes = re.compile(r'section(\d+)')
        super(MPUtilsYAMLValidationReport, self).__init__(*args, **kwargs)
        self.validators = [val for val in args if isinstance(val, Validator)]

    def _is_valid(self, value):
        return isinstance(value, Mapping)

    def fail(self, value):
        return 'test'
        # return util.isstr(value) and self.regexes.match(value)


class MPUtilsYAMLValidationPreProcess(Validator):
    tag = 'preprocess'
    is_required = False

    def _is_valid(self, value):
        inner = ['joiner']
        if isinstance(value, dict):
            for item in inner:
                if item in value:
                    return True
        return isinstance(value, map)


class MPUtilsYAMLValidationSections(List):
    tag = 'sections'

    def _is_inner(self, value):
        inner = ['file', 'image', 'appendix', 'loop']
        for x in inner:
            if x in value:
                return True
        return False

    def _is_valid(self, value):
        if isinstance(value, list):
            for item in value:
                if not self._is_inner(item):
                    return False
            return True
        return False
