import sys
sys.dont_write_bytecode=True

from . import svc, local_config, package, mjm, config, resource, main_java, build_gradle, settings_gradle, tests

__all__ = ['svc', 'local_config', 'package', 'mjm', 'config', 'resource', 'main_java', 'build_gradle', 'settings_gradle', 'tests']
