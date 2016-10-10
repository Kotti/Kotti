# -*- coding: utf-8 -*-
from pyramid.security import DENY_ALL
from repoze.workflow import get_workflow as base_get_workflow
import transaction

from kotti import TRUE_VALUES
from kotti import DBSession
from kotti.events import notify
from kotti.events import ObjectEvent
from kotti.resources import Content
from kotti.util import command


class WorkflowTransition(ObjectEvent):
    def __init__(self, obj, info, **kwargs):
        super(WorkflowTransition, self).__init__(obj, **kwargs)
        self.info = info


def get_workflow(context, name='security'):
    return base_get_workflow(context, name, context=context)


def reset_workflow(objs=None, purge_existing=False):
    if objs is None:
        objs = DBSession.query(Content)
    for obj in objs:
        if purge_existing:
            obj.state = None
        workflow = get_workflow(obj)
        if workflow is not None:
            workflow.reset(obj)
    transaction.commit()


def initialize_workflow(event):
    wf = get_workflow(event.object)
    if wf is not None:
        wf.initialize(event.object)


def workflow_callback(context, info):
    wf = info.workflow
    to_state = info.transition.get('to_state')

    if to_state is None:
        if context.state:
            to_state = context.state
        else:
            to_state = wf.initial_state

    state_data = wf._state_data[to_state].copy()
    acl = []

    # This could definitely be cached...
    special_roles = ('system.Everyone', 'system.Authenticated')
    for key, value in state_data.items():
        if key.startswith('role:') or key in special_roles:
            for perm in value.split():
                acl.append(("Allow", key, perm))

    if state_data.get('inherit', '0').lower() not in TRUE_VALUES:
        acl.append(DENY_ALL)

    context.__acl__ = acl

    if info.transition:
        notify(WorkflowTransition(context, info))


def reset_workflow_command():
    __doc__ = """Reset the workflow of all content objects in the database.

    This is useful when you want to migrate an existing database to
    use a different workflow.  When run, this script will reset all
    your content objects to use the new workflow, while trying to
    preserve workflow state information.

    For this command to work, all currently persisted states must map
    directly to a state in the new workflow.  As an example, if
    there's a 'public' object in the database, the new workflow must
    define 'public' also.

    If this is not the case, you may choose to reset all your content
    objects to the new workflow's *initial state* by passing the
    '--purge-existing' option.

    Usage:
      kotti-reset-workflow <config_uri> [--purge-existing]

    Options:
      -h --help          Show this screen.
      --purge-existing   Reset all objects to new workflow's initial state.
    """
    return command(
        lambda args: reset_workflow(purge_existing=args['--purge-existing']),
        __doc__,
        )
