import os
import re

command_counter = 0


def create_next_log_file_name(log_dir, target_name, command_start_timestamp, user_name, source_host, tag=None):
    command_counter = get_command_counter_and_increment()

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

    print "%s %s %s %s %s %s" % (
        log_dir,
        target_name,
        command_start_timestamp,
        user_name,
        source_host,
        tag
    )

    return create_next_log_file_name(
        log_dir,
        target_name,
        command_start_timestamp,
        user_name,
        source_host,
        tag=tag
    )


def _strip_special_characters(tag):  # :*[]:*[]:*[]
    tag = re.sub('[:\*\[\]]*', '', tag).lower()
    return tag


def _trim_underscores(tag):
    tag = re.sub('^_', '', tag)
    tag = re.sub('_$', '', tag)
    return tag


def _strip_dashes(tag):
    tag = tag.replace('-', '')
    return tag


def _replace_uri_specific_characters_with_underscores(tag):
    tag = tag.replace('://', '_')
    tag = tag.replace('/', '_')
    return tag


def get_command_counter_and_increment():
    global command_counter

    current_command_counter = command_counter
    command_counter += 1

    return current_command_counter
