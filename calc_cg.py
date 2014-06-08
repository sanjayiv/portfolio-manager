'''
Notes: Keep all COMMON UTIL functions here. Repeat, "COMMON UTIL"
'''
import os, sys, datetime
import logging
import optparse

# utils

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

def get_logger(filename='', format="%(asctime)s: %(levelname)s: %(message)s", level=logging.DEBUG):
    filename = filename or formatted_filepath('', 'log', '.')
    logging.basicConfig(filename=filename, format="%(asctime)s: %(levelname)s: %(message)s", level=logging.DEBUG)
    return logging.getLogger(filename)

def main(txncsvs, outdir, logger):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print "Created `%s` output dir"%outdir
    else:
        print "Output dir `%s` already exists! Overwriting content"%outdir
    for eachcsv in txncsvs.split(','):
        print eachcsv

def parse_args():
    default_output = formatted_filepath('output', datestamp=True)
    default_logger = formatted_filepath(suffix='log', sep='.')
    parser = optparse.OptionParser()
    parser.add_option("", "--txncsvs", default=None, help="CSV files with txn, multiple files can be passed as comma,separated")
    parser.add_option("-o", "--outdir", default=default_output, help="Output dir name")
    parser.add_option("-l", "--logger", default=default_logger, help="Log name")
    (options, args) = parser.parse_args()
    if not (options.txncsvs):
        parser.print_help()
        sys.exit(1)
    return (options, args)

if __name__ == '__main__':
    try:
        options, args = parse_args()
        logger = get_logger(options.logger)
        main(options.txncsvs, options.outdir, logger)
    except SystemExit, ee:
        if 1 == ee.code:
            print "Error: Mandatory arguments missing!!"
        else:
            print str(ee)
    except Exception, ee:
        import traceback
        print traceback.print_exc()

