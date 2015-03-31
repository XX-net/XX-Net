# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.

"""A few utilities for raw greenlets.

.. warning::

    This module is deprecated. Use :class:`gevent.Greenlet` instead.

.. note::

    These functions do not support *timeout* parameter.
"""

import warnings
warnings.warn("gevent.rawgreenlet is deprecated", DeprecationWarning, stacklevel=2)

import traceback
from gevent import core
from gevent.hub import GreenletExit, Waiter, sleep


__all__ = ['kill',
           'killall',
           'join',
           'joinall']


def _kill(greenlet, exception, waiter):
    try:
        greenlet.throw(exception)
    except:
        traceback.print_exc()
    waiter.switch()


def kill(greenlet, exception=GreenletExit, block=True, polling_period=0.2):
    """Kill greenlet with exception (GreenletExit by default).
    Wait for it to die if block is true.
    """
    if not greenlet.dead:
        waiter = Waiter()
        core.active_event(_kill, greenlet, exception, waiter)
        if block:
            waiter.wait()
            join(greenlet, polling_period=polling_period)


def _killall(greenlets, exception, waiter):
    diehards = []
    for greenlet in greenlets:
        if not greenlet.dead:
            try:
                greenlet.throw(exception)
            except:
                traceback.print_exc()
            if not greenlet.dead:
                diehards.append(greenlet)
    waiter.switch(diehards)


def killall(greenlets, exception=GreenletExit, block=True, polling_period=0.2):
    """Kill all the greenlets with exception (GreenletExit by default).
    Wait for them to die if block is true.
    """
    waiter = Waiter()
    core.active_event(_killall, greenlets, exception, waiter)
    if block:
        alive = waiter.wait()
        if alive:
            joinall(alive, polling_period=polling_period)


def join(greenlet, polling_period=0.2):
    """Wait for a greenlet to finish by polling its status"""
    delay = 0.002
    while not greenlet.dead:
        delay = min(polling_period, delay * 2)
        sleep(delay)


def joinall(greenlets, polling_period=0.2):
    """Wait for the greenlets to finish by polling their status"""
    current = 0
    while current < len(greenlets) and greenlets[current].dead:
        current += 1
    delay = 0.002
    while current < len(greenlets):
        delay = min(polling_period, delay * 2)
        sleep(delay)
        while current < len(greenlets) and greenlets[current].dead:
            current += 1
