from os import getcwd

from ubos.webapptest import find_app_tests_in_directory


class Run(object):
    pass


class ListAppTests(object):

    def run(self, *args, **kwargs):
        app_tests = dict()
        if args:
            for directory in args:
                tests = find_app_tests_in_directory(directory)
                if len(app_tests) is 0:
                    app_tests = tests.copy()
                else:
                    #merge two dicts
                    app_tests.update(tests.copy())
        else:
            app_tests = find_app_tests_in_directory(getcwd())

        print(app_tests)

    def synopsis_help(self):
        return {
            '[ <dir> ]...': """
    Lists the available app tests in the specified directories.

    If no directory is given, lists the available app tests in

    the current directory.

    """}
