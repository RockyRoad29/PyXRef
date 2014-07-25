#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file: {}
"""
Runs QuickXRef on my sample projects.

"""
import os
from quickxref import run

__author__ = 'rockyroad'


if __name__ == '__main__':
    project_set = [
        dict(
            project_name='flask-pycon2014',
            project_root='/home/mich/Learn/webauth/flask/flask-pycon2014',
            module_sources=['manage.py', 'config.py', 'app']),
        dict(
            project_name='flask-kit',
            project_root='/home/mich/Learn/webauth/flask/flask-kit',
            module_sources=[
                'app.py',
                'ext.py',
                'helpers.py',
                'manage.py',
                'settings.py',
                'testing.py',
                'base', 'info', 'flaskr']),
        dict(
            project_name='flask-chassis',
            project_root='/home/mich/Learn/webauth/flask/flask-chassis/src/',
            module_sources=[
                'runserver.py',
                'manage.py',
                'tests.py',
                'factories.py',
                'chassis',
            ]),
        dict(
            project_name='blueprintexample',
            project_root='/usr/local/src/flask/examples/blueprintexample/',
            module_sources=[
                'blueprintexample.py',
                'blueprintexample_test.py',
                'simple_page',
            ]),
        dict(
            project_name='flask-skeleton',
            project_root='/home/mich/Learn/webauth/flask/flask-skeleton/',
            module_sources=[
                'default_settings.py',
                'runserver.py',
                'shell.py',
                'skeleton',
            ]),
    ]

    for proj in project_set:
        reports_dir = os.path.realpath('static')
        assert(os.path.isdir(reports_dir), 'directory not found: ' + reports_dir)
        run(reports_dir=reports_dir, **proj)
