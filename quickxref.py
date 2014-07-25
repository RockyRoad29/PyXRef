#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Python /extrospection/. Inspecting modules without loading them.
#
#     Copyright (C) 2014 Michelle Baert ('RockyRoad')
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Python /extrospection/. Inspecting modules without loading them.

This utility will let you build a cross-reference report
within the scope of your project.
"""
import json
import re
import sys, os, subprocess, logging

__author__ = 'rockyroad'


def collect_sourcefiles(names, prefix=''):
    """
        >>> os.path.abspath(os.curdir)
        '/home/mich/Devlp/s2m/proto'
        >>> collect_sourcefiles(['manage.py', 'config.py', 'reqs.pip'])
        ['manage.py', 'config.py']
        >>> collect_sourcefiles(['manage.py', 'config.py', 'reqs.pip', 'app'])
        ['manage.py', 'config.py', 'app/__init__.py', 'app/routes.py']

        You may give redundant filenames, to essure order
        >>> collect_sourcefiles(['manage.py', 'config.py', 'reqs.pip', 'app/routes.py', 'app'])
        ['manage.py', 'config.py', 'app/routes.py', 'app/__init__.py']

        This project has much more files:
        >>> os.chdir('/home/mich/Learn/webauth/flask/flask-pycon2014')
        >>> c = collect_sourcefiles(['manage.py', 'config.py', 'app', 'tests'])
        >>> len(c)
        20

        ['manage.py', 'config.py', 'app/__init__.py', 'app/models.py', 'app/api_1_0/errors.py', 'app/api_1_0/__init__.py',
        'app/api_1_0/comments.py', 'app/emails.py', 'app/auth/forms.py', 'app/auth/__init__.py',
        'app/auth/routes.py', 'app/talks/forms.py', 'app/talks/__init__.py', 'app/talks/routes.py',
        'tests/__init__.py', 'tests/test_user_model.py', 'tests/test_pending_email_model.py',
        'tests/test_talk_model.py', 'tests/test_comment_model.py', 'tests/test_api.py']

        """
    results = []  # don't use set as they are unordered
    logging.info('collect_sourcefiles(%r, %r)', names, prefix)
    for name in names:
        path = prefix + name
        assert (os.path.exists(path))
        if os.path.isdir(path):
            results += collect_sourcefiles(os.listdir(path), prefix=path + '/')
        else:
            if name.endswith('.py'):
                results.append(path)
    # clean duplicates before last return
    if not prefix:
        clean = []
        for f in results:
            if f not in clean:
                clean.append(f)
        results = clean
    return results


def module_name(module_filename):
    """
    >>> module_name('manage.py')
    'manage'
    >>> module_name('app/talks/models.py')
    'app.talks.models'

    :param module_filename:
    :return:
    """
    assert (module_filename[-3:] == '.py')
    return module_filename[:-3].replace('/', '.')


def path_steps(module_name):
    """
    >>> path_steps('app.talks.models')
    ['app.talks.models', 'app.talks', 'app']
    """
    steps = module_name.split(".")
    locations = []
    q = module_name
    steps.reverse()
    for step in steps:
        locations.append(q)
        # remove last step from package path
        n = len(step) + 1
        q = q[:-n]
    return locations


def abs_package(ref, locations):
    """
    >>> abs_package('..views', ['app.talks.models', 'app.talks', 'app'])
    'app.views'
    >>> abs_package('.', ['app.api_1_0.__init__', 'app.api_1_0', 'app'])
    'app.api_1_0'
    """
    logging.debug('abs_package(%r,%r)', ref, locations)

    p = 0
    for c in ref:
        if c == '.':
            p += 1
            continue
        else:
            if p:
                base = locations[p]
                return base + '.' + ref[p:]
            else:
                return ref
    # if we get here we have an all-dots ref
    return locations[p]


def parse_imports(imports):
    """
    >>> parse_imports('generate_password_hash, check_password_hash, talks as talks_blueprint')
    ['generate_password_hash', 'check_password_hash', 'talks']
    """
    pat = re.compile(' *(.*?) as .*')
    objects = []
    for imp in imports.split(','):
        m = pat.match(imp)
        if m:
            imp = m.group(1)
        # assert(' ' not in imp)
        objects.append(imp.strip())
    return objects


class XRef:
    direct_import = re.compile('^ *import (?P<sources>.+)')
    selective_import = re.compile('^ *from (?P<source>.+?) import (?P<objects>.*)')

    def __init__(self, module_files=None):
        self.all_refs = {}
        self.xref = {}
        if module_files:
            # self.modules = {module_name(f): [] for f in module_files}
            self.module_list = [module_name(f) for f in module_files]
        else:
            self.module_list = None

    def add_target(self, target):
        logging.info("adding target %r", target)
        if target not in self.all_refs:
            self.all_refs[target] = []
        if self.module_list and target in self.module_list and target not in self.xref:
            self.xref[target] = []

    def add_entry(self, target, source, symbol=None):
        """
        >>> xr = XRef(['manage.py', 'config.py', 'app/__init__.py', 'app/routes.py'])
        >>> xr.add_target('app.__init__')
        >>> xr.add_entry('app.__init__', 'app.routes', 'whatever')
        >>> xr.add_entry('app.__init__', 'flask.ext.wtf', 'Form')
        >>> xr.all_refs
        {'app.__init__': ['app.routes.whatever', 'flask.ext.wtf.Form']}
        >>> xr.xref
        {'app.__init__': ['app.routes.whatever']}
        """
        logging.info("adding entry: %r", dict(target=target, source=source, symbol=symbol))
        assert ('/' not in source)
        obj = source
        if symbol:
            assert ('.' not in symbol)
            assert (symbol > ' ')
            obj += '.' + symbol
        self.all_refs[target].append(obj)
        # if self.modules and ((source in self.modules) or ((source + "__init__") in self.modules)):
        if self.module_list:
            if source in self.module_list:
                self.xref[target].append(obj)
            if (source + "__init__") in self.module_list:
                self.xref[target].append(obj)

    def add_imports(self, target, source, imports):
        """
        >>> xr = XRef()
        >>> xr.add_imports('app.__init__', '.talks', 'talks as talks_blueprint')
        >>> xr.all_refs
        {'app.__init__': ['app.talks.talks']}
        """
        location = path_steps(target)
        package = abs_package(source, location)
        self.add_target(target)
        if imports:
            symbols = parse_imports(imports)
            for sym in symbols:
                self.add_entry(target, package, sym)


    def add_imports_direct(self, target, sources):
        """
        >>> xr = XRef()
        >>> xr.add_imports_direct('hello.py', 'os,sys,re'.split(','))
        >>> xr.all_refs
        {'hello.py': ['os', 'sys', 're']}
        """
        location = path_steps(target)
        self.add_target(target)
        for source in sources:
            package = abs_package(source, location)
            self.add_entry(target, package)

    def parse_line(self, line, filename):
        """
        >>> xr = XRef()
        >>> xr.parse_line('import os, sys, re', 'hello.py')
        >>> xr.all_refs
        {'hello': ['os', 'sys', 're']}
        >>> xr.parse_line('from . import comments, errors', 'app/api_1_0/__init__.py')
        >>> xr.all_refs['app.api_1_0.__init__']
        ['app.api_1_0.comments', 'app.api_1_0.errors']
        """
        logging.info("Parsing : %r", line)
        target = module_name(filename)
        m = self.selective_import.match(line)
        if m:
            self.add_imports(target, m.group('source'), m.group('objects'))
        else:
            m = self.direct_import.match(line)
            if m:
                self.add_imports_direct(target, [s.strip() for s in m.group('sources').split(',')])

    def read_imports(self, module_filename):
        """
        >>> xr = XRef()
        >>> xr.read_imports('app/__init__.py')
        >>> xr.all_refs
        {'app.__init__': ['flask.Flask', 'routes.*']}
        """
        # return dict(package1=['obj1', 'obj2'],package1=['obj3', 'obj2'])

        logging.info('Analysing %r', module_filename)
        try:
            lines = subprocess.check_output(['grep', '^[^#]*import ', module_filename]).split("\n")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                logging.info("No imports in %r", module_filename)
                return
            else:
                raise e
        for line in lines:
            # remove comments
            if '#' in line:
                line = line[:line.index('#')]
            # remove extra commands ... FIXME hopefully import is first command in line
            if ';' in line:
                logging.warning('Multiple commands on import line : %r', line)
                line = line[:line.index(';')]
            self.parse_line(line, module_filename)

    def exclude_libs(self):
        """
        removes any xref entry external to project scope
        """

    def as_json(self, scoped=True):
        report = self.xref if scoped else self.all_refs
        return json.dumps(report, sort_keys=True, indent=4, separators=(',', ': '))

    def build_table(self):
        # modules = self.xref.keys()
        #modules.sort()
        # Based on supplied ordered list, remove unused.
        #modules = [ m for m in self.module_list if m in self.xref]
        modules = self.module_list
        headers = [''] + [m.replace('.__init__', '') for m in modules]
        table = []
        for target in modules:
            row = [[] for c in headers]
            if (target in self.xref):
                for obj in self.xref[target]:
                    logging.info("Placing %r in %r", obj, target)
                    if '.' in obj:
                        assert (obj[0] != '.')  # i.e. rindex won't return 0
                        p = obj.rindex('.')
                    else:
                        p = 0
                    src = obj[:p]  # 'hello'[:0] == ''
                    name = obj[p:]  # 'hello'[0:] == 'hello'
                    if not (src in headers):
                        logging.error("Error matching %r: %r not found in headers", obj, src)
                    c = headers.index(src)
                    logging.debug("%r found at %d for %r", src, c, obj)
                    row[c].append(dict(name=name, fullname=obj))
            else:
                logging.warning("Empty row for %r", target)
            table.append(row)
        return dict(headers=headers, table=table)

    def as_html(self, **kwargs):
        import jinja2

        wd = os.path.dirname(os.path.realpath(__file__))
        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(wd + '/templates')
        logging.info("Template search: %s", env.loader.searchpath)
        template = env.get_template('xref.html')
        # the template need to process headers and contents cells in parallel
        # env.globals[zip] = zip # doesn't work
        return template.render(data=self.build_table(), zip=zip, **kwargs)


def run(project_name, project_root, module_sources, reports_dir='/tmp'):
    """
    Analyses a project source and builds xref reports.
    """
    wd = os.path.realpath(os.curdir)
    os.chdir('%s' % project_root)
    module_files = collect_sourcefiles(module_sources)
    xr = XRef(module_files)
    for f in module_files:
        xr.read_imports(f)

    # restore initial working directory
    os.chdir(wd)
    base_report = reports_dir + '/xref_' + project_name
    with open(base_report + '.json', 'w') as f:
        f.write(xr.as_json())

    with open(base_report + '.html', 'w') as html:
        html.write(xr.as_html(project_root=project_root))


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format=('[%(lineno)d]%(levelname)s: %(message)s'))

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--project_root', help='Project root directory', default=os.curdir)
    parser.add_argument('-n', '--project_name', help='Project name (for reports)')
    parser.add_argument('sources', metavar='module_or_dir', nargs='+', help='Modules and directories file list')
    args = parser.parse_args()

    assert os.path.isdir(args.project_root)
    args.project_root = os.path.realpath(args.project_root)
    if not args.project_name:
        args.project_name = os.path.basename(args.project_root)
    logging.info('arguments: %r', args)

    # We put reports in static directory where the css and js reside.
    reports_dir =  os.path.realpath(os.path.join(os.path.dirname(__file__), 'static'))
    assert(os.path.isdir(reports_dir), 'Reports directory not found: ' + reports_dir)
    run(reports_dir=reports_dir, project_root=args.project_root, project_name=args.project_name,
        module_sources=args.sources)
