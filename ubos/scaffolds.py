from logging import info
from stat import S_ISLNK
from subprocess import call

import re

import os

from os import readlink

from ubos.webapptest import AbstractScaffold


class Here(AbstractScaffold):

    def __init__(self):
        AbstractScaffold.__init__(self)

    def setup(self, options):
        AbstractScaffold.setup(self, options)

        impersonate_depot = options["impersonatedepot"] if options and "impersonatedepot" in options else None

        info('Creating scaffold here')

        self._is_ok = self.handle_impersonate_depot(impersonate_depot)

    def backup_to_local(self, site, file_name):
        cmd = 'sudo ubos-admin backup'
        cmd += "--verbose" if self.verbose is 1 else ""
        cmd += " --siteid {siteid} --out {filename}".format(siteid=site['siteid'], filename=file_name)

        #TODO: run command


    def restore_from_local(self, site, file_name):
        cmd = 'sudo ubos-admin listsites'
        cmd += "--verbose" if self.verbose is 1 else ""
        cmd += ' --brief --backupfile ' + file_name;

        site_id_in_backup = ""

        #TODO: run command

        site_id_in_backup = site_id_in_backup.strip()
        cmd = 'sudo ubos-admin restore'
        cmd += "--verbose" if self.verbose is 1 else ""
        cmd += "--siteid {siteid} --hostname {hostname} --newsiteid {newsiteid} --in {filename}".\
            format(siteid=site_id_in_backup,
                   hostname=site['hostname'],
                   newsiteid=site['siteid'],
                   filename=file_name)

        #TODO exec command

        return 1

    def invoke_on_target(self, cmd, stdin, stdout, stderr):
        if self.verbose:
            if stdin:
                info('Scaffold {name} exec: {cmd} << INPUT\n{stdin}\nINPUT'
                     .format(name=self.name(),cmd=cmd, stdin=stdin))
            else:
                info('Scaffold {name} exec: {cmd}'
                     .format(name=self.name(),cmd=cmd))

        ret = 0 #TODO: execute command

        #if ret is 0 and stderr:
        #    if re.compile("^(FATAL|ERROR|WARNING):").match(stderr.__str__()):
        #        ret = - 999
        #    else:
        #        stderr = ''

        return ret

    def get_target_ip(self):
        return '127.0.0.1'

    def get_file_info(self, file_name, make_content_available):
        stat_info = os.stat(file_name)

        if not stat_info.st_dev:
            return None

        if make_content_available:
            if S_ISLNK(stat_info.st_mode):
                return stat_info.st_uid, stat_info.st_gid, stat_info.st_mode, readlink(file_name)
            else:
                return stat_info.st_uid, stat_info.st_gid, stat_info.st_mode, file_name

        return stat_info.st_uid, stat_info.st_gid, stat_info.st_mode

    def help(self):
        return 'A trivial scaffold that runs tests on the local machine without any insulation.'


