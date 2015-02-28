'''
Notes: Keep all COMMON UTIL functions here. Repeat, "COMMON UTIL"
'''
import os, sys
import time, datetime
import logging

## Returns filename in the format of "[basename][date/timestamp][sep][suffix]"
# @param basename a string, for basename to be used
# @param suffix a string, for suffix to be used as a file extension
# @param sep a string, for separator
# @param datestamp a boolean, for enabling datestamp with basename
# @param timestamp a boolean, for enabling timestamp with basename
def formatted_filepath(basename='', suffix='', sep='', datestamp=False, timestamp=False):
    '''
    Returns filename in the format of "[basename][date/timestamp][sep][suffix]"
    Example#1
    >>> formatted_filepath('utils', 'log', '.')
    'utils.log'
    '''
    basename = basename or "%s"%(sys.argv[0].split(os.path.extsep,1)[0])
    if timestamp:
        basename += "_%s"%( datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%dT%H%M%S") )
    elif datestamp:
        basename += "_%s"%( datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d") )
    return "%s%s%s"%(basename, sep, suffix)

## Return python logger
# @param filename a string, for logger filename
# @param format a string, for logging format. Must comply with logging format
# @param level an int, for setting log level to DEBUG/INFO/ERROR
def get_logger(filename='', format="%(asctime)s: %(levelname)s: %(message)s", level=logging.DEBUG):
    filename = filename or formatted_filepath('', 'log', '.')
    logging.basicConfig(filename=filename, format="%(asctime)s: %(levelname)s: %(message)s", level=logging.DEBUG)
    return logging.getLogger(filename)

## raises exception with given error message
# @param err_msg error message to display
def raise_error_msg(err_msg, *kwds):
    '''
    Example:
    >>> raise_error_msg('Hello World!')
    Traceback (most recent call last):
       ...
    ValueError: Hello World!

    >>> raise_error_msg('Hello %s%s%s%s%s!', 'W', 'O', 'R', 'L', 'D')
    Traceback (most recent call last):
       ...
    ValueError: Hello WORLD!
    '''
    if kwds:
        raise ValueError(err_msg%(kwds))
    else:
        raise ValueError(err_msg)

## gracefully exit the execution after showing error message
# @param warning_msg warning message to display
# @param kwds all other keyword arguments to warning_msg
def graceful_exit(warning_msg, *kwds):
    if kwds:
        print(warning_msg%(kwds))
    else:
        print(warning_msg)
    sys.exit(0)

## return pretty log message for given message
# @param message a text, for logging or rendering
def pretty_log(message, line_padding=0, decorator="-"):
    return "\n"*(line_padding) + \
            decorator*(4+len(message)) + \
            "\n| " + message + " |\n" + \
            decorator*(4+len(message)) + \
            "\n"*line_padding

