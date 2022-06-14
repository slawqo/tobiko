# Copyright 2022 Red Hat
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import argparse
from xml.etree import ElementTree


def main():
    parser = argparse.ArgumentParser(
        description='Remove testcases with no name '
                    'from the provided xml report file')
    parser.add_argument('--xmlfile', type=str, required=True,
                        help='XML report file path')
    args = parser.parse_args()

    report_tree = ElementTree.parse(args.xmlfile)
    report_root = report_tree.getroot()
    testsuite = report_root[0]
    new_testsuite = ElementTree.Element('testsuite')
    for testcase in testsuite:
        if 'name' in testcase.attrib:
            new_testsuite.append(testcase)
    new_testsuite.attrib = testsuite.attrib
    report_root[0] = new_testsuite
    report_tree.write(
        args.xmlfile, encoding="utf-8", xml_declaration=True)


if __name__ == '__main__':
    main()
