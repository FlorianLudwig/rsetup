#
__version__ = '1.7.2'

class exception:
    class Error(Exception):
        def __str__(self):
            return "%s: %s" %(self.__class__.__name__, self.args[0])
    class ConfigError(Error):
        """ error in tox configuration. """
    class UnsupportedInterpreter(Error):
        "signals an unsupported Interpreter"
    class InterpreterNotFound(Error):
        "signals that an interpreter could not be found"
    class InvocationError(Error):
        """ an error while invoking a script. """
    class MissingFile(Error):
        """ an error while invoking a script. """
    class MissingDirectory(Error):
        """ a directory did not exist. """
    class MissingDependency(Error):
        """ a dependency could not be found or determined. """

from tox._cmdline import main as cmdline  # noqa
