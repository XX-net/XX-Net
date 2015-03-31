from __future__ import absolute_import
import sys
import os
import errno
import types
import gc
import signal
import traceback
from gevent.event import AsyncResult
from gevent.hub import get_hub, linkproxy, sleep, getcurrent
from gevent.fileobject import FileObject
from gevent.greenlet import Greenlet, joinall
spawn = Greenlet.spawn
import subprocess as __subprocess__


# Standard functions and classes that this module re-implements in a gevent-aware way.
__implements__ = ['Popen',
                  'call',
                  'check_call',
                  'check_output']


# Standard functions and classes that this module re-imports.
__imports__ = ['PIPE',
               'STDOUT',
               'CalledProcessError',
               # Windows:
               'CREATE_NEW_CONSOLE',
               'CREATE_NEW_PROCESS_GROUP',
               'STD_INPUT_HANDLE',
               'STD_OUTPUT_HANDLE',
               'STD_ERROR_HANDLE',
               'SW_HIDE',
               'STARTF_USESTDHANDLES',
               'STARTF_USESHOWWINDOW']


__extra__ = ['MAXFD',
             '_eintr_retry_call',
             'STARTUPINFO',
             'pywintypes',
             'list2cmdline',
             '_subprocess',
             # Python 2.5 does not have _subprocess, so we don't use it
             'WAIT_OBJECT_0',
             'WaitForSingleObject',
             'GetExitCodeProcess',
             'GetStdHandle',
             'CreatePipe',
             'DuplicateHandle',
             'GetCurrentProcess',
             'DUPLICATE_SAME_ACCESS',
             'GetModuleFileName',
             'GetVersion',
             'CreateProcess',
             'INFINITE',
             'TerminateProcess']


for name in __imports__[:]:
    try:
        value = getattr(__subprocess__, name)
        globals()[name] = value
    except AttributeError:
        __imports__.remove(name)
        __extra__.append(name)

if sys.version_info[:2] <= (2, 6):
    __implements__.remove('check_output')
    __extra__.append('check_output')

_subprocess = getattr(__subprocess__, '_subprocess', None)
_NONE = object()

for name in __extra__[:]:
    if name in globals():
        continue
    value = _NONE
    try:
        value = getattr(__subprocess__, name)
    except AttributeError:
        if _subprocess is not None:
            try:
                value = getattr(_subprocess, name)
            except AttributeError:
                pass
    if value is _NONE:
        __extra__.remove(name)
    else:
        globals()[name] = value


__all__ = __implements__ + __imports__


mswindows = sys.platform == 'win32'
if mswindows:
    import msvcrt
else:
    import fcntl
    import pickle
    from gevent import monkey
    fork = monkey.get_original('os', 'fork')


def call(*popenargs, **kwargs):
    """Run command with arguments.  Wait for command to complete, then
    return the returncode attribute.

    The arguments are the same as for the Popen constructor.  Example:

    retcode = call(["ls", "-l"])
    """
    return Popen(*popenargs, **kwargs).wait()


def check_call(*popenargs, **kwargs):
    """Run command with arguments.  Wait for command to complete.  If
    the exit code was zero then return, otherwise raise
    CalledProcessError.  The CalledProcessError object will have the
    return code in the returncode attribute.

    The arguments are the same as for the Popen constructor.  Example:

    check_call(["ls", "-l"])
    """
    retcode = call(*popenargs, **kwargs)
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd)
    return 0


def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.

    The arguments are the same as for the Popen constructor.  Example:

    >>> check_output(["ls", "-1", "/dev/null"])
    '/dev/null\n'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> check_output(["/bin/sh", "-c", "echo hello world"], stderr=STDOUT)
    'hello world\n'
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = Popen(stdout=PIPE, *popenargs, **kwargs)
    output = process.communicate()[0]
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        ex = CalledProcessError(retcode, cmd)
        # on Python 2.6 and older CalledProcessError does not accept 'output' argument
        ex.output = output
        raise ex
    return output


class Popen(object):

    def __init__(self, args, bufsize=0, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=False, shell=False,
                 cwd=None, env=None, universal_newlines=False,
                 startupinfo=None, creationflags=0, threadpool=None):
        """Create new Popen instance."""
        if not isinstance(bufsize, (int, long)):
            raise TypeError("bufsize must be an integer")
        hub = get_hub()

        if mswindows:
            if preexec_fn is not None:
                raise ValueError("preexec_fn is not supported on Windows "
                                 "platforms")
            if close_fds and (stdin is not None or stdout is not None or
                              stderr is not None):
                raise ValueError("close_fds is not supported on Windows "
                                 "platforms if you redirect stdin/stdout/stderr")
            if threadpool is None:
                threadpool = hub.threadpool
            self.threadpool = threadpool
            self._waiting = False
        else:
            # POSIX
            if startupinfo is not None:
                raise ValueError("startupinfo is only supported on Windows "
                                 "platforms")
            if creationflags != 0:
                raise ValueError("creationflags is only supported on Windows "
                                 "platforms")
            assert threadpool is None
            self._loop = hub.loop

        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.pid = None
        self.returncode = None
        self.universal_newlines = universal_newlines
        self.result = AsyncResult()

        # Input and output objects. The general principle is like
        # this:
        #
        # Parent                   Child
        # ------                   -----
        # p2cwrite   ---stdin--->  p2cread
        # c2pread    <--stdout---  c2pwrite
        # errread    <--stderr---  errwrite
        #
        # On POSIX, the child objects are file descriptors.  On
        # Windows, these are Windows file handles.  The parent objects
        # are file descriptors on both platforms.  The parent objects
        # are None when not using PIPEs. The child objects are None
        # when not redirecting.

        (p2cread, p2cwrite,
         c2pread, c2pwrite,
         errread, errwrite) = self._get_handles(stdin, stdout, stderr)

        self._execute_child(args, executable, preexec_fn, close_fds,
                            cwd, env, universal_newlines,
                            startupinfo, creationflags, shell,
                            p2cread, p2cwrite,
                            c2pread, c2pwrite,
                            errread, errwrite)

        if mswindows:
            if p2cwrite is not None:
                p2cwrite = msvcrt.open_osfhandle(p2cwrite.Detach(), 0)
            if c2pread is not None:
                c2pread = msvcrt.open_osfhandle(c2pread.Detach(), 0)
            if errread is not None:
                errread = msvcrt.open_osfhandle(errread.Detach(), 0)

        if p2cwrite is not None:
            self.stdin = FileObject(p2cwrite, 'wb')
        if c2pread is not None:
            if universal_newlines:
                self.stdout = FileObject(c2pread, 'rU')
            else:
                self.stdout = FileObject(c2pread, 'rb')
        if errread is not None:
            if universal_newlines:
                self.stderr = FileObject(errread, 'rU')
            else:
                self.stderr = FileObject(errread, 'rb')

    def __repr__(self):
        return '<%s at 0x%x pid=%r returncode=%r>' % (self.__class__.__name__, id(self), self.pid, self.returncode)

    def _on_child(self, watcher):
        watcher.stop()
        status = watcher.rstatus
        if os.WIFSIGNALED(status):
            self.returncode = -os.WTERMSIG(status)
        else:
            self.returncode = os.WEXITSTATUS(status)
        self.result.set(self.returncode)

    def communicate(self, input=None):
        """Interact with process: Send data to stdin.  Read data from
        stdout and stderr, until end-of-file is reached.  Wait for
        process to terminate.  The optional input argument should be a
        string to be sent to the child process, or None, if no data
        should be sent to the child.

        communicate() returns a tuple (stdout, stderr)."""
        greenlets = []
        if self.stdin:
            greenlets.append(spawn(write_and_close, self.stdin, input))

        if self.stdout:
            stdout = spawn(self.stdout.read)
            greenlets.append(stdout)
        else:
            stdout = None

        if self.stderr:
            stderr = spawn(self.stderr.read)
            greenlets.append(stderr)
        else:
            stderr = None

        joinall(greenlets)

        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()

        self.wait()
        return (None if stdout is None else stdout.value or '',
                None if stderr is None else stderr.value or '')

    def poll(self):
        return self._internal_poll()

    def rawlink(self, callback):
        self.result.rawlink(linkproxy(callback, self))
    # XXX unlink

    if mswindows:
        #
        # Windows methods
        #
        def _get_handles(self, stdin, stdout, stderr):
            """Construct and return tuple with IO objects:
            p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite
            """
            if stdin is None and stdout is None and stderr is None:
                return (None, None, None, None, None, None)

            p2cread, p2cwrite = None, None
            c2pread, c2pwrite = None, None
            errread, errwrite = None, None

            if stdin is None:
                p2cread = GetStdHandle(STD_INPUT_HANDLE)
                if p2cread is None:
                    p2cread, _ = CreatePipe(None, 0)
            elif stdin == PIPE:
                p2cread, p2cwrite = CreatePipe(None, 0)
            elif isinstance(stdin, int):
                p2cread = msvcrt.get_osfhandle(stdin)
            else:
                # Assuming file-like object
                p2cread = msvcrt.get_osfhandle(stdin.fileno())
            p2cread = self._make_inheritable(p2cread)

            if stdout is None:
                c2pwrite = GetStdHandle(STD_OUTPUT_HANDLE)
                if c2pwrite is None:
                    _, c2pwrite = CreatePipe(None, 0)
            elif stdout == PIPE:
                c2pread, c2pwrite = CreatePipe(None, 0)
            elif isinstance(stdout, int):
                c2pwrite = msvcrt.get_osfhandle(stdout)
            else:
                # Assuming file-like object
                c2pwrite = msvcrt.get_osfhandle(stdout.fileno())
            c2pwrite = self._make_inheritable(c2pwrite)

            if stderr is None:
                errwrite = GetStdHandle(STD_ERROR_HANDLE)
                if errwrite is None:
                    _, errwrite = CreatePipe(None, 0)
            elif stderr == PIPE:
                errread, errwrite = CreatePipe(None, 0)
            elif stderr == STDOUT:
                errwrite = c2pwrite
            elif isinstance(stderr, int):
                errwrite = msvcrt.get_osfhandle(stderr)
            else:
                # Assuming file-like object
                errwrite = msvcrt.get_osfhandle(stderr.fileno())
            errwrite = self._make_inheritable(errwrite)

            return (p2cread, p2cwrite,
                    c2pread, c2pwrite,
                    errread, errwrite)

        def _make_inheritable(self, handle):
            """Return a duplicate of handle, which is inheritable"""
            return DuplicateHandle(GetCurrentProcess(),
                                   handle, GetCurrentProcess(), 0, 1,
                                   DUPLICATE_SAME_ACCESS)

        def _find_w9xpopen(self):
            """Find and return absolut path to w9xpopen.exe"""
            w9xpopen = os.path.join(os.path.dirname(GetModuleFileName(0)),
                                    "w9xpopen.exe")
            if not os.path.exists(w9xpopen):
                # Eeek - file-not-found - possibly an embedding
                # situation - see if we can locate it in sys.exec_prefix
                w9xpopen = os.path.join(os.path.dirname(sys.exec_prefix),
                                        "w9xpopen.exe")
                if not os.path.exists(w9xpopen):
                    raise RuntimeError("Cannot locate w9xpopen.exe, which is "
                                       "needed for Popen to work with your "
                                       "shell or platform.")
            return w9xpopen

        def _execute_child(self, args, executable, preexec_fn, close_fds,
                           cwd, env, universal_newlines,
                           startupinfo, creationflags, shell,
                           p2cread, p2cwrite,
                           c2pread, c2pwrite,
                           errread, errwrite):
            """Execute program (MS Windows version)"""

            if not isinstance(args, types.StringTypes):
                args = list2cmdline(args)

            # Process startup details
            if startupinfo is None:
                startupinfo = STARTUPINFO()
            if None not in (p2cread, c2pwrite, errwrite):
                startupinfo.dwFlags |= STARTF_USESTDHANDLES
                startupinfo.hStdInput = p2cread
                startupinfo.hStdOutput = c2pwrite
                startupinfo.hStdError = errwrite

            if shell:
                startupinfo.dwFlags |= STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = SW_HIDE
                comspec = os.environ.get("COMSPEC", "cmd.exe")
                args = '{} /c "{}"'.format(comspec, args)
                if GetVersion() >= 0x80000000 or os.path.basename(comspec).lower() == "command.com":
                    # Win9x, or using command.com on NT. We need to
                    # use the w9xpopen intermediate program. For more
                    # information, see KB Q150956
                    # (http://web.archive.org/web/20011105084002/http://support.microsoft.com/support/kb/articles/Q150/9/56.asp)
                    w9xpopen = self._find_w9xpopen()
                    args = '"%s" %s' % (w9xpopen, args)
                    # Not passing CREATE_NEW_CONSOLE has been known to
                    # cause random failures on win9x.  Specifically a
                    # dialog: "Your program accessed mem currently in
                    # use at xxx" and a hopeful warning about the
                    # stability of your system.  Cost is Ctrl+C wont
                    # kill children.
                    creationflags |= CREATE_NEW_CONSOLE

            # Start the process
            try:
                hp, ht, pid, tid = CreateProcess(executable, args,
                                                 # no special security
                                                 None, None,
                                                 int(not close_fds),
                                                 creationflags,
                                                 env,
                                                 cwd,
                                                 startupinfo)
            except pywintypes.error, e:
                # Translate pywintypes.error to WindowsError, which is
                # a subclass of OSError.  FIXME: We should really
                # translate errno using _sys_errlist (or similar), but
                # how can this be done from Python?
                raise WindowsError(*e.args)
            finally:
                # Child is launched. Close the parent's copy of those pipe
                # handles that only the child should have open.  You need
                # to make sure that no handles to the write end of the
                # output pipe are maintained in this process or else the
                # pipe will not close when the child process exits and the
                # ReadFile will hang.
                if p2cread is not None:
                    p2cread.Close()
                if c2pwrite is not None:
                    c2pwrite.Close()
                if errwrite is not None:
                    errwrite.Close()

            # Retain the process handle, but close the thread handle
            self._handle = hp
            self.pid = pid
            ht.Close()

        def _internal_poll(self):
            """Check if child process has terminated.  Returns returncode
            attribute.
            """
            if self.returncode is None:
                if WaitForSingleObject(self._handle, 0) == WAIT_OBJECT_0:
                    self.returncode = GetExitCodeProcess(self._handle)
                    self.result.set(self.returncode)
            return self.returncode

        def rawlink(self, callback):
            if not self.result.ready() and not self._waiting:
                self._waiting = True
                Greenlet.spawn(self._wait)
            self.result.rawlink(linkproxy(callback, self))
            # XXX unlink

        def _blocking_wait(self):
            WaitForSingleObject(self._handle, INFINITE)
            self.returncode = GetExitCodeProcess(self._handle)
            return self.returncode

        def _wait(self):
            self.threadpool.spawn(self._blocking_wait).rawlink(self.result)

        def wait(self, timeout=None):
            """Wait for child process to terminate.  Returns returncode
            attribute."""
            if self.returncode is None:
                if not self._waiting:
                    self._waiting = True
                    self._wait()
            return self.result.wait(timeout=timeout)

        def send_signal(self, sig):
            """Send a signal to the process
            """
            if sig == signal.SIGTERM:
                self.terminate()
            elif sig == signal.CTRL_C_EVENT:
                os.kill(self.pid, signal.CTRL_C_EVENT)
            elif sig == signal.CTRL_BREAK_EVENT:
                os.kill(self.pid, signal.CTRL_BREAK_EVENT)
            else:
                raise ValueError("Unsupported signal: {}".format(sig))

        def terminate(self):
            """Terminates the process
            """
            TerminateProcess(self._handle, 1)

        kill = terminate

    else:
        #
        # POSIX methods
        #
        def _get_handles(self, stdin, stdout, stderr):
            """Construct and return tuple with IO objects:
            p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite
            """
            p2cread, p2cwrite = None, None
            c2pread, c2pwrite = None, None
            errread, errwrite = None, None

            if stdin is None:
                pass
            elif stdin == PIPE:
                p2cread, p2cwrite = self.pipe_cloexec()
            elif isinstance(stdin, int):
                p2cread = stdin
            else:
                # Assuming file-like object
                p2cread = stdin.fileno()

            if stdout is None:
                pass
            elif stdout == PIPE:
                c2pread, c2pwrite = self.pipe_cloexec()
            elif isinstance(stdout, int):
                c2pwrite = stdout
            else:
                # Assuming file-like object
                c2pwrite = stdout.fileno()

            if stderr is None:
                pass
            elif stderr == PIPE:
                errread, errwrite = self.pipe_cloexec()
            elif stderr == STDOUT:
                errwrite = c2pwrite
            elif isinstance(stderr, int):
                errwrite = stderr
            else:
                # Assuming file-like object
                errwrite = stderr.fileno()

            return (p2cread, p2cwrite,
                    c2pread, c2pwrite,
                    errread, errwrite)

        def _set_cloexec_flag(self, fd, cloexec=True):
            try:
                cloexec_flag = fcntl.FD_CLOEXEC
            except AttributeError:
                cloexec_flag = 1

            old = fcntl.fcntl(fd, fcntl.F_GETFD)
            if cloexec:
                fcntl.fcntl(fd, fcntl.F_SETFD, old | cloexec_flag)
            else:
                fcntl.fcntl(fd, fcntl.F_SETFD, old & ~cloexec_flag)

        def _remove_nonblock_flag(self, fd):
            flags = fcntl.fcntl(fd, fcntl.F_GETFL) & (~os.O_NONBLOCK)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)

        def pipe_cloexec(self):
            """Create a pipe with FDs set CLOEXEC."""
            # Pipes' FDs are set CLOEXEC by default because we don't want them
            # to be inherited by other subprocesses: the CLOEXEC flag is removed
            # from the child's FDs by _dup2(), between fork() and exec().
            # This is not atomic: we would need the pipe2() syscall for that.
            r, w = os.pipe()
            self._set_cloexec_flag(r)
            self._set_cloexec_flag(w)
            return r, w

        def _close_fds(self, but):
            if hasattr(os, 'closerange'):
                os.closerange(3, but)
                os.closerange(but + 1, MAXFD)
            else:
                for i in xrange(3, MAXFD):
                    if i == but:
                        continue
                    try:
                        os.close(i)
                    except:
                        pass

        def _execute_child(self, args, executable, preexec_fn, close_fds,
                           cwd, env, universal_newlines,
                           startupinfo, creationflags, shell,
                           p2cread, p2cwrite,
                           c2pread, c2pwrite,
                           errread, errwrite):
            """Execute program (POSIX version)"""

            if isinstance(args, types.StringTypes):
                args = [args]
            else:
                args = list(args)

            if shell:
                args = ["/bin/sh", "-c"] + args
                if executable:
                    args[0] = executable

            if executable is None:
                executable = args[0]

            self._loop.install_sigchld()

            # For transferring possible exec failure from child to parent
            # The first char specifies the exception type: 0 means
            # OSError, 1 means some other error.
            errpipe_read, errpipe_write = self.pipe_cloexec()
            try:
                try:
                    gc_was_enabled = gc.isenabled()
                    # Disable gc to avoid bug where gc -> file_dealloc ->
                    # write to stderr -> hang.  http://bugs.python.org/issue1336
                    gc.disable()
                    try:
                        self.pid = fork()
                    except:
                        if gc_was_enabled:
                            gc.enable()
                        raise
                    if self.pid == 0:
                        # Child
                        try:
                            # Close parent's pipe ends
                            if p2cwrite is not None:
                                os.close(p2cwrite)
                            if c2pread is not None:
                                os.close(c2pread)
                            if errread is not None:
                                os.close(errread)
                            os.close(errpipe_read)

                            # When duping fds, if there arises a situation
                            # where one of the fds is either 0, 1 or 2, it
                            # is possible that it is overwritten (#12607).
                            if c2pwrite == 0:
                                c2pwrite = os.dup(c2pwrite)
                            if errwrite == 0 or errwrite == 1:
                                errwrite = os.dup(errwrite)

                            # Dup fds for child
                            def _dup2(a, b):
                                # dup2() removes the CLOEXEC flag but
                                # we must do it ourselves if dup2()
                                # would be a no-op (issue #10806).
                                if a == b:
                                    self._set_cloexec_flag(a, False)
                                elif a is not None:
                                    os.dup2(a, b)
                                self._remove_nonblock_flag(b)
                            _dup2(p2cread, 0)
                            _dup2(c2pwrite, 1)
                            _dup2(errwrite, 2)

                            # Close pipe fds.  Make sure we don't close the
                            # same fd more than once, or standard fds.
                            closed = set([None])
                            for fd in [p2cread, c2pwrite, errwrite]:
                                if fd not in closed and fd > 2:
                                    os.close(fd)
                                    closed.add(fd)

                            # Close all other fds, if asked for
                            if close_fds:
                                self._close_fds(but=errpipe_write)

                            if cwd is not None:
                                os.chdir(cwd)

                            if preexec_fn:
                                preexec_fn()

                            if env is None:
                                os.execvp(executable, args)
                            else:
                                os.execvpe(executable, args, env)

                        except:
                            exc_type, exc_value, tb = sys.exc_info()
                            # Save the traceback and attach it to the exception object
                            exc_lines = traceback.format_exception(exc_type,
                                                                   exc_value,
                                                                   tb)
                            exc_value.child_traceback = ''.join(exc_lines)
                            os.write(errpipe_write, pickle.dumps(exc_value))

                        finally:
                            # Make sure that the process exits no matter what.
                            # The return code does not matter much as it won't be
                            # reported to the application
                            os._exit(1)

                    # Parent
                    self._watcher = self._loop.child(self.pid)
                    self._watcher.start(self._on_child, self._watcher)

                    if gc_was_enabled:
                        gc.enable()
                finally:
                    # be sure the FD is closed no matter what
                    os.close(errpipe_write)

                if p2cread is not None and p2cwrite is not None:
                    os.close(p2cread)
                if c2pwrite is not None and c2pread is not None:
                    os.close(c2pwrite)
                if errwrite is not None and errread is not None:
                    os.close(errwrite)

                # Wait for exec to fail or succeed; possibly raising exception
                errpipe_read = FileObject(errpipe_read, 'rb')
                data = errpipe_read.read()
            finally:
                if hasattr(errpipe_read, 'close'):
                    errpipe_read.close()
                else:
                    os.close(errpipe_read)

            if data != "":
                self.wait()
                child_exception = pickle.loads(data)
                for fd in (p2cwrite, c2pread, errread):
                    if fd is not None:
                        os.close(fd)
                raise child_exception

        def _handle_exitstatus(self, sts):
            if os.WIFSIGNALED(sts):
                self.returncode = -os.WTERMSIG(sts)
            elif os.WIFEXITED(sts):
                self.returncode = os.WEXITSTATUS(sts)
            else:
                # Should never happen
                raise RuntimeError("Unknown child exit status!")

        def _internal_poll(self):
            """Check if child process has terminated.  Returns returncode
            attribute.
            """
            if self.returncode is None:
                if get_hub() is not getcurrent():
                    sig_pending = getattr(self._loop, 'sig_pending', True)
                    if sig_pending:
                        sleep(0.00001)
            return self.returncode

        def wait(self, timeout=None):
            """Wait for child process to terminate.  Returns returncode
            attribute."""
            return self.result.wait(timeout=timeout)

        def send_signal(self, sig):
            """Send a signal to the process
            """
            os.kill(self.pid, sig)

        def terminate(self):
            """Terminate the process with SIGTERM
            """
            self.send_signal(signal.SIGTERM)

        def kill(self):
            """Kill the process with SIGKILL
            """
            self.send_signal(signal.SIGKILL)


def write_and_close(fobj, data):
    try:
        if data:
            fobj.write(data)
    except (OSError, IOError), ex:
        if ex.errno != errno.EPIPE and ex.errno != errno.EINVAL:
            raise
    finally:
        try:
            fobj.close()
        except EnvironmentError:
            pass
