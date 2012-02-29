"""
sentry_graphite
~~~~~~~~

:copyright: (c) 2012 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

import logging
from django import forms
from sentry.conf import settings
from sentry.plugins import Plugin, register
from greplin import scales
from greplin.scales import graphite

# from pystatsd import Client

NOTSET = object()


class GraphiteConfigurationForm(forms.Form):
    host = forms.CharField(max_length=64, required=False, 
             help_text="the host to which your scales will connect",
             widget=forms.TextInput(attrs={
                 'placeholder': '127.0.0.1',
            })
    )
    port = forms.IntegerField(max_value=65535, widget=forms.TextInput(attrs={
        'placeholder': '2003',
    }))
    prefix = forms.CharField(max_length=64, widget=forms.TextInput(attrs={
        'placeholder': 'sentry',
    }))


pusher = None


class GraphiteProcessor(Plugin):
    title = 'Graphite'
    conf_key = 'graphite'
    project_conf_form = GraphiteConfigurationForm

    def __init__(self, min_level=NOTSET, include_loggers=NOTSET, exclude_loggers=NOTSET,
                host=NOTSET, port=NOTSET, prefix=NOTSET, *args, **kwargs):

        super(GraphiteProcessor, self).__init__(*args, **kwargs)

        if min_level is NOTSET:
            min_level = getattr(settings, 'GRAPHITE_LEVEL', logging.DEBUG)
        if include_loggers is NOTSET:
            include_loggers = getattr(settings, 'GRAPHITE_INCLUDE_LOGGERS', None)
        if exclude_loggers is NOTSET:
            exclude_loggers = getattr(settings, 'GRAPHITE_EXCLUDE_LOGGERS', None)
        if host is NOTSET:
            host = getattr(settings, 'GRAPHITE_HOST', '127.0.0.1')
        if port is NOTSET:
            port = getattr(settings, 'GRAPHITE_PORT', 2444)
        if prefix is NOTSET:
            prefix = getattr(settings, 'GRAPHITE_PREFIX', 'sentry')

        self.min_level = min_level
        self.include_loggers = include_loggers
        self.exclude_loggers = exclude_loggers
        self.host = host
        self.port = port
        self.prefix = prefix

        # self.client = Client(host=self.host, port=self.port)
        self.stats = scales.collection('/sentry', scales.IntStat('totalEvents'),
                                  scales.IntDictStat('eventsByTop'))
        global pusher
        if pusher is None:
            pusher = graphite.GraphitePeriodicPusher(self.host, self.port, self.prefix)
            pusher.start()

    def record_event(self, group, event, fail_silently=True):
        # project = group.project

        # host = self.get_option('host', project) or self.host
        # port = self.get_option('port', project) or self.port
        # prefix = self.get_option('prefix', project) or self.prefix

        # key = '.'.join([prefix, event.message_top()])

        # self.client.increment(key)
        self.stats.totalEvents += 1
        self.stats.eventsByTop[event.message_top()] += 1

    def should_record(self, group, event):
        project = group.project
        host = self.get_option('host', project) or self.host
        if not host:
            return False
        port = self.get_option('port', project) or self.port
        if not port:
            return False
        prefix = self.get_option('prefix', project) or self.prefix
        if not prefix:
            return False
        min_level = self.get_option('min_level', project) or self.min_level
        if min_level is not None and int(group.level) < min_level:
            return False
        include_loggers = self.get_option('include_loggers', project) or self.include_loggers
        if include_loggers is not None and group.logger not in include_loggers:
            return False
        exclude_loggers = self.get_option('exclude_loggers', project) or self.exclude_loggers
        if exclude_loggers and group.logger in exclude_loggers:
            return False

        return True

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        if not self.should_record(group, event):
            return

        self.record_event(group, event)
 
register(GraphiteProcessor)
