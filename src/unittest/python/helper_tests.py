import unittest

import yadtshell

from yadtshell.helper import condense_hosts
from yadtshell.helper import condense_hosts2


class HelperTests(unittest.TestCase):


    def test_condense_hosts(self):
        TARGET_SETTINGS = {
          'hosts': ["foobar01","foobar02", "foobar03", "bazbar01", "bazbar02", "bazbar03"]}
	result = ' '.join(condense_hosts2(condense_hosts(TARGET_SETTINGS['hosts'])))
        condensed_hosts = '{baz,foo}bar[01..03]'
	self.assertEqual(result, condensed_hosts)

