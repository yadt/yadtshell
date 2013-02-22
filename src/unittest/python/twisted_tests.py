import unittest
from mock import Mock, call

from yadtshell.twisted import YadtProcessProtocol

class TwistedTests(unittest.TestCase):

    def test_out_received_should_append_data(self):
        mock_process_protocol = Mock(YadtProcessProtocol)
        mock_process_protocol.data = 'some-data-'
        mock_process_protocol.out_log_level = 'info'
        mock_process_protocol.pi = None
        mock_logger = Mock()
        mock_process_protocol.logger = mock_logger

        YadtProcessProtocol.outReceived(mock_process_protocol, '-more-data')

        self.assertEqual(mock_process_protocol.data, 'some-data--more-data')


    def test_out_received_should_update_progress_indicator_with_command_and_component(self):
        mock_progress_indicator = Mock()

        mock_process_protocol = Mock(YadtProcessProtocol)
        mock_process_protocol.data = ''
        mock_process_protocol.cmd = 'command'
        mock_process_protocol.component = 'component'
        mock_process_protocol.out_log_level = 'info'
        mock_process_protocol.pi = mock_progress_indicator
        mock_logger = Mock()
        mock_process_protocol.logger = mock_logger

        YadtProcessProtocol.outReceived(mock_process_protocol, 'data')

        self.assertEqual(call(('command', 'component')), mock_progress_indicator.update.call_args)

