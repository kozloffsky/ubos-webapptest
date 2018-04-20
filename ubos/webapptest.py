import inspect
import json
import logging
import os
import random
from importlib import import_module
import re
import sys


class BadArgumentError(Exception):
    pass


class StateTransitionBase(object):
    def __init__(self, name, func):
        self.name = name
        self.function = func


class StateCheck(StateTransitionBase):
    def __init__(self, name, func):
        if not name:
            raise BadArgumentError("All StateChecks must have a name.")

        if not isinstance(name, str):
            raise BadArgumentError("A StateCheck\'s name must be a string.")

        if not function:
            raise BadArgumentError('All StateChecks must have a check function.')

        if not callable(func):
            raise BadArgumentError('A StateCheck\'s check function must be a Perl subroutine.')

        StateTransitionBase.__init__(self, name, func)

    def check(self, c):
        c.clear_http_session()

        try:
            self.function(c)
        except Exception as e:
            pass










class WebAppTest(object):
    def __init__(self, app_to_test=None, accessories_to_test: list=[], name=None, fixed_test_context=None, description=""
                 ,customization_point_values=[], checks=None, package_dbs_to_add: dict = {}):
        app_package_name = app_to_test
        accessory_package_names = accessories_to_test

        if not app_package_name:
            raise BadArgumentError('AppTest must identify the application package being tested. Use parameter named '
                                   '"app_to_test".')

        if accessory_package_names and not isinstance(accessory_package_names, list):
            raise BadArgumentError('If accessoriesToTest is given, it must be an array of package names')

        if not isinstance(name, str):
            raise BadArgumentError('AppTest name name must be a string.')

        if fixed_test_context:
            if not isinstance(fixed_test_context, str):
                raise BadArgumentError('AppTest testContext name must be a string.')

            if fixed_test_context is not "" and not re.match("^/[-_.a-z0-9%]+$", fixed_test_context):
                raise BadArgumentError('AppTest fixedTestContext must be a single-level relative path starting with a '
                                       'slash, or be empty')

        if not isinstance(description, str):
            raise BadArgumentError("AppTest description name must be a string.")

        if package_dbs_to_add and not isinstance(package_dbs_to_add, dict):
            raise BadArgumentError("AppTest packageDbsToAdd must be a hash, mapping section name to URL")

        if customization_point_values:
            if not isinstance(customization_point_values, dict):
                raise BadArgumentError("CustomizationPointValues must be a hash")

            for package in customization_point_values:
                values_for_package = customization_point_values[package]

                if not isinstance(values_for_package, dict):
                    raise BadArgumentError("Entries in CustomizationPointValues reference a hash of name-value paris")

        if checks is None:
            raise BadArgumentError('AppTest must provide at least a StateCheck for the virgin state')

        i = 0
        for candidate in checks:
            if i%2:
                if not isinstance(candidate, StateTransitionBase):
                    raise BadArgumentError('Array of StateChecks and StateTransitions must alternate: expected '
                                           'StateTransition')
            else:
                if not isinstance(candidate, StateCheck):
                    raise BadArgumentError('Array of StateChecks and StateTransitions must alternate: expected '
                                           'StateCheck')
            i += i+1

        if not len(checks) % 2:
            raise BadArgumentError('Array of StateChecks and StateTransitions must alternate and end with a '
                                   'StateCheck.')

        self.name = name
        self.description = description
        self.app_package_name = app_package_name
        self.accessory_package_names = accessory_package_names
        self.package_dbs_to_add = package_dbs_to_add
        self.fixed_test_context = fixed_test_context
        self.customization_point_values = customization_point_values
        self.states_transitions = checks

    def get_virgin_state_test(self):
        return self.states_transitions[0]

    def get_transition_from(self, to_state):
        counter = 0
        for state in self.states_transitions:
            if state == to_state:
                return self.states_transitions[counter + 1], self.states_transitions[counter + 2]
            i = i+1
        return None


class AbstractScaffold(object):

    def __init__(self):
        self.verbose = 0
        self._is_ok = False

    def setup(self, options):
        if options and "verbose" in options:
            self.verbose = options["verbose"]
        else:
            self.verbose = 0

    def is_ok(self):
        return self._is_ok

    def name(self):
        return __package__ + self.__class__

    def deploy(self, site):
        json_string = json.dump(site)

        logging.info("Site JSON: "+ json_string)

        cmd = "sudo ubos-admin deploy --stdin "
        cmd += "--verbose" if self.verbose is 1 else ""

        return not self.invoke_on_target(cmd, json_string)

    def undeploy(self, site):
        json_string = json.dump(site)

        logging.info("Site JSON: " + json_string)

        cmd = "sudo ubos-admin undeploy "
        cmd += "--verbose " if self.verbose is 1 else ""
        cmd += "--siteid " + site["siteid"]

        return not self.invoke_on_target(cmd)

    def update(self):
        cmd = "sudo ubos-admin update "
        cmd += "--verbose" if self.verbose is 1 else ""

        return not self.invoke_on_target(cmd)

    def switch_channel_update(self, new_channel, verbose, cmd):
        if not cmd:
            cmd = "sudo ubos-admin update "
            cmd += "--verbose" if self.verbose is 1 else ""

        script = "echo "+ new_channel+ " > /etc/ubos/channel"
        script += cmd

        out_p = None

        ext = self.invoke_on_target("sudo /bin/bash ", script, out_p, out_p)

        if ext:
            if verbose:
                logging.error("Channel switch failed:" + "script:\n"+ script+"\n")
            else:
                logging.error("Channel switch failed:" + "script:\n" + script + "\n" + out_p +"\n")

        return not ext

    def backup(self, site):
        cmd = 'F=$(mktemp webapptest-XXXXX.ubos-backup);'
        cmd += ' sudo ubos-admin backup'
        cmd += "--verbose" if self.verbose is 1 else ""
        cmd += ' --siteid ' + site-["siteid"] + ' --force --out $F';
        cmd += ' echo $F'

        file = ""

        ext = self.invoke_on_target(cmd, None, file)

        if not ext:
            file = file.strip()
            return file
        else:
            logging.error("Backup failed")
            return 0

    def backup_to_local(self, site, file_name):
        raise NotImplementedError("Mut be overriden by child")

    def restore(self, site, identifier):
        cmd = 'sudo ubos-admin restore'
        cmd += "--verbose" if self.verbose is 1 else ""
        cmd += ' --siteid ' + site["siteid"]+' --in ' + identifier

        return not self.invoke_on_target(cmd)

    def restore_from_local(self, site, file_name):
        raise NotImplementedError("Mut be overriden by child")

    def destroy_backup(self, site, identifier):
        return not self.invoke_on_target('rm '+identifier)

    def teardown(self):
        return 0

    def invoke_on_target(self, cmd, stdin, stdout, stderr):
        raise NotImplementedError("Mut be overriden by child")

    def get_target_ip(self):
        raise NotImplementedError("Mut be overriden by child")

    def get_file_info(self, file_name, make_content_available):
        raise NotImplementedError("Mut be overriden by child")

    def handle_impersonate_depot(self, ip):
        cmd = """use strict;
use warnings;
        
use Ubos::Utils;

my $ip="""+ip if ip is not None else "undef"+""";
unless( -r '/etc/hosts' ) {

    print STDERR "Cannot read /etc/hosts\\n";

    exit 1;

}

my $etchosts = UBOS::Utils::slurpFile( '/etc/hosts' );

if( $etchosts ) {

    if( defined( $ip )) {

        unless( $etchosts =~ m!depot\.ubos\.net! ) {

            $etchosts .= <<ADD;

# webapptest added

$ip depot.ubos.net

ADD

            UBOS::Utils::saveFile( '/etc/hosts', $etchosts, 0644, 'root', 'root' );

        }

    } else {

        my $changed = 0;

        if( $etchosts =~ s!# webapptest added\s*!! ) {

            $changed = 1;

        }

        my $ipEsc = quotemeta( $ip );

        if( $etchosts =~ s!$ipEsc\s+depot\.ubos\.net!! ) {

            $changed = 1;

        }

        if( $changed ) {

            UBOS::Utils::saveFile( '/etc/hosts', $etchosts, 0644, 'root', 'root' );

        }

    }

    exit 0;



} else {

    print STDERR "/etc/hosts is empty. Not changing\n";

    exit 1;

}

1;"""

        out = object()
        err = object()
        if self.invoke_on_target('sudo /bin/bash -c /usr/bin/perl', cmd, out, err):
            logging.error("Failed to edit /etc/hosts file to add depot.ubos.net:\nout:{out}\nerr:{err}\ncmd:{cmd}"
                          .format(out=out, err=err, cmd=cmd))
            return 0
        #elif re.compile("/Respect the privacy of others/").match(err):
        #    logging.error("Failed to edit /etc/hosts file to add depot.ubos.net. sudo problem:",
        #                  out, err)
        #    return 0
        return 1

    def install_additional_package_dbs(self, repos: dict):
        if len(repos) is 0:
            return 1

        logging.info("Installing additional package dbs:", repos.keys())

        cmd = """
use strict
use warnings;


use UBOS::Utils;
        """

        for name in repos.keys():
            url = repos[name]
            cmd += """
UBOS::Utils::saveFile( '/etc/pacman.d/repositories.d/$name', <<'DATA' );

[{name}]

Server = {url}

DATA
            """.format(name=name, url=url)

        cmd += """
UBOS::Utils::myexec( "ubos-admin update" );


1;
        """

        out = object()
        err = object()

        if self.invoke_on_target('sudo /bin/bash -c /usr/bin/perl', cmd, out, err):
            logging.error("Failed to add repositories:\nout:{out}\nerr:{err}\ncmd:{cmd}"
                          .format(out=out, err=err, cmd=cmd))
            return 0

        return 1













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
    if name in plans.keys():
        return plans[name]
    else:
        return None


def find_scaffold(name: str):
    plans = find_scaffolds()
    if name in plans.keys():
        return plans[name]
    else:
        return None


def find_app_test_in_directory(directory, name):
    apps = find_app_tests_in_directory(directory)
    if name in apps.keys():
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
