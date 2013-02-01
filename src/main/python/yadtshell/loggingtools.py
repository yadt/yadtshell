import os
import re

command_counter = 0


def create_next_log_file_name(log_dir, target_name, command_start_timestamp, user_name, source_host, tag=None):
    global command_counter

    log_file_name = '%(log_dir)s/yadtshell.%(target_name)s.%(command_start_timestamp)s.%(user_name)s.%(command_counter)03i.%(source_host)s' % {
        "log_dir": log_dir,
        "target_name": target_name,
        "command_start_timestamp": command_start_timestamp,
        "command_counter": command_counter,
        "user_name": user_name,
        "source_host": source_host,
    }

    if tag:
        log_file_name += '.' + tag

    log_file_name += '.log'

    command_counter += 1
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
