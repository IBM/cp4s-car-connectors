from car_framework.inc_import import BaseIncrementalImport
from car_framework.util import IncrementalImportNotPossible


# This is to disable context().fooMember error in IDE
# pylint: disable=no-member

class IncrementalImport(BaseIncrementalImport):
    def run(self):
        raise IncrementalImportNotPossible('Connector doesn\'t support incremental import.')