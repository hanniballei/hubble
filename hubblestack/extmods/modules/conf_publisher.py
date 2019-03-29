# -*- coding: utf-8 -*-
'''
Module to send config options to splunk
'''
import logging
import hubblestack.log
import copy
import time

log = logging.getLogger(__name__)


def publish(report_directly_to_splunk=True, remove_dots=True, *args):

    '''
    Publishes config to splunk at an interval defined in schedule

    report_directly_to_splunk
        Whether to emit directly to splunk in addition to returning as a normal
        job. Defaults to True.

    remove_dots
        Whether to replace dots in top-level keys with underscores for ease
        of handling in splunk. Defaults to True.

    *args
       Tuple of opts to log (keys in __opts__). Only those key-value pairs
       would be published, keys for which are in *args If not passed, entire
       __opts__ (excluding password/token) would be published

    '''
    log.debug('Started publishing config to splunk')

    opts_to_log = {}
    if not args:
        opts_to_log = copy.deepcopy(__opts__)
        if 'grains' in opts_to_log:
            opts_to_log.pop('grains')
    else:
        for arg in args:
            if arg in  __opts__:
                opts_to_log[arg] = __opts__[arg]

    filtered_conf = _filter_config(opts_to_log, remove_dots=remove_dots)

    if report_directly_to_splunk:
        hubblestack.log.emit_to_splunk(filtered_conf, 'INFO', 'hubblestack.hubble_config')
        log.debug('Published config to splunk')

    return filtered_conf


def _filter_config(opts_to_log, remove_dots=True):
    '''
    Filters out keys containing certain patterns to avoid sensitive information being sent to splunk
    '''
    patterns_to_filter = ["password", "token", "passphrase", "privkey", "keyid", "s3.key"]
    if remove_dots:
        for key in opts_to_log.keys():
            if '.' in key:
                opts_to_log[key.replace('.', '_')] = opts_to_log.pop(key)
    filtered_conf = _remove_sensitive_info(opts_to_log, patterns_to_filter)
    return filtered_conf


def _remove_sensitive_info(obj, patterns_to_filter):
    '''
    Filter known sensitive info
    '''
    if isinstance(obj, dict):
         obj = {
             key: _remove_sensitive_info(value, patterns_to_filter)
             for key, value in obj.iteritems()
             if not any(patt in key for patt in patterns_to_filter)}
    elif isinstance(obj, list):
         obj = [_remove_sensitive_info(item, patterns_to_filter)
                    for item in obj]
    return obj
