import os
import re
import logging

command_counter = 0


def configure_logger_output_stream_by_level(stderr_handler, stdout_handler):
    stdout_handler.setLevel(logging.INFO)
    stderr_handler.setLevel(logging.WARN)
    stderr_filter = ErrorFilter()
    stdout_filter = InfoFilter()
    stderr_handler.addFilter(stderr_filter)
    stdout_handler.addFilter(stdout_filter)


def create_next_log_file_name(log_dir, target_name, command_start_timestamp, user_name, source_host, tag=None):
    command_counter = _get_command_counter_and_increment()

    log_file_name = '%(log_dir)s/yadtshell.%(target_name)s.%(command_start_timestamp)s.%(user_name)s.%(command_counter)03i.%(source_host)s' % locals()

    if tag:
        log_file_name += '.' + tag

    log_file_name += '.log'
    return log_file_name


def create_next_log_file_name_with_command_arguments_as_tag(
                        log_dir,
                        target_name,
                        command_start_timestamp,
                        user_name,
                        source_host,
                        command_arguments):

    tag_args = command_arguments
    if os.path.basename(tag_args[0]) == 'yadtshell':
        tag_args = tag_args[1:]
    tag = '_'.join(tag_args)
    tag = _replace_uri_specific_characters_with_underscores(tag)
    tag = _strip_dashes(tag)
    tag = _strip_special_characters(tag)
    tag = _trim_underscores(tag)
    tag = _replace_blanks_with_underscores(tag)
    tag = _switch_characters_to_lower_case(tag)

    return create_next_log_file_name(
        log_dir,
        target_name,
        command_start_timestamp,
        user_name,
        source_host,
        tag=tag
    )


def _get_command_counter_and_increment():
    global command_counter

    current_command_counter = command_counter
    command_counter += 1

    return current_command_counter


def _strip_special_characters(tag):
    tag = re.sub("[:\*\[\]']*", '', tag)
    return tag


def _trim_underscores(tag):
    tag = re.sub('^_*', '', tag)
    tag = re.sub('_*$', '', tag)
    return tag


def _strip_dashes(tag):
    tag = tag.replace('-', '')
    return tag


def _replace_uri_specific_characters_with_underscores(tag):
    tag = tag.replace('://', '_')
    tag = tag.replace('/', '_')
    return tag


def _replace_blanks_with_underscores(text):
    return re.sub(' ', '_', text)


def _switch_characters_to_lower_case(text):
    return text.lower()


class ErrorFilter(logging.Filter):

    def filter(self, record):
        if record.levelno == logging.DEBUG or record.levelno == logging.INFO:
            return 0
        return 1


class InfoFilter(logging.Filter):

    def filter(self, record):
        if record.levelno == logging.WARN or record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            return 0
        return 1
