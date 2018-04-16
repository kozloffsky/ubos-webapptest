from logging import info

from ubos.webapptest import ask_user, TestContext
from .webapptest import AbstractSingleSiteTestPlan


class Default(AbstractSingleSiteTestPlan):

    def __init__(self, test, options, tls_data):
        AbstractSingleSiteTestPlan.__init__(self, test, options, tls_data)

    def run(self, scaffold=False, interactive=False, verbose=False):
        site_json = self.get_site_json()
        ret = 1
        success = 0
        repeat = 0
        abort = 0
        qt = 0
        deployed = 1

        while repeat:
            success = scaffold.deploy(site_json)
            repeat, abort, qt = ask_user('Performed deployment', interactive=interactive, success_of_last_step=success,
                                         success_of_plan_so_far=ret)
        ret = success
        deployed = success

        statesBackupsReverse = list()

        if not abort  and not qt:
            c = TestContext(scaffold=scaffold, test_plan=self, verbose=verbose)
            current_state = self.get_test().get_virgin_state_test()
            done = 0

            while not done:
                info('Checking StateCheck', current_state.get_name())

                while repeat:
                    success = current_state.check(c)

                    repeat, abort, qt = ask_user('Performed StateCheck', interactive, success, ret)

                ret = success

                if abort or qt:
                    return

                backup = scaffold.backup(site_json)

                statesBackupsReverse.insert(0, [current_state, backup])

                transition, nextState = self.get_test().get_transition_from(current_state)




