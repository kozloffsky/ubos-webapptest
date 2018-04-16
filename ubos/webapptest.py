import inspect
import logging
import os
import random
from importlib import import_module
import re
import sys


class AbstractTestPlan(object):

    def __init__(self, test, options):
        if not test:
            raise Exception('Must provide test')

        self.test = test

    def run(self, scaffold=False, interactive=False, verbose=False):
        raise NotImplementedError("Must override ubos.webapptest.AbstractTestPlan::run")

    def get_test(self):
        return self.test


class AbstractSingleSiteTestPlan(AbstractTestPlan):

    def __init__(self, test, options, tls_data):
        AbstractTestPlan.__init__(test, options)

        hostname = None

        if "siteJson" in options:
            if "appConfigJson" not in options:
                raise Exception("If specifying siteJson, you also need to specify appConfigJson")

            if "hostname" not in options:
                raise Exception("If specifying siteJson, you also need to specify hostname")

            if "context" not in options:
                raise Exception("If specifying siteJson, you also need to specify context")

            self.site_json = options['siteJson']
            self.app_config_json = options['siteConfigJson']

        elif "appConfigJson" in options:
            raise Exception("If specifying appConfigJson, you also need to specify siteJson")

        else:
            if "hostname" in options:
                if options["hostname"] != "*" and not re.compile("m!^[-.a-z0-9_]+$!").match(options["hostname"]):
                    raise Exception("Test plan hostname parameter must be a valid hostname, or *")

                hostname = options["hostname"]

            context = test.get_fixed_test_context()

            if context:
                if "context" in options:
                    logging.warning("Context " + options["context"] +
                                    " provided as argument to test plan ignored: WebAppTest requires fixed test context"
                                    )

            elif "context" in options:
                context = options["context"]
            else:
                context = "/ctxt-" + random_hex(8)

            if context != '' and not re.compile("m!^/[-_.a-z0-9%]+$!").match(context):
                raise Exception("'Context parameter must be a single-level relative path starting with a slash, "
                                "or be empty'")

            self.app_config_json = {
                'context': context,
                'appconfigid': "a" + random_hex(40),
                'appid': test.app_package_name()
            }

            if test.accessoryPackageNames():
                self.app_config_json['accessoryids'] = [test.accessoryPackageNames()]

            cust_point_values = test.get_customization_point_values()

            if cust_point_values:
                packages = test.accessory_package_names().copy().append(test.app_package_name())
                for package in packages:
                    if package in cust_point_values:
                        json_hash = dict()

                        for name in cust_point_values[package].keys():
                            value = cust_point_values[package][name]
                            json_hash[name] = {"value": value}

                        self.app_config_json["customizationpoints"] = {package: json_hash}

            admin = {
                "userid": "testuser",
                "username": "Test User",
                "credential": 's3cr3t',
                "email": 'testing.ignore.ubos.net'
            }

            self.site_json = {
                'siteid': 's' + random_hex(40),
                'hostname': hostname,
                'admin': admin,
                'appconfigs': [self.app_config_json]
            }
        if tls_data is not None:
            self.site_json["tls"] = tls_data

    def run(self, scaffold=False, interactive=False, verbose=False):
        raise NotImplementedError("Must override ubos.webapptest.AbstractSingleSiteTestPlan::run")

    def protocol(self):
        if "tls" in self.site_json:
            return "https"
        else:
            return "http"

    def hostname(self):
        return self.site_json["hostname"]

    def context(self):
        return self.app_config_json["context"]

    def site_id(self):
        self.app_config_json["appconfigid"]

    def get_site_json(self):
        return self.site_json

    def set_site_json(self, json):
        self.site_json = json

    def get_app_config_json(self):
        return self.app_config_json

    def set_app_config_json(self, json):
        self.app_config_json = json

    def get_admin_data(self):
        return self.site_json["admin"]


class TestContext(object):
    max_wait_till_ready = 60

    def __init__(self, scaffold, test_plan, verbose):
        self.scaffold = scaffold
        self.test_plan = test_plan
        self.verbose = verbose



# TestUtils

def random_hex(length):
    ('%030x' % random.randrange(16 ** 30))[:length]

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
    import ubos.commands
    return class_info_to_dict(inspect.getmembers(sys.modules["ubos.commands"], inspect.isclass))


def find_testplans():
    import ubos.testplans
    return class_info_to_dict(inspect.getmembers(sys.modules["ubos.testplans"], inspect.isclass))


def find_scaffolds():
    import ubos.scaffolds
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
