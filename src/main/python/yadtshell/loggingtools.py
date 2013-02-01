import os
import re

command_counter = 0


def create_next_log_file_name(log_dir, target_name, started_on, user, host, tag=None):
    global command_counter
    log_file = '%s/yadtshell.%s.%s.%s.%03i.%s' % (log_dir, target_name, started_on, user, command_counter, host)
    command_counter += 1
    if tag:
        log_file = '%s.%s' % (log_file, tag)
    return '%s.log' % log_file


def create_next_log_file_name_with_command_arguments_as_tag(
                        command_arguments,
                        log_dir,
                        target_name,
                        command_start_timestamp,
                        user_name,
                        source_host):
    tag_args = command_arguments
    if os.path.basename(tag_args[0]) == 'yadtshell':
        tag_args = tag_args[1:]
    tag = '_'.join(tag_args)
    tag = tag.replace('://', '_')
    tag = tag.replace('/', '_')
    tag = tag.replace('-', '')
    tag = re.sub('[:\*\[\]]*', '', tag).lower()
    tag = re.sub('^_', '', tag)
    tag = re.sub('_$', '', tag)
    return create_next_log_file_name(
        log_dir,
        target_name,
        command_start_timestamp,
        user_name,
        source_host,
        tag=tag
    )
