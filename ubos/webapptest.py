import inspect
import logging
import os
from importlib import import_module
import re

import sys
from ubos import commands, testplans, scaffolds



class AbstractTestPlan(object):

    def __init__(self, test, options):
        if not test:
            raise Exception('Must provide test')

        self.test = test

    def get_test(self):
        return self.test


#TestUtils
def find_app_tests_in_directory(directory):
    if not os.path.isdir(directory):
        raise Exception('Not a directory')

    app_test_candidates = os.listdir(directory)

    sys.path.append(directory)

    pysearchre = re.compile('.py$', re.IGNORECASE)

    pluginfiles = filter(pysearchre.search,
                         app_test_candidates)

    plugins = map(lambda fp: os.path.splitext(fp)[0], pluginfiles)

    modules = dict()

    for plugin in plugins:
        if not plugin.startswith("__"):
            import_module(plugin)
            for member, cls in inspect.getmembers(sys.modules[plugin], inspect.isclass):
                for base in cls.__bases__:
                    if base is AbstractTestPlan:
                        modules[member] = cls

    print(modules)
    return modules


def class_info_to_dict(info):
    result = dict()
    for class_name, cls in info:
        result[class_name] = cls

    return result


def find_commands():
    return class_info_to_dict(inspect.getmembers(sys.modules["ubos.commands"], inspect.isclass))


def find_testplans():
    return class_info_to_dict(inspect.getmembers(sys.modules["ubos.testplans"], inspect.isclass))


def find_scaffolds():
    return class_info_to_dict(inspect.getmembers(sys.modules["ubos.scaffolds"], inspect.isclass))


def find_testplan(name):
    plans = find_testplans()
    if plans.keys().__contains__(name):
        return plans[name]
    else:
        return None


def find_scaffold(name):
    plans = find_scaffolds()
    if plans.keys().__contains__(name):
        return plans[name]
    else:
        return None


def find_app_test_in_directory(directory, name):
    apps = find_app_tests_in_directory(directory)

    if apps.keys().__contains__(name):
        return apps.get(name)
    else:
        return None


def ask_user(question=None, interactive=True, success_of_last_step=True, success_of_plan_so_far=True):
    repeat = 0
    abort = 0
    qt = int(not success_of_last_step)

    if interactive:
        full_question = ""
        if question:
            full_question += question + " (" + "success" if success_of_last_step else "failure" + ")."
        else:
            full_question += "Last step " + "success" if success_of_last_step else "failure" + "."

        full_question += " C(ontinue)/R(epeat)/A(bort)/Q(uit)? "

        user_input = input(full_question)

        if user_input.lower() is "c":
            repeat = 0
            abort = 0
            qt = 0

        if re.compile("^\s*r\s*$").match(user_input):
            repeat = 1
            abort = 0
            qt = 0

        if re.compile("^\s*a\s*$").match(user_input):
            repeat = 0
            abort = 1
            qt = 0

        if re.compile("^\s*q\s*$").match(user_input):
            repeat = 0
            abort = 0
            qt = 1

    return repeat, abort, qt
