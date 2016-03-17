# Make our own testrunner that by default only tests our own apps

from django.conf import settings
from django.test.runner import DiscoverRunner

class TripalocalTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        """ Override the database creation defined in parent class """
        pass

    def teardown_databases(self, old_config, **kwargs):
        """ Override the database teardown defined in parent class """
        pass

    #def build_suite(self, test_labels, *args, **kwargs):
    #    return super(TripalocalTestRunner, self).build_suite(test_labels or settings.PROJECT_APPS, *args, **kwargs)
