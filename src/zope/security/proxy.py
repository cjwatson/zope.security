##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Helper functions for Proxies.
"""
__docformat__ = 'restructuredtext'

import functools
import sys

from zope.proxy import PyProxyBase
from zope.security.interfaces import ForbiddenAttribute


def _check_name(meth):
    name = meth.__name__
    def _wrapper(self, *args, **kw):
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        checker = super(PyProxyBase, self).__getattribute__('_checker')
        checker.check_getattr(wrapped, name)
        return checker.proxy(getattr(wrapped, name)(*args, **kw))
    return functools.update_wrapper(_wrapper, meth)

def _check_name_inplace(meth):
    name = meth.__name__
    def _wrapper(self, *args, **kw):
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        checker = super(PyProxyBase, self).__getattribute__('_checker')
        checker.check_getattr(wrapped, name)
        w_meth = getattr(wrapped, name, None)
        if w_meth is not None:
            # The proxy object cannot change; we are modifying in place.
            self._wrapped = w_meth(*args, **kw)
            return self
        x_name = '__%s__' %  name[3:-2]
        return ProxyPy(getattr(wrapped, x_name)(*args, **kw), checker)
    return functools.update_wrapper(_wrapper, meth)

def _fmt_address(obj):
    # Try to replicate PyString_FromString("%p", obj), which actually uses
    # the platform sprintf(buf, "%p", obj), which we cannot access from Python
    # directly (and ctypes seems like overkill).
    if sys.platform == 'win32':
        return '0x%08x' % id(obj)
    else:
        return '0x%0x' % id(obj)


class ProxyPy(PyProxyBase):
    __slots__ = ('_wrapped', '_checker')

    def __new__(cls, value, checker):
        inst = super(PyProxyBase, cls).__new__(cls)
        inst._wrapped = value
        inst._checker = checker
        return inst

    def __init__(self, value, checker):
        if checker is None:
            raise ValueError('checker may now be None')
        self._wrapped = value
        self._checker = checker

    # Attribute protocol
    def __getattribute__(self, name):
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        checker = super(PyProxyBase, self).__getattribute__('_checker')
        if name == '_wrapped':
            return wrapped
        if name == '_checker':
            return checker
        if name not in ['__cmp__', '__hash__', '__bool__', '__nonzero__',
                        '__lt__', '__le__', '__eq__', '__ne__', '__ge__',
                        '__gt__']:
            checker.check_getattr(wrapped, name)
        return checker.proxy(super(ProxyPy, self).__getattribute__(name))

    def __getattr__(self, name):
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        checker = super(PyProxyBase, self).__getattribute__('_checker')
        checker.check_getattr(wrapped, name)
        return checker.proxy(getattr(self._wrapped, name))

    def __setattr__(self, name, value):
        if name in ('_wrapped', '_checker'):
            return super(PyProxyBase, self).__setattr__(name, value)
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        checker = super(PyProxyBase, self).__getattribute__('_checker')
        checker.check_setattr(wrapped, name)
        setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name in ('_wrapped', '_checker'):
            raise AttributeError()
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        checker = super(PyProxyBase, self).__getattribute__('_checker')
        checker.check_setattr(wrapped, name)
        delattr(self._wrapped, name)

    @_check_name
    def __getslice__(self, start, end):
        getitem = super(PyProxyBase, self).__getattribute__('__getitem__')
        return getitem(start, end)

    @_check_name
    def __setslice__(self, i, j, value):
        setitem = super(PyProxyBase, self).__getattribute__('__setitem__')
        return setitem(i, j, value)

    def __cmp__(self, other):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return cmp(wrapped, other)

    def __lt__(self, other):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return wrapped < other

    def __le__(self, other):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return wrapped <= other

    def __eq__(self, other):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return wrapped == other

    def __ne__(self, other):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return wrapped != other

    def __ge__(self, other):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return wrapped >= other

    def __gt__(self, other):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return wrapped > other

    def __hash__(self):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return hash(wrapped)

    def __nonzero__(self):
        # no check
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        return bool(wrapped)
    __bool__ = __nonzero__

    def __coerce__(self, other):
        # For some reason _check_name does not work for coerce()
        wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
        checker = super(PyProxyBase, self).__getattribute__('_checker')
        checker.check_getattr(wrapped, '__coerce__')
        return PyProxyBase.__coerce__(self, other)

    def __str__(self):
        try:
            return _check_name(PyProxyBase.__str__)(self)
        except ForbiddenAttribute:
            wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
            return '<security proxied %s.%s instance at %s>' %(
                wrapped.__class__.__module__, wrapped.__class__.__name__,
                _fmt_address(wrapped))

    def __repr__(self):
        try:
            return _check_name(PyProxyBase.__repr__)(self)
        except ForbiddenAttribute:
            wrapped = super(PyProxyBase, self).__getattribute__('_wrapped')
            return '<security proxied %s.%s instance at %s>' %(
                wrapped.__class__.__module__, wrapped.__class__.__name__,
                _fmt_address(wrapped))

for name in ['__call__',
             #'__repr__',
             #'__str__',
             '__unicode__',
             '__reduce__',
             '__reduce_ex__',
             #'__lt__',      # Unchecked in C proxy (rich coparison)
             #'__le__',      # Unchecked in C proxy (rich coparison)
             #'__eq__',      # Unchecked in C proxy (rich coparison)
             #'__ne__',      # Unchecked in C proxy (rich coparison)
             #'__ge__',      # Unchecked in C proxy (rich coparison)
             #'__gt__',      # Unchecked in C proxy (rich coparison)
             #'__nonzero__', # Unchecked in C proxy (rich coparison)
             #'__bool__',    # Unchecked in C proxy (rich coparison)
             #'__hash__',    # Unchecked in C proxy (rich coparison)
             #'__cmp__',     # Unchecked in C proxy
             '__len__',
             '__getitem__',
             '__setitem__',
             '__delitem__',
             '__iter__',
             '__next__',
             'next',
             '__contains__',
             '__neg__',
             '__pos__',
             '__abs__',
             '__invert__',
             '__complex__',
             '__int__',
             '__float__',
             '__long__',
             '__oct__',
             '__hex__',
             '__index__',
             '__add__',
             '__sub__',
             '__mul__',
             '__div__',
             '__truediv__',
             '__floordiv__',
             '__mod__',
             '__divmod__',
             '__pow__',
             '__radd__',
             '__rsub__',
             '__rmul__',
             '__rdiv__',
             '__rtruediv__',
             '__rfloordiv__',
             '__rmod__',
             '__rdivmod__',
             '__rpow__',
             '__lshift__',
             '__rshift__',
             '__and__',
             '__xor__',
             '__or__',
             '__rlshift__',
             '__rrshift__',
             '__rand__',
             '__rxor__',
             '__ror__',
            ]:
    meth = getattr(PyProxyBase, name)
    setattr(ProxyPy, name, _check_name(meth))

for name in ['__iadd__',
             '__isub__',
             '__imul__',
             '__idiv__',
             '__itruediv__',
             '__ifloordiv__',
             '__imod__',
             '__ilshift__',
             '__irshift__',
             '__iand__',
             '__ixor__',
             '__ior__',
             '__ipow__',
            ]:
    meth = getattr(PyProxyBase, name)
    setattr(ProxyPy, name, _check_name_inplace(meth))

try:
    from zope.security._proxy import _Proxy
except ImportError: #pragma NO COVER PyPy
    #getChecker = getCheckerPy
    #getObject = getObjectPy
    Proxy = ProxyPy
else: #pragma NO COVER CPython
    from zope.security._proxy import getChecker
    from zope.security._proxy import getObject
    Proxy = _Proxy

# We need the injection of DecoratedSecurityCheckerDescriptor into
# zope.location's LocationProxy as soon someone uses security proxies by
# importing zope.security.proxy:
import zope.security.decorator


removeSecurityProxy = getObject

# This import represents part of the API for this module
from zope.security.checker import ProxyFactory

def getTestProxyItems(proxy):
    """Return a sorted sequence of checker names and permissions for testing
    """
    checker = getChecker(proxy)
    return sorted(checker.get_permissions.items())


builtin_isinstance = None
def isinstance(object, cls):
    """Test whether an object is an instance of a type.

    This works even if the object is security proxied:
    """
    global builtin_isinstance
    if builtin_isinstance is None:
        builtin_isinstance = __builtins__['isinstance']
    # The removeSecurityProxy call is OK here because it is *only*
    # being used for isinstance
    return builtin_isinstance(removeSecurityProxy(object), cls)
