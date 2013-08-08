import unittest
from mock import Mock, call

from yadtshell.twisted import (YadtProcessProtocol,
                               _determine_issued_command,
                               report_error)


class TwistedTests(unittest.TestCase):


    def test_should_return_empty_string_when_failure_has_no_protocol_command(self):
        failure = lambda: None
        self.assertEqual(_determine_issued_command(failure), '')


    def test_should_return_protocol_command_with_trailing_at_symbol(self):
        failure = lambda: None
        failure.value = lambda: None
        failure.value.orig_protocol = lambda: None
        failure.value.orig_protocol.cmd = 'foobar'
        self.assertEqual(_determine_issued_command(failure), 'foobar@')


    def test_report_error_should_report_command_and_component(self):
        mock_line_fun = Mock()
        failure = lambda: None
        failure.getErrorMessage = lambda: 'You cannot stop the internet!'
        failure.value = lambda: None
        failure.value.orig_protocol = lambda: None
        failure.value.orig_protocol.cmd = 'stop'
        failure.value.component = 'internet'
        report_error(failure, line_fun=mock_line_fun)

        self.assertEqual(mock_line_fun.call_args, call('stop@internet: You cannot stop the internet!'))


    def test_report_error_should_report_failure_when_no_component_present(self):
        mock_line_fun = Mock()
        failure = lambda: None
        failure.value = lambda: None
        failure.getBriefTraceback = lambda: ''
        failure.getErrorMessage = lambda: 'Something has gone wrong'
        report_error(failure, line_fun=mock_line_fun)

        self.assertEqual(mock_line_fun.call_args,  call('Something has gone wrong'))


    def test_out_received_should_append_data(self):
        mock_process_protocol = Mock(YadtProcessProtocol)
        mock_process_protocol.data = 'some-data-'
        mock_process_protocol.component = 'component'
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



    def test_err_received_should_update_progress_indicator_with_command_and_component(self):
        mock_progress_indicator = Mock()

        mock_process_protocol = Mock(YadtProcessProtocol)
        mock_process_protocol.data = ''
        mock_process_protocol.cmd = 'command'
        mock_process_protocol.component = 'component'
        mock_process_protocol.err_log_level = 'info'
        mock_process_protocol.pi = mock_progress_indicator
        mock_logger = Mock()
        mock_process_protocol.logger = mock_logger

        YadtProcessProtocol.errReceived(mock_process_protocol, 'data')

        self.assertEqual(call(('command', 'component')), mock_progress_indicator.update.call_args)
