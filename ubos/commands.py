import getopt
import json
import re
from argparse import ArgumentParser
from optparse import OptionParser
from os import getcwd

import ubos.webapptest


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

