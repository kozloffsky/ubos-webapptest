
from .webapptest import AbstractSingleSiteTestPlan


class Default(AbstractSingleSiteTestPlan):

    def __init__(self, test, options, tls_data):
        AbstractSingleSiteTestPlan.__init__(self, test, options)

    def run(self, scaffold=False, interactive=False, verbose=False):
        site_json = self.get_site_json()

    def get_site_json(self):
        pass

