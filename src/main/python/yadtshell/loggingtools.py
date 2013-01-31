import os
import re
from yadtshell.helper import create_log_filename


def create_next_log_file_name(command_arguments,
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
    return create_log_filename(
        log_dir,
        target_name,
        command_start_timestamp,
        user_name,
        source_host,
        tag=tag
    )
