from mock import patch
from pyramid.security import ALL_PERMISSIONS
from zope.configuration import xmlconfig

from kotti.testing import Dummy
from kotti.testing import EventTestBase
from kotti.testing import FunctionalTestBase
from kotti.testing import UnitTestBase


class TestWorkflow(EventTestBase, UnitTestBase):
    def setUp(self):
        super(TestWorkflow, self).setUp()
        import kotti
        xmlconfig.file('workflow.zcml', kotti, execute=True)

    def test_workflow_callback(self):
        from kotti.workflow import workflow_callback

        context = Dummy(__acl__=[])
        info = Dummy()
        info.transition = {"to_state": "next_state"}
        info.workflow = Dummy()
        info.workflow.initial_state = 'bar'
        info.workflow._state_data = {
            "next_state": {
                "role:me": "myfirstpermission mysecondpermission",
                "role:you": " \t yourpermission ",
                },
            }
        workflow_callback(context, info)

        self.assertEqual(sorted(context.__acl__), [
            ('Allow', 'role:me', 'myfirstpermission'),
            ('Allow', 'role:me', 'mysecondpermission'),
            ('Allow', 'role:you', 'yourpermission'),
            ('Deny', 'system.Everyone', ALL_PERMISSIONS),
            ])

    def test_workflow_callback_with_inheritance(self):
        from kotti.workflow import workflow_callback

        context = Dummy(__acl__=[])
        info = Dummy()
        info.transition = {"to_state": "next_state"}
        info.workflow = Dummy()
        info.workflow.initial_state = 'bar'
        info.workflow._state_data = {
            "next_state": {
                "role:me": "myfirstpermission mysecondpermission",
                "role:you": " \t yourpermission ",
                "inherit": "true",
                },
            }
        workflow_callback(context, info)

        self.assertEqual(sorted(context.__acl__), [
            ('Allow', 'role:me', 'myfirstpermission'),
            ('Allow', 'role:me', 'mysecondpermission'),
            ('Allow', 'role:you', 'yourpermission'),
            ])

    def test_workflow_callback_event(self):
        from kotti.events import listeners
        from kotti.events import ObjectEvent
        from kotti.workflow import workflow_callback
        from kotti.workflow import WorkflowTransition

        events = []
        my_listener = lambda event: events.append(event)
        listeners[WorkflowTransition].append(my_listener)

        context = Dummy()
        info = Dummy()
        info.transition = {"to_state": "next_state"}
        info.workflow = Dummy()
        info.workflow.initial_state = 'bar'
        info.workflow._state_data = {"next_state": {}}
        workflow_callback(context, info)

        self.assertEqual(len(events), 1)
        [event] = events
        self.assertEqual(event.object, context)
        self.assertEqual(event.info, info)
        assert isinstance(event, ObjectEvent)


class TestResetWorkflow(UnitTestBase):
    def call(self, *args, **kwargs):
        from kotti.workflow import reset_workflow
        return reset_workflow(*args, **kwargs)

    def test_workflow_reset_calls(self):
        objs = [Dummy(), Dummy()]

        with patch('kotti.workflow.get_workflow') as get_workflow:
            wf = get_workflow.return_value
            self.call(objs)
            assert wf.reset.call_count == 2
            assert wf.reset.call_args_list[0][0][0] is objs[0]
            assert wf.reset.call_args_list[1][0][0] is objs[1]

    def test_reset_purge_existing(self):
        dummy = Dummy(state='partying')
        self.call([dummy], purge_existing=True)
        assert dummy.state is None

    def test_reset_no_purge(self):
        dummy = Dummy(state='partying')
        self.call([dummy], purge_existing=False)
        assert dummy.state == 'partying'


class TestResetWorkflowCommand(UnitTestBase):
    def test_it(self):
        from kotti.workflow import reset_workflow_command

        with patch('kotti.workflow.command') as command:
            with patch('kotti.workflow.reset_workflow') as reset_workflow:
                reset_workflow_command()
                func, doc = command.call_args[0]
                func({'--purge-existing': True})
                reset_workflow.assert_called_with(purge_existing=True)


class TestDefaultWorkflow(FunctionalTestBase):
    def setUp(self):
        from kotti.resources import get_root

        super(TestDefaultWorkflow, self).setUp()
        self.root = get_root()

    def make_document(self):
        from kotti import DBSession
        from kotti.resources import Document

        content = self.root['document'] = Document()
        DBSession.flush()
        DBSession.refresh(content)
        return content

    def test_workflow_root(self):
        from kotti.workflow import get_workflow

        wf = get_workflow(self.root)
        assert wf.name == u'simple'
        assert self.root.state == u'public'

    def test_workflow_new_content(self):
        from kotti.workflow import get_workflow

        content = self.make_document()
        wf = get_workflow(content)
        assert wf.name == u'simple'
        assert content.state == u'private'
        assert content.__acl__[0] == (
            'Allow', 'role:admin', ALL_PERMISSIONS)
        assert content.__acl__[-1] == (
            'Deny', 'system.Everyone', ALL_PERMISSIONS)

    def test_workflow_transition(self):
        from kotti.workflow import get_workflow
        content = self.make_document()
        wf = get_workflow(content)
        wf.transition_to_state(content, None, u'public')
        assert content.state == u'public'

    def test_reset_workflow(self):
        from kotti.workflow import get_workflow
        from kotti.workflow import reset_workflow

        content = self.make_document()
        wf = get_workflow(content)
        wf.transition_to_state(content, None, u'public')
        assert content.state == u'public'
        save_acl = content.__acl__
        content.__acl__ = []
        reset_workflow()
        assert content.state == u'public'
        assert len(content.__acl__) == len(save_acl)

    def test_reset_workflow_purge_existing(self):
        from kotti.workflow import get_workflow
        from kotti.workflow import reset_workflow

        content = self.make_document()
        wf = get_workflow(content)
        wf.transition_to_state(content, None, u'public')
        assert content.state == u'public'
        reset_workflow(purge_existing=True)
        assert content.state == u'private'
