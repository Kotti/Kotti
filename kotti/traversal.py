# -*- coding: utf-8 -*-
""" This module contains Kotti's node tree traverser.

In Kotti versions < 1.3.0, Pyramid's default traverser
(:class:`pyramid.traversal.ResourceTreeTraverser`) was used.  This traverser
still works, but it becomes decreasingly performant the deeper your resource
tree is nested.  This is caused by the fact, that it generates one DB query per
level, whereas the Kotti traverser (:class:`kotti.traversal.NodeTreeTraverser`)
generates a single DB query, regardless of the number of request path segments.
This query not only finds the context, but also returns all node items in its
lineage.  This means, that neither accessing ``context.parent`` nor calling
:func:`pyramid.location.lineage` will result in additional DB queries.

The performance benefits are huge.  The table below compares the requests per
seconds (rps) that were reached on a developer's notebook against a PostgreSQL
database with 4419 :class:`kotti.resources.Document` nodes.

===================== ======================= =====================
request.path          Pyramid traverser (rps) Kotti traverser (rps)
===================== ======================= =====================
/                     49                      49
/a/                   41                      36
/a/b/                 30                      35
/a/b/c/               23                      34
/a/b/c/d/             19                      33
/a/b/c/d/e/           16                      33
/a/b/c/d/e/f/         14                      33
/a/b/c/d/e/f/g/       12                      32
/a/b/c/d/e/f/g/h/     11                      31
/a/b/c/d/e/f/g/h/i/   10                      30
/a/b/c/d/e/f/g/h/i/j/ 8                       29
===================== ======================= =====================

"""

from pyramid.compat import decode_path_info
from pyramid.compat import is_nonstr_iter
from pyramid.exceptions import URLDecodeError
from pyramid.interfaces import ITraverser
from pyramid.interfaces import VH_ROOT_KEY
from pyramid.traversal import empty
from pyramid.traversal import ResourceTreeTraverser
from pyramid.traversal import slash
from pyramid.traversal import split_path_info
from sqlalchemy import or_
from zope.interface import implementer

from kotti import DBSession
from kotti.resources import Node


@implementer(ITraverser)
class NodeTreeTraverser(ResourceTreeTraverser):
    """ An optimized resource tree traverser for :class:`kotti.resources.Node`
    based resource trees. """

    @staticmethod
    def _extract_from_request(request):  # pragma: no cover
        """ Extract subpath, vpath and vroot_tuple from the request.  The
        contents of this method is just a copy from the base class'
        implementation.

        :param request: Current request
        :type request: :class:`pyramid.request.Request`

        :return: (subpath, vpath, vroot_tuple)
        :rtype: tuple
        """

        environ = request.environ
        matchdict = request.matchdict
        if matchdict is not None:
            path = matchdict.get('traverse', slash) or slash
            if is_nonstr_iter(path):
                path = '/' + slash.join(path) or slash
            subpath = matchdict.get('subpath', ())
            if not is_nonstr_iter(subpath):
                subpath = split_path_info(subpath)
        else:
            subpath = ()
            try:
                path = request.path_info or slash
            except KeyError:
                path = slash
            except UnicodeDecodeError as e:
                raise URLDecodeError(e.encoding, e.object, e.start, e.end,
                                     e.reason)
        if VH_ROOT_KEY in environ:
            vroot_path = decode_path_info(environ[VH_ROOT_KEY])
            vroot_tuple = split_path_info(vroot_path)
            vpath = vroot_path + path
        else:
            vroot_tuple = ()
            vpath = path
        return subpath, vpath, vroot_tuple

    def __call__(self, request):
        """ The first part of this function is copied without changes from
        :meth:`pyramid.traversal.ResourceTreeTraverser.__call__`.

        :param request: Current request
        :type request: :class:`pyramid.request.Request`

        :return: Traversal info dictionary
        :rtype: see :func:`pyramid.traversal.traverse`
        """

        subpath, vpath, vroot_tuple = self._extract_from_request(request)

        root = self.root

        # Part 2:
        vs = self.VIEW_SELECTOR
        lvs = len(vs)
        result = {
            'context': root,
            'view_name': empty,
            'subpath': subpath,
            'traversed': (),
            'virtual_root': root,
            'virtual_root_path': vroot_tuple,
            'root': root}

        if vpath == slash:
            return result
        else:
            vpath_tuple = split_path_info(vpath)
            traversed_nodes = self.traverse(root, vpath_tuple)
            if not traversed_nodes:
                view_name = vpath_tuple[0]
                if view_name[:lvs] == vs:
                    view_name = view_name[lvs:]
                result['view_name'] = view_name
                result['subpath'] = vpath_tuple[1:]
                return result
            traversed = vpath_tuple[:len(traversed_nodes)]
            subpath = list(vpath_tuple[len(traversed_nodes):])
            if subpath:
                view_name = subpath.pop(0)
                if view_name[:lvs] == vs:
                    view_name = view_name[lvs:]
            else:
                view_name = empty
            return {'context': traversed_nodes[-1],
                    'view_name': view_name,
                    'subpath': subpath,
                    'traversed': traversed,
                    'virtual_root': root,
                    'virtual_root_path': vroot_tuple,
                    'root': root}

    @staticmethod
    def traverse(root, vpath_tuple):
        """
        :param root: The node where traversal should start
        :type root: :class:`kotti.resources.Node`

        :param vpath_tuple: Tuple of path segments to be traversed
        :type vpath_tuple: tuple

        :return: List of nodes, from root (excluded) to context (included).
                 Each node has its parent set already, so that no subsequent
                 queries will be be performed, e.g. when calling
                 ``lineage(context)``
        :rtype: list of :class:`kotti.resources.Node`
        """

        conditions = [
            (Node.path == root.path + '/'.join(vpath_tuple[:idx + 1]) + '/')
            for idx, item in enumerate(vpath_tuple)]
        nodes = DBSession().query(Node)\
            .order_by(Node.path)\
            .filter(or_(*conditions))\
            .all()
        for i, node in enumerate(nodes):
            if i == 0:
                setattr(node, 'parent', root)
            else:
                setattr(node, 'parent', nodes[i - 1])

        return nodes

    @staticmethod
    def _traverse_cte(root, vpath_tuple):  # pragma: no cover
        """ Version of the traverse method, that uses a CTE instead of the
        Node.path attribute.  Unfortunately this is **much** slower and works
        only on PostgreSQL.

        It **does** work, but is not used ATM.  Could be very useful to replace
        :func:`kotti.events._set_path_for_new_parent` and
        :func:`kotti.events._set_path_for_new_name` event handlers to handle
        everything on the database with a single call, instead of the expensive
        recursion maassacre we have right now.
        """

        raise NotImplementedError('Use the traverse method instead.')

        """
        # needed until we find out how to pass an empty array of type String
        # (i.e. 'VARCHAR[]') to the initial cte.

        vpath = ('', ) + vpath_tuple

        cte = DBSession.query(
                Node.id,
                # array([concat('', Node.name)]).label('path')) \
                concat('', Node.name).label('path')) \
            .enable_eagerloads(False) \
            .filter(Node.parent_id == None) \
            .cte(name="n1", recursive=True)
        parent = aliased(cte, name='parent')
        child = aliased(Node, name='child')
        inner = DBSession.query(
                child.id,
                # (parent.c.path + array([concat('', child.name)])).label('path')) \
                concat(parent.c.path, '/', child.name).label('path')) \
            .enable_eagerloads(False) \
            .filter(child.parent_id == parent.c.id)
        cte = cte.union_all(inner)
        conditions = [
            # (cte.c.path == array(vpath[:idx + 1]))
            (cte.c.path == '/'.join(vpath[:idx + 1]))
            for idx, item in enumerate(vpath)]
        ids = DBSession.query(Node.id.label('node_id')) \
            .select_entity_from(cte) \
            .filter(or_(*conditions))
        nodes = DBSession.query(Node).filter(Node.id.in_(ids)).order_by(Node.path).offset(1).all()
        for i, node in enumerate(nodes):
            if i == 0:
                setattr(node, 'parent', root)
            else:
                setattr(node, 'parent', nodes[i-1])
        return nodes
        """


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.add_traverser(NodeTreeTraverser, Node)
