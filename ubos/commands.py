import getopt
import json
import re
from argparse import ArgumentParser
from logging import info
from optparse import OptionParser
from os import getcwd

import ubos.webapptest
from ubos.webapptest import find_scaffold, find_testplan, find_app_test_in_directory, ask_user


class Run(object):

    @classmethod
    def run(cls, args):
        print("Run args", args)

        parser = ArgumentParser()
        parser.add_argument("--configfile", action="store", dest="config_file")
        parser.add_argument("--interactive", dest="interactive")
        parser.add_argument("--verbose", dest="verbose")
        parser.add_argument("--logConfig", dest="log_config")
        parser.add_argument("--scaffold", dest="scaffold_opts")
        parser.add_argument("--testplan", dest="testplan_opts")
        parser.add_argument("--tlskeyfile", dest="tls_key_file")
        parser.add_argument("--tlscrtfile", dest="tls_crt_file")

        config = parser.parse_args(args)

        print("Config", config)
        config_data = []

        if config.config_file:
            json_file = open(config.config_file)
            config_data = json.load(json_file)

            if not config.interactive and "interactive" in config_data:
                config.interactive = config_data["interactive"]

            if not config.verbose and "verbose" in config_data:
                config.verbose = config_data["verbose"]

            if not config.log_config and "logConfig" in config_data:
                config.log_config = config_data["logConfig"]

            if not config.tls_key_file and "tlsKeyFile" in config_data:
                config.tls_key_file = config_data["tlsKeyFile"]

            if not config.tls_crt_file and "tlsCrtFile" in config_data:
                config.tls_crt_file = config_data["tlsCrtFile"]

        tls_data = dict()

        if "tls_key_file" in config and "tls_crt_file" in config and config.tls_crt_file and config.tls_key_file:
            tls_data["key"] = open(config.tls_key_file).read()
            tls_data["crt"] = open(config.tls_crt_file).read()

        scaffold_packages_with_options = dict()

        if config.scaffold_opts:
            for scaffold_opt in config.scaffold_opts:
                scaffold_name, scaffold_options = decode(scaffold_opt)
                scaffold_package = find_scaffold(scaffold_name)
                if not scaffold_package:
                    raise ModuleNotFoundError("Cannot find scaffold" + scaffold_name)

                if scaffold_package in scaffold_packages_with_options:
                    raise Exception("Cannot run the scaffold multiple times at this time")

                scaffold_packages_with_options[scaffold_package] = scaffold_options

        if config and config_data and "scaffold" in config_data:
            for scaffold_name in config_data["scaffold"].keys():
                scaffold_package = find_scaffold(scaffold_name)

                if not scaffold_package:
                    raise ModuleNotFoundError("Cannot find scaffold" + scaffold_name)

                # don't do duplicates check; command-line might override

                scaffold_options = config_data["scaffold"][scaffold_name]

                for option in scaffold_options.keys():
                    if option not in scaffold_packages_with_options[scaffold_package]:
                        scaffold_packages_with_options[scaffold_package] = scaffold_options[option]

        if len(scaffold_packages_with_options.keys()) is 0:
            here = find_scaffold('Here')
            print(here)
            scaffold_packages_with_options[here] = None

        print('Found scaffold(s)', scaffold_packages_with_options.keys())

        test_plan_packages_with_args_to_run = dict()

        if config.testplan_opts:
            for test_plan_opt in config.testplan_opts:
                test_plan_name, test_plan_options = decode(test_plan_opt)

                if not test_plan_name:
                    test_plan_name = 'default'

                test_plan_package = find_testplan(test_plan_name)

                if not test_plan_package:
                    raise Exception("Cannot find test plan " + test_plan_name)

                if test_plan_package in test_plan_packages_with_args_to_run:
                    raise Exception("Cannot run the same test plan multiple times at this time")

                test_plan_packages_with_args_to_run[test_plan_package] = test_plan_options

        if config_data and "testPlan" in config_data:
            for test_plan_name in config_data['testPlan'].keys():
                test_plan_package = find_testplan(test_plan_name)

                if not test_plan_package:
                    raise Exception("Cannot find test plan " + test_plan_name)

                # don't do duplicates check; command-line might override

                test_plan_options = config_data["testPlan"][test_plan_name]

                for option in test_plan_options.keys():
                    if option not in test_plan_packages_with_args_to_run[test_plan_package]:
                        test_plan_packages_with_args_to_run[test_plan_package]["option"] = test_plan_options[option]

        if len(test_plan_packages_with_args_to_run.keys()) == 0:
            test_plan = find_testplan('Default')
            test_plan_packages_with_args_to_run[test_plan] = None

        print('Found test plan(s) ', test_plan_packages_with_args_to_run.keys())

        app_test_to_run = list()

        for app_test_name in ['Test']:
            app_test_to_run.append(find_app_test_in_directory(getcwd(), app_test_name))
            if not app_test_to_run:
                raise Exception("Cannot find app test " + app_test_name)

        ret = 1
        success = 0
        repeat = 1
        abort = 0
        qt = 0

        for scaffold_package in scaffold_packages_with_options:
            scaffold_options = scaffold_packages_with_options[scaffold_package]

            while repeat is 1:
                print('Scaffold->setup', scaffold_package)
                scaffold = scaffold_package()
                scaffold.setup(scaffold_options)
                if scaffold.is_ok:
                    success = 1
                else:
                    success = 0

                repeat, abort, qt = ask_user('Setting up scaffold', config.interactive, success, ret)

                if success and not repeat and not abort:
                    print_test = len(app_test_to_run) > 1
                    print_test_plan = len(test_plan_packages_with_args_to_run.keys()) > 1

                    for app_test in app_test_to_run:
                        if print_test:
                            print("Running AppTest " + app_test.name)

                        #scaffold.init_additional_package_dbs(app_test.get_package_dbs_to_add())









        print(config)

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


def decode(string: str):
    parts = string.split(":")
    name = parts[0]
    options = dict()

    for part in parts[1:]:
        if part:
            options[part.lower()] = part.lower()

    return name, options

