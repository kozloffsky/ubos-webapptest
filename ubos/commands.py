from os import getcwd

import ubos.webapptest


class Run(object):

    @classmethod
    def run(cls, args):
        print(args)

    @classmethod
    def synopsis_help(cls):
        return {
            "[--verbose | --logConfig <file>] [--interactive] [--scaffold <scaffold>] [--testplan <testplan>] [--tlskeyfile <tlskeyfile> --tlscrtfile <tlscrtfile>] <apptest>...": """
       Run the test apptest.

    --interactive: stop at important points and wait for user input

    <scaffold>:   use this named scaffold instead of the default. If given as

                  "abc:def=ghi:jkl=mno", "abc" represents the name of the scaffold,

                  and "def" and "jkl" are scaffold-specific options

    <testplan>:   use this named testplan instead of the default. If given as

                  "abc:def=ghi:jkl=mno", "abc" represents the name of the testplan,

                  and "def" and "jkl" are scaffold-specific options

    <tlskeyfile>, <tlscrtfile>: files containing TLS key certificate, and

                  all required certificates up the chain in one file if test

                  is supposed to be run with TLS

       """, "[--verbose | --logConfig <file>] --configfile <configfile> <apptest>...": """
         Run the test apptest.

    <configfile>: Read arguments from <configfile>, instead of from command-line

                  arguments. If arguments are provided on the command-line

                  anyway, they will override the values from the config file.

                  The config file must be a JSON file, in a hierarchical order

                  that corresponds to the command-line arguments and options for

                  scaffolds and testplans.
        """}


class ListAppTests(object):

    @classmethod
    def run(cls, args, **kwargs):
        app_tests = dict()
        if args:
            for directory in args:
                tests = ubos.webapptest.find_app_tests_in_directory(directory)
                if len(app_tests) is 0:
                    app_tests = tests.copy()
                else:
                    #merge two dicts
                    app_tests.update(tests.copy())
        else:
            app_tests = ubos.webapptest.find_app_tests_in_directory(getcwd())

        print(app_tests)

    @classmethod
    def synopsis_help(cls):
        return {
            '[ <dir> ]...': """
    Lists the available app tests in the specified directories.

    If no directory is given, lists the available app tests in

    the current directory.

    """}
