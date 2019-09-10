# -*- encoding: utf-8 -*-
"""
HubbleStack Nebula-to-graylog (http input) returner

Deliver HubbleStack Nebula query data into graylog using the HTTP input
plugin. Required config/pillar settings:

.. code-block:: yaml

hubblestack:
  returner:
    graylog:
      - port: 12202
        proxy: {}
        timeout: 10
        gelfhttp_ssl: True
        sourcetype_nebula: hubble_osquery
        sourcetype_pulsar: hubble_fim
        sourcetype_nova: hubble_audit
        gelfhttp: https://graylog-gelf-http-input-addr

"""

from __future__ import absolute_import

import json
import requests
import hubblestack.extmods.returners.common.graylog as graylog


def returner(ret):
    """
    Aggregates the configuration options related to graylog and returns a dict containing them.
    """
    # sanity check
    if not ret['return']:
        return

    opts_list = graylog.get_options('nebula')

    # Get cloud details
    cloud_details = __grains__.get('cloud_details', {})

    fqdn = __grains__['fqdn'] if __grains__['fqdn'] else ret['id']
    try:
        fqdn_ip4 = __grains__['fqdn_ip4'][0]
    except IndexError:
        fqdn_ip4 = __grains__['ipv4'][0]
    if fqdn_ip4.startswith('127.'):
        for ip4_addr in __grains__['ipv4']:
            if ip4_addr and not ip4_addr.startswith('127.'):
                fqdn_ip4 = ip4_addr
                break

    for opts in opts_list:

        for query in ret['return']:
            for query_name, value in query.items():
                for query_data in value['data']:
                    args = {'query': query_name,
                            'job_id': ret['jid'],
                            'minion_id': ret['id'],
                            'dest_host': fqdn,
                            'dest_ip': fqdn_ip4}
                    event = _generate_event(opts['custom_fields'], args, cloud_details, query_data)

                    payload = {'host': fqdn,
                               '_sourcetype': opts['sourcetype'],
                               'short_message': 'hubblestack',
                               'hubblemsg': event}

                    rdy = json.dumps(payload)
                    requests.post('{}:{}/gelf'.format(opts['gelfhttp'], opts['port']), rdy)
    return


def _generate_event(custom_fields, args, cloud_details, query_data):
    """
    Helper function that builds and returns the event dict
    """
    event = {}
    event.update(query_data)
    event.update(args)
    event.update(cloud_details)

    for custom_field in custom_fields:
        custom_field_name = 'custom_' + custom_field
        custom_field_value = __salt__['config.get'](custom_field, '')
        if isinstance(custom_field_value, str):
            event.update({custom_field_name: custom_field_value})
        elif isinstance(custom_field_value, list):
            custom_field_value = ','.join(custom_field_value)
            event.update({custom_field_name: custom_field_value})

    return event
