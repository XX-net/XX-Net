#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# rumps: Ridiculously Uncomplicated Mac os x Python Statusbar apps.
# Copyright: (c) 2015, Jared Suttles. All rights reserved.
# License: BSD, see LICENSE for details.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

_NOTIFICATIONS = True
try:
    from Foundation import NSUserNotification, NSUserNotificationCenter
except ImportError:
    _NOTIFICATIONS = False

from Foundation import (NSDate, NSTimer, NSRunLoop, NSDefaultRunLoopMode, NSSearchPathForDirectoriesInDomains,
                        NSMakeRect, NSLog, NSObject)
from AppKit import NSApplication, NSStatusBar, NSMenu, NSMenuItem, NSAlert, NSTextField, NSImage
from PyObjCTools import AppHelper

import os
import weakref
from collections import Mapping, Iterable
from .utils import ListDict

_TIMERS = weakref.WeakKeyDictionary()
separator = object()


def debug_mode(choice):
    """Enable/disable printing helpful information for debugging the program. Default is off."""
    global _log
    if choice:
        def _log(*args):
            NSLog(' '.join(map(str, args)))
    else:
        def _log(*_):
            pass
debug_mode(False)


def alert(title=None, message='', ok=None, cancel=None):
    """Generate a simple alert window.

    .. versionchanged:: 0.2.0
        Providing a `cancel` string will set the button text rather than only using text "Cancel". `title` is no longer
        a required parameter.

    :param title: the text positioned at the top of the window in larger font. If ``None``, a default localized title
                  is used. If not ``None`` or a string, will use the string representation of the object.
    :param message: the text positioned below the `title` in smaller font. If not a string, will use the string
                    representation of the object.
    :param ok: the text for the "ok" button. Must be either a string or ``None``. If ``None``, a default
               localized button title will be used.
    :param cancel: the text for the "cancel" button. If a string, the button will have that text. If `cancel`
                   evaluates to ``True``, will create a button with text "Cancel". Otherwise, this button will not be
                   created.
    :return: a number representing the button pressed. The "ok" button is ``1`` and "cancel" is ``0``.
    """
    message = unicode(message)
    if title is not None:
        title = unicode(title)
    _require_string_or_none(ok)
    if not isinstance(cancel, basestring):
        cancel = 'Cancel' if cancel else None
    alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
        title, ok, cancel, None, message)
    alert.setAlertStyle_(0)  # informational style
    _log('alert opened with message: {0}, title: {1}'.format(repr(message), repr(title)))
    return alert.runModal()


def notification(title, subtitle, message, data=None, sound=True):
    """Send a notification to Notification Center (Mac OS X 10.8+). If running on a version of Mac OS X that does not
    support notifications, a ``RuntimeError`` will be raised. Apple says,

        "The userInfo content must be of reasonable serialized size (less than 1k) or an exception will be thrown."

    So don't do that!

    :param title: text in a larger font.
    :param subtitle: text in a smaller font below the `title`.
    :param message: text representing the body of the notification below the `subtitle`.
    :param data: will be passed to the application's "notification center" (see :func:`rumps.notifications`) when this
                 notification is clicked.
    :param sound: whether the notification should make a noise when it arrives.
    """
    if not _NOTIFICATIONS:
        raise RuntimeError('Mac OS X 10.8+ is required to send notifications')
    if data is not None and not isinstance(data, Mapping):
        raise TypeError('notification data must be a mapping')
    _require_string_or_none(title, subtitle, message)
    notification = NSUserNotification.alloc().init()
    notification.setTitle_(title)
    notification.setSubtitle_(subtitle)
    notification.setInformativeText_(message)
    notification.setUserInfo_({} if data is None else data)
    if sound:
        notification.setSoundName_("NSUserNotificationDefaultSoundName")
    notification.setDeliveryDate_(NSDate.dateWithTimeInterval_sinceDate_(0, NSDate.date()))
    NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)


def application_support(name):
    """Return the application support folder path for the given `name`, creating it if it doesn't exist."""
    app_support_path = os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, 1).objectAtIndex_(0), name)
    if not os.path.isdir(app_support_path):
        os.mkdir(app_support_path)
    return app_support_path


def timers():
    """Return a list of all :class:`rumps.Timer` objects. These can be active or inactive."""
    return list(_TIMERS)


def quit_application(sender=None):
    """Quit the application. Some menu item should call this function so that the application can exit gracefully."""
    nsapplication = NSApplication.sharedApplication()
    _log('closing application')
    nsapplication.terminate_(sender)


def _nsimage_from_file(filename, dimensions=None):
    """Take a path to an image file and return an NSImage object."""
    try:
        _log('attempting to open image at {0}'.format(filename))
        with open(filename):
            pass
    except IOError:  # literal file path didn't work -- try to locate image based on main script path
        try:
            from __main__ import __file__ as main_script_path
            main_script_path = os.path.dirname(main_script_path)
            filename = os.path.join(main_script_path, filename)
        except ImportError:
            pass
        _log('attempting (again) to open image at {0}'.format(filename))
        with open(filename):  # file doesn't exist
            pass              # otherwise silently errors in NSImage which isn't helpful for debugging
    image = NSImage.alloc().initByReferencingFile_(filename)
    image.setScalesWhenResized_(True)
    image.setSize_((20, 20) if dimensions is None else dimensions)
    return image


def _require_string(*objs):
    for obj in objs:
        if not isinstance(obj, basestring):
            raise TypeError('a string is required but given {0}, a {1}'.format(obj, type(obj).__name__))


def _require_string_or_none(*objs):
    for obj in objs:
        if not(obj is None or isinstance(obj, basestring)):
            raise TypeError('a string or None is required but given {0}, a {1}'.format(obj, type(obj).__name__))


# Decorators and helper function serving to register functions for dealing with interaction and events
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def timer(interval):
    """Decorator for registering a function as a callback in a new thread. The function will be repeatedly called every
    `interval` seconds. This decorator accomplishes the same thing as creating a :class:`rumps.Timer` object by using
    the decorated function and `interval` as parameters and starting it on application launch.

    .. code-block:: python

        @rumps.timer(2)
        def repeating_function(sender):
            print 'hi'

    :param interval: a number representing the time in seconds before the decorated function should be called.
    """
    def decorator(f):
        timers = timer.__dict__.setdefault('*timers', [])
        timers.append(Timer(f, interval))
        return f
    return decorator


def clicked(*args, **options):
    """Decorator for registering a function as a callback for a click action on a :class:`rumps.MenuItem` within the
    application. The passed `args` must specify an existing path in the main menu. The :class:`rumps.MenuItem`
    instance at the end of that path will have its :meth:`rumps.MenuItem.set_callback` method called, passing in the
    decorated function.

    .. versionchanged:: 0.2.1
        Accepts `key` keyword argument.

    .. code-block:: python

        @rumps.clicked('Animal', 'Dog', 'Corgi')
        def corgi_button(sender):
            import subprocess
            subprocess.call(['say', '"corgis are the cutest"'])

    :param args: a series of strings representing the path to a :class:`rumps.MenuItem` in the main menu of the
                 application.
    :param key: a string representing the key shortcut as an alternative means of clicking the menu item.
    """
    def decorator(f):

        def register_click(self):
            menuitem = self._menu  # self not defined yet but will be later in 'run' method
            if menuitem is None:
                raise ValueError('no menu created')
            for arg in args:
                try:
                    menuitem = menuitem[arg]
                except KeyError:
                    menuitem.add(arg)
                    menuitem = menuitem[arg]
            menuitem.set_callback(f, options.get('key'))

        # delay registering the button until we have a current instance to be able to traverse the menu
        buttons = clicked.__dict__.setdefault('*buttons', [])
        buttons.append(register_click)

        return f
    return decorator


def notifications(f):
    """Decorator for registering a function to serve as a "notification center" for the application. This function will
    receive the data associated with an incoming OS X notification sent using :func:`rumps.notification`. This occurs
    whenever the user clicks on a notification for this application in the OS X Notification Center.

    .. code-block:: python

        @rumps.notifications
        def notification_center(info):
            if 'unix' in info:
                print 'i know this'

    """
    notifications.__dict__['*notification_center'] = f
    return f


def _call_as_function_or_method(f, event):
    # The idea here is that when using decorators in a class, the functions passed are not bound so we have to
    # determine later if the functions we have (those saved as callbacks) for particular events need to be passed
    # 'self'.
    #
    # This works for an App subclass method or a standalone decorated function. Will attempt to call function with event
    # alone then try with self and event. This might not be a great idea if the function is unbound and normally takes
    # two arguments... but people shouldn't be decorating functions that consume more than a single parameter anyway!
    #
    # Decorating methods of a class subclassing something other than App should produce AttributeError eventually which
    # is hopefully understandable.
    try:
        r = f(event)
        _log('given function {0} is outside an App subclass definition'.format(repr(f)))
        return r
    except TypeError as e:  # possibly try it with self if TypeError makes sense
        if e.message.endswith('takes exactly 2 arguments (1 given)'):
            r = f(getattr(App, '*app_instance'), event)
            _log('given function {0} is probably inside a class (which should be an App subclass)'.format(repr(f)))
            return r
        raise e
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class Menu(ListDict):
    """Wrapper for Objective-C's NSMenu class.

    Implements core functionality of menus in rumps. :class:`rumps.MenuItem` subclasses `Menu`.
    """

    # NOTE:
    # Only ever used as the main menu since every other menu would exist as a submenu of a MenuItem

    _choose_key = object()

    def __init__(self):
        self._separators = 1
        if not hasattr(self, '_menu'):
            self._menu = NSMenu.alloc().init()
        super(Menu, self).__init__()

    def __setitem__(self, key, value):
        if key not in self:
            key, value = self._process_new_menuitem(key, value)
            self._menu.addItem_(value._menuitem)
            super(Menu, self).__setitem__(key, value)

    def __delitem__(self, key):
        value = self[key]
        self._menu.removeItem_(value._menuitem)
        super(Menu, self).__delitem__(key)

    def add(self, menuitem):
        """Adds the object to the menu as a :class:`rumps.MenuItem` using the :attr:`rumps.MenuItem.title` as the
        key. `menuitem` will be converted to a `MenuItem` object if not one already.
        """
        self.__setitem__(self._choose_key, menuitem)

    def clear(self):
        """Remove all `MenuItem` objects from within the menu of this `MenuItem`."""
        self._menu.removeAllItems()
        super(Menu, self).clear()

    def copy(self):
        raise NotImplementedError

    @classmethod
    def fromkeys(cls, *args, **kwargs):
        raise NotImplementedError

    def update(self, iterable, **kwargs):
        """Update with objects from `iterable` after each is converted to a :class:`rumps.MenuItem`, ignoring
        existing keys. This update is a bit different from the usual ``dict.update`` method. It works recursively and
        will parse a variety of Python containers and objects, creating `MenuItem` object and submenus as necessary.

        If the `iterable` is an instance of :class:`rumps.MenuItem`, then add to the menu.

        Otherwise, for each element in the `iterable`,

            - if the element is a string or is not an iterable itself, it will be converted to a
              :class:`rumps.MenuItem` and the key will be its string representation.
            - if the element is a :class:`rumps.MenuItem` already, it will remain the same and the key will be its
              :attr:`rumps.MenuItem.title` attribute.
            - if the element is an iterable having a length of 2, the first value will be converted to a
              :class:`rumps.MenuItem` and the second will act as the submenu for that `MenuItem`
            - if the element is an iterable having a length of anything other than 2, a ``ValueError`` will be raised
            - if the element is a mapping, each key-value pair will act as an iterable having a length of 2

        """
        def parse_menu(iterable, menu, depth):
            if isinstance(iterable, MenuItem):
                menu.add(iterable)
                return

            for n, ele in enumerate(iterable.iteritems() if isinstance(iterable, Mapping) else iterable):

                # for mappings we recurse but don't drop down a level in the menu
                if not isinstance(ele, MenuItem) and isinstance(ele, Mapping):
                    parse_menu(ele, menu, depth)

                # any iterables other than strings and MenuItems
                elif not isinstance(ele, (basestring, MenuItem)) and isinstance(ele, Iterable):
                    try:
                        menuitem, submenu = ele
                    except TypeError:
                        raise ValueError('menu iterable element #{0} at depth {1} has length {2}; must be a single '
                                         'menu item or a pair consisting of a menu item and its '
                                         'submenu'.format(n, depth, len(tuple(ele))))
                    menuitem = MenuItem(menuitem)
                    menu.add(menuitem)
                    parse_menu(submenu, menuitem, depth+1)

                # menu item / could be visual separator where ele is None or separator
                else:
                    menu.add(ele)
        parse_menu(iterable, self, 0)
        parse_menu(kwargs, self, 0)

    # ListDict insertion methods
    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insert_after(self, existing_key, menuitem):
        """Insert a :class:`rumps.MenuItem` in the menu after the `existing_key`.

        :param existing_key: a string key for an existing `MenuItem` value.
        :param menuitem: an object to be added. It will be converted to a `MenuItem` if not one already.
        """
        key, menuitem = self._process_new_menuitem(self._choose_key, menuitem)
        self._insert_helper(existing_key, key, menuitem, 1)
        super(Menu, self).insert_after(existing_key, (key, menuitem))

    def insert_before(self, existing_key, menuitem):
        """Insert a :class:`rumps.MenuItem` in the menu before the `existing_key`.

        :param existing_key: a string key for an existing `MenuItem` value.
        :param menuitem: an object to be added. It will be converted to a `MenuItem` if not one already.
        """
        key, menuitem = self._process_new_menuitem(self._choose_key, menuitem)
        self._insert_helper(existing_key, key, menuitem, 0)
        super(Menu, self).insert_before(existing_key, (key, menuitem))

    def _insert_helper(self, existing_key, key, menuitem, pos):
        if existing_key == key:  # this would mess stuff up...
            raise ValueError('same key provided for location and insertion')
        existing_menuitem = self[existing_key]
        index = self._menu.indexOfItem_(existing_menuitem._menuitem)
        self._menu.insertItem_atIndex_(menuitem._menuitem, index + pos)

    # Processing MenuItems
    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _process_new_menuitem(self, key, value):
        if value is None:
            value = separator

        if value is not separator:
            value = MenuItem(value)  # safely convert if not already MenuItem
            if key is self._choose_key:
                key = value.title
            if key != value.title:
                _log('WARNING: key {0} is not the same as the title of the corresponding MenuItem {1}; while this '
                     'would occur if the title is dynamically altered, having different names at the time of menu '
                     'creation may not be desired '.format(repr(key), repr(value.title)))
        else:
            value = SeparatorMenuItem()
            if key is self._choose_key:
                key = 'separator_' + str(self._separators)
                self._separators += 1

        return key, value


class MenuItem(Menu):
    """Represents an item within the application's menu.

    A :class:`rumps.MenuItem` is a button inside a menu but it can also serve as a menu itself whose elements are
    other `MenuItem` instances.

    Encapsulates and abstracts Objective-C NSMenuItem (and possibly a corresponding NSMenu as a submenu).

    A couple of important notes:

        - A new `MenuItem` instance can be created from any object with a string representation.
        - Attempting to create a `MenuItem` by passing an existing `MenuItem` instance as the first parameter will not
          result in a new instance but will instead return the existing instance.

    Remembers the order of items added to menu and has constant time lookup. Can insert new `MenuItem` object before or
    after other specified ones.

    .. note::
       When adding a `MenuItem` instance to a menu, the value of :attr:`title` at that time will serve as its key for
       lookup performed on menus even if the `title` changes during program execution.

    :param title: the name of this menu item. If not a string, will use the string representation of the object.
    :param callback: the function serving as callback for when a click event occurs on this menu item.
    :param key: the key shortcut to click this menu item. Must be a string or ``None``.
    :param icon: a path to an image. If set to ``None``, the current image (if any) is removed.
    :param dimensions: a sequence of numbers whose length is two, specifying the dimensions of the icon.
    """

    # NOTE:
    # Because of the quirks of PyObjC, a class level dictionary **inside an NSObject subclass for 10.9.x** is required
    # in order to have callback_ be a @classmethod. And we need callback_ to be class level because we can't use
    # instances in setTarget_ method of NSMenuItem. Otherwise this would be much more straightfoward like Timer class.
    #
    # So the target is always the NSApp class and action is always the @classmethod callback_ -- for every function
    # decorated with @clicked(...). All we do is lookup the MenuItem instance and the user-provided callback function
    # based on the NSMenuItem (the only argument passed to callback_).

    def __new__(cls, *args, **kwargs):
        if args and isinstance(args[0], MenuItem):  # can safely wrap MenuItem instances
            return args[0]
        return super(MenuItem, cls).__new__(cls, *args, **kwargs)

    def __init__(self, title, callback=None, key=None, icon=None, dimensions=None):
        if isinstance(title, MenuItem):  # don't initialize already existing instances
            return
        self._menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(unicode(title), None, '')
        self._menuitem.setTarget_(NSApp)
        self._menu = self._icon = None
        self.set_callback(callback, key)
        self.set_icon(icon, dimensions)
        super(MenuItem, self).__init__()

    def __setitem__(self, key, value):
        if self._menu is None:
            self._menu = NSMenu.alloc().init()
            self._menuitem.setSubmenu_(self._menu)
        super(MenuItem, self).__setitem__(key, value)

    def __repr__(self):
        return '<{0}: [{1} -> {2}; callback: {3}]>'.format(type(self).__name__, repr(self.title), map(str, self),
                                                           repr(self.callback))

    @property
    def title(self):
        """The text displayed in a menu for this menu item. If not a string, will use the string representation of the
        object.
        """
        return self._menuitem.title()

    @title.setter
    def title(self, new_title):
        new_title = unicode(new_title)
        self._menuitem.setTitle_(new_title)

    @property
    def icon(self):
        """The path to an image displayed next to the text for this menu item. If set to ``None``, the current image
        (if any) is removed.

        .. versionchanged:: 0.2.0
           Setting icon to ``None`` after setting it to an image will correctly remove the icon. Returns the path to an
           image rather than exposing a `PyObjC` class.

        """
        return self._icon

    @icon.setter
    def icon(self, icon_path):
        self.set_icon(icon_path)

    def set_icon(self, icon_path, dimensions=None):
        """Sets the icon displayed next to the text for this menu item. If set to ``None``, the current image (if any)
        is removed. Can optionally supply `dimensions`.

        .. versionchanged:: 0.2.0
           Setting `icon` to ``None`` after setting it to an image will correctly remove the icon. Passing `dimensions`
           a sequence whose length is not two will no longer silently error.

        :param icon_path: a file path to an image.
        :param dimensions: a sequence of numbers whose length is two.
        """
        new_icon = _nsimage_from_file(icon_path, dimensions) if icon_path is not None else None
        self._icon = icon_path
        self._menuitem.setImage_(new_icon)

    @property
    def state(self):
        """The state of the menu item. The "on" state is symbolized by a check mark. The "mixed" state is symbolized
        by a dash.

        .. table:: Setting states

           =====  ======
           State  Number
           =====  ======
            ON      1
            OFF     0
           MIXED   -1
           =====  ======

        """
        return self._menuitem.state()

    @state.setter
    def state(self, new_state):
        self._menuitem.setState_(new_state)

    def set_callback(self, callback, key=None):
        """Set the function serving as callback for when a click event occurs on this menu item. When `callback` is
        ``None``, it will disable the callback function and grey out the menu item. If `key` is a string, set as the
        key shortcut. If it is ``None``, no adjustment will be made to the current key shortcut.

        .. versionchanged:: 0.2.0
           Allowed passing ``None`` as both `callback` and `key`. Additionally, passing a `key` that is neither a
           string nor ``None`` will result in a standard ``TypeError`` rather than various, uninformative `PyObjC`
           internal errors depending on the object.

        :param callback: the function to be called when the user clicks on this menu item.
        :param key: the key shortcut to click this menu item.
        """
        _require_string_or_none(key)
        if key is not None:
            self._menuitem.setKeyEquivalent_(key)
        NSApp._ns_to_py_and_callback[self._menuitem] = self, callback
        self._menuitem.setAction_('callback:' if callback is not None else None)

    @property
    def callback(self):
        """Return the current callback function.

        .. versionadded:: 0.2.0

        """
        return NSApp._ns_to_py_and_callback[self._menuitem][1]

    @property
    def key(self):
        """The key shortcut to click this menu item.

        .. versionadded:: 0.2.0

        """
        return self._menuitem.keyEquivalent()


class SeparatorMenuItem(object):
    """Visual separator between :class:`rumps.MenuItem` objects in the application menu."""
    def __init__(self):
        self._menuitem = NSMenuItem.separatorItem()


class Timer(object):
    """
    Python abstraction of an Objective-C event timer in a new thread for application. Controls the callback function,
    interval, and starting/stopping the run loop.

    .. versionchanged:: 0.2.0
       Method `__call__` removed.

    :param callback: Function that should be called every `interval` seconds. It will be passed this
                     :class:`rumps.Timer` object as its only parameter.
    :param interval: The time in seconds to wait before calling the `callback` function.
    """
    def __init__(self, callback, interval):
        self.set_callback(callback)
        self._interval = interval
        self._status = False

    def __repr__(self):
        return ('<{0}: [callback: {1}; interval: {2}; '
                'status: {3}]>').format(type(self).__name__, repr(getattr(self, '*callback').__name__),
                                        self._interval, 'ON' if self._status else 'OFF')

    @property
    def interval(self):
        """The time in seconds to wait before calling the :attr:`callback` function."""
        return self._interval  # self._nstimer.timeInterval() when active but could be inactive

    @interval.setter
    def interval(self, new_interval):
        if self._status:
            if abs(self._nsdate.timeIntervalSinceNow()) >= self._nstimer.timeInterval():
                self.stop()
                self._interval = new_interval
                self.start()
        else:
            self._interval = new_interval

    @property
    def callback(self):
        """The current function specified as the callback."""
        return getattr(self, '*callback')

    def is_alive(self):
        """Whether the timer thread loop is currently running."""
        return self._status

    def start(self):
        """Start the timer thread loop."""
        if not self._status:
            self._nsdate = NSDate.date()
            self._nstimer = NSTimer.alloc().initWithFireDate_interval_target_selector_userInfo_repeats_(
                self._nsdate, self._interval, self, 'callback:', None, True)
            NSRunLoop.currentRunLoop().addTimer_forMode_(self._nstimer, NSDefaultRunLoopMode)
            _TIMERS[self] = None
            self._status = True

    def stop(self):
        """Stop the timer thread loop."""
        if self._status:
            self._nstimer.invalidate()
            del self._nstimer
            del self._nsdate
            self._status = False

    def set_callback(self, callback):
        """Set the function that should be called every :attr:`interval` seconds. It will be passed this
        :class:`rumps.Timer` object as its only parameter.
        """
        setattr(self, '*callback', callback)

    def callback_(self, _):
        _log(self)
        return _call_as_function_or_method(getattr(self, '*callback'), self)


class Window(object):
    """Generate a window to consume user input in the form of both text and button clicked.

    .. versionchanged:: 0.2.0
        Providing a `cancel` string will set the button text rather than only using text "Cancel". `message` is no
        longer a required parameter.

    :param message: the text positioned below the `title` in smaller font. If not a string, will use the string
                    representation of the object.
    :param title: the text positioned at the top of the window in larger font. If not a string, will use the string
                  representation of the object.
    :param default_text: the text within the editable textbox. If not a string, will use the string representation of
                         the object.
    :param ok: the text for the "ok" button. Must be either a string or ``None``. If ``None``, a default
               localized button title will be used.
    :param cancel: the text for the "cancel" button. If a string, the button will have that text. If `cancel`
                   evaluates to ``True``, will create a button with text "Cancel". Otherwise, this button will not be
                   created.
    :param dimensions: the size of the editable textbox. Must be sequence with a length of 2.
    """

    def __init__(self, message='', title='', default_text='', ok=None, cancel=None, dimensions=(320, 160)):
        message = unicode(message)
        title = unicode(title)

        self._cancel = bool(cancel)
        self._icon = None

        _require_string_or_none(ok)
        if not isinstance(cancel, basestring):
            cancel = 'Cancel' if cancel else None

        self._alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
            title, ok, cancel, None, message)
        self._alert.setAlertStyle_(0)  # informational style

        self._textfield = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, *dimensions))
        self._textfield.setSelectable_(True)
        self._alert.setAccessoryView_(self._textfield)

        self.default_text = default_text

    @property
    def title(self):
        """The text positioned at the top of the window in larger font. If not a string, will use the string
        representation of the object.
        """
        return self._alert.messageText()

    @title.setter
    def title(self, new_title):
        new_title = unicode(new_title)
        self._alert.setMessageText_(new_title)

    @property
    def message(self):
        """The text positioned below the :attr:`title` in smaller font. If not a string, will use the string
        representation of the object.
        """
        return self._alert.informativeText()

    @message.setter
    def message(self, new_message):
        new_message = unicode(new_message)
        self._alert.setInformativeText_(new_message)

    @property
    def default_text(self):
        """The text within the editable textbox. An example would be

            "Type your message here."

        If not a string, will use the string representation of the object.
        """
        return self._default_text

    @default_text.setter
    def default_text(self, new_text):
        new_text = unicode(new_text)
        self._default_text = new_text
        self._textfield.setStringValue_(new_text)

    @property
    def icon(self):
        """The path to an image displayed for this window. If set to ``None``, will default to the icon for the
        application using :attr:`rumps.App.icon`.

        .. versionchanged:: 0.2.0
           If the icon is set to an image then changed to ``None``, it will correctly be changed to the application
           icon.

        """
        return self._icon

    @icon.setter
    def icon(self, icon_path):
        new_icon = _nsimage_from_file(icon_path) if icon_path is not None else None
        self._icon = icon_path
        self._alert.setIcon_(new_icon)

    def add_button(self, name):
        """Create a new button.

        .. versionchanged:: 0.2.0
           The `name` parameter is required to be a string.

        :param name: the text for a new button. Must be a string.
        """
        _require_string(name)
        self._alert.addButtonWithTitle_(name)

    def add_buttons(self, iterable=None, *args):
        """Create multiple new buttons.

        .. versionchanged:: 0.2.0
           Since each element is passed to :meth:`rumps.Window.add_button`, they must be strings.

        """
        if iterable is None:
            return
        if isinstance(iterable, basestring):
            self.add_button(iterable)
        else:
            for ele in iterable:
                self.add_button(ele)
        for arg in args:
            self.add_button(arg)

    def run(self):
        """Launch the window. :class:`rumps.Window` instances can be reused to retrieve user input as many times as
        needed.

        :return: a :class:`rumps.rumps.Response` object that contains the text and the button clicked as an integer.
        """
        _log(self)
        clicked = self._alert.runModal() % 999
        if clicked > 2 and self._cancel:
            clicked -= 1
        self._textfield.validateEditing()
        text = self._textfield.stringValue()
        self.default_text = self._default_text  # reset default text
        return Response(clicked, text)


class Response(object):
    """Holds information from user interaction with a :class:`rumps.Window` after it has been closed."""

    def __init__(self, clicked, text):
        self._clicked = clicked
        self._text = text

    def __repr__(self):
        shortened_text = self._text if len(self._text) < 21 else self._text[:17] + '...'
        return '<{0}: [clicked: {1}, text: {2}]>'.format(type(self).__name__, self._clicked, repr(shortened_text))

    @property
    def clicked(self):
        """Return a number representing the button pressed by the user.

        The "ok" button will return ``1`` and the "cancel" button will return ``0``. This makes it convenient to write
        a conditional like,

        .. code-block:: python

            if response.clicked:
                do_thing_for_ok_pressed()
            else:
                do_thing_for_cancel_pressed()

        Where `response` is an instance of :class:`rumps.rumps.Response`.

        Additional buttons added using methods :meth:`rumps.Window.add_button` and :meth:`rumps.Window.add_buttons`
        will return ``2``, ``3``, ... in the order they were added.
        """
        return self._clicked

    @property
    def text(self):
        """Return the text collected from the user."""
        return self._text


class NSApp(NSObject):
    """Objective-C delegate class for NSApplication. Don't instantiate - use App instead."""

    _ns_to_py_and_callback = {}

    def userNotificationCenter_didActivateNotification_(self, notification_center, notification):
        notification_center.removeDeliveredNotification_(notification)
        data = dict(notification.userInfo())
        try:
            notification_function = getattr(notifications, '*notification_center')
        except AttributeError:  # notification center function not specified -> no error but warning in log
            _log('WARNING: notification received but no function specified for answering it; use @notifications '
                 'decorator to register a function.')
        else:
            _call_as_function_or_method(notification_function, data)

    def initializeStatusBar(self):
        self.nsstatusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(-1)  # variable dimensions
        self.nsstatusitem.setHighlightMode_(True)

        self.setStatusBarIcon()
        self.setStatusBarTitle()

        mainmenu = self._app['_menu']
        quit_button = self._app['_quit_button']
        if quit_button is not None:
            quit_button.set_callback(quit_application)
            mainmenu.add(quit_button)
        else:
            _log('WARNING: the default quit button is disabled. To exit the application gracefully, another button '
                 'should have a callback of quit_application or call it indirectly.')
        self.nsstatusitem.setMenu_(mainmenu._menu)  # mainmenu of our status bar spot (_menu attribute is NSMenu)

    def setStatusBarTitle(self):
        self.nsstatusitem.setTitle_(self._app['_title'])
        self.fallbackOnName()

    def setStatusBarIcon(self):
        self.nsstatusitem.setImage_(self._app['_icon_nsimage'])
        self.fallbackOnName()

    def fallbackOnName(self):
        if not (self.nsstatusitem.title() or self.nsstatusitem.image()):
            self.nsstatusitem.setTitle_(self._app['_name'])

    @classmethod
    def callback_(cls, nsmenuitem):
        self, callback = cls._ns_to_py_and_callback[nsmenuitem]
        _log(self)
        return _call_as_function_or_method(callback, self)


class App(object):
    """Represents the statusbar application.

    Provides a simple and pythonic interface for all those long and ugly `PyObjC` calls. :class:`rumps.App` may be
    subclassed so that the application logic can be encapsulated within a class. Alternatively, an `App` can be
    instantiated and the various callback functions can exist at module level.

    .. versionchanged:: 0.2.0
       `name` parameter must be a string and `title` must be either a string or ``None``. `quit_button` parameter added.

    :param name: the name of the application.
    :param title: text that will be displayed for the application in the statusbar.
    :param icon: file path to the icon that will be displayed for the application in the statusbar.
    :param menu: an iterable of Python objects or pairs of objects that will be converted into the main menu for the
                 application. Parsing is implemented by calling :meth:`rumps.MenuItem.update`.
    :param quit_button: the quit application menu item within the main menu. If ``None``, the default quit button will
                        not be added.
    """

    # NOTE:
    # Serves as a setup class for NSApp since Objective-C classes shouldn't be instantiated normally.
    # This is the most user-friendly way.

    def __init__(self, name, title=None, icon=None, menu=None, quit_button='Quit'):
        _require_string(name)
        self._name = name
        self._icon = self._icon_nsimage = self._title = None
        self.icon = icon
        self.title = title
        self.quit_button = quit_button
        self._menu = Menu()
        if menu is not None:
            self.menu = menu
        self._application_support = application_support(self._name)

    # Properties
    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @property
    def name(self):
        """The name of the application. Determines the application support folder name. Will also serve as the title
        text of the application if :attr:`title` is not set.
        """
        return self._name

    @property
    def title(self):
        """The text that will be displayed for the application in the statusbar. Can be ``None`` in which case the icon
        will be used or, if there is no icon set the application text will fallback on the application :attr:`name`.

        .. versionchanged:: 0.2.0
           If the title is set then changed to ``None``, it will correctly be removed. Must be either a string or
           ``None``.

        """
        return self._title

    @title.setter
    def title(self, title):
        _require_string_or_none(title)
        self._title = title
        try:
            self._nsapp.setStatusBarTitle()
        except AttributeError:
            pass

    @property
    def icon(self):
        """A path to an image representing the icon that will be displayed for the application in the statusbar.
        Can be ``None`` in which case the text from :attr:`title` will be used.

        .. versionchanged:: 0.2.0
           If the icon is set to an image then changed to ``None``, it will correctly be removed.

        """
        return self._icon

    @icon.setter
    def icon(self, icon_path):
        new_icon = _nsimage_from_file(icon_path) if icon_path is not None else None
        self._icon = icon_path
        self._icon_nsimage = new_icon
        try:
            self._nsapp.setStatusBarIcon()
        except AttributeError:
            pass

    @property
    def menu(self):
        """Represents the main menu of the statusbar application. Setting `menu` works by calling
        :meth:`rumps.MenuItem.update`.
        """
        return self._menu

    @menu.setter
    def menu(self, iterable):
        self._menu.update(iterable)

    @property
    def quit_button(self):
        """The quit application menu item within the main menu. This is a special :class:`rumps.MenuItem` object that
        will both replace any function callback with :func:`rumps.quit_application` and add itself to the end of the
        main menu when :meth:`rumps.App.run` is called. If set to ``None``, the default quit button will not be added.

        .. warning::
           If set to ``None``, some other menu item should call :func:`rumps.quit_application` so that the
           application can exit gracefully.

        .. versionadded:: 0.2.0

        """
        return self._quit_button

    @quit_button.setter
    def quit_button(self, quit_text):
        if quit_text is None:
            self._quit_button = None
        else:
            self._quit_button = MenuItem(quit_text)

    # Open files in application support folder
    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def open(self, *args):
        """Open a file within the application support folder for this application.

        .. code-block:: python

            app = App('Cool App')
            with app.open('data.json') as f:
                pass

        Is a shortcut for,

        .. code-block:: python

            app = App('Cool App')
            filename = os.path.join(application_support(app.name), 'data.json')
            with open(filename) as f:
                pass

        """
        return open(os.path.join(self._application_support, args[0]), *args[1:])

    # Run the application
    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def run(self, **options):
        """Performs various setup tasks including creating the underlying Objective-C application, starting the timers,
        and registering callback functions for click events. Then starts the application run loop.

        .. versionchanged:: 0.2.1
            Accepts `debug` keyword argument.

        :param debug: determines if application should log information useful for debugging. Same effect as calling
                      :func:`rumps.debug_mode`.

        """
        dont_change = object()
        debug = options.get('debug', dont_change)
        if debug is not dont_change:
            debug_mode(debug)

        nsapplication = NSApplication.sharedApplication()
        nsapplication.activateIgnoringOtherApps_(True)  # NSAlerts in front
        self._nsapp = NSApp.alloc().init()
        self._nsapp._app = self.__dict__  # allow for dynamic modification based on this App instance
        nsapplication.setDelegate_(self._nsapp)
        if _NOTIFICATIONS:
            NSUserNotificationCenter.defaultUserNotificationCenter().setDelegate_(self._nsapp)

        setattr(App, '*app_instance', self)  # class level ref to running instance (for passing self to App subclasses)
        t = b = None
        for t in getattr(timer, '*timers', []):
            t.start()
        for b in getattr(clicked, '*buttons', []):
            b(self)  # we waited on registering clicks so we could pass self to access _menu attribute
        del t, b

        self._nsapp.initializeStatusBar()

        AppHelper.runEventLoop()
