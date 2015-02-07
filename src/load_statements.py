'''
This script would load statements from various sites
'''
import os
import pandas
import xlrd
import optparse
import logging
from utils import formatted_filepath, get_logger, raise_error_msg

domain_settings = {
        'hdfcsec': {'num_header_rows': 5}
        }

def adjust_multirow_header(df, num_header_rows):
    header_df = df.loc[0:num_header_rows-1,:]
    columns = []
    for key in header_df.keys():
        tmp_header_df = header_df[header_df[key].notnull()]
        column = ' '.join(tmp_header_df[key].values)
        columns.append(column)
    earlier_len = len(df)
    df = df.loc[num_header_rows:,:]
    later_len = len(df)
    if earlier_len-num_header_rows != later_len:
        raise_error_msg("Header information is not set properly for %s from %s", txn_file, domain)
    df.columns = columns
    return df

def handle_xls(domain, txn_file, outdir, num_header_rows):
    df = pandas.read_excel(txn_file, 0, header=None)
    df = adjust_multirow_header(df, num_header_rows)
    csv_path = os.path.join(outdir, formatted_filepath(os.path.basename(txn_file), suffix='csv'))
    df.to_csv(csv_path, index=False)
    return df

def handle_csv(domain, txn_file, outdir, num_header_rows):
    df = pandas.read_csv(txn_file, header=None)
    df = adjust_multirow_header(df, num_header_rows)
    return df

def main(domain, txn_files, outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    assert domain in domain_settings
    num_header_rows = domain_settings[domain]['num_header_rows']
    for txn_file in txn_files.split(','):
        if 'xls' in txn_file:
            txn_df = handle_xls(domain, txn_file, outdir, num_header_rows)
        elif 'csv' in txn_file:
            txn_df = handle_csv(domain, txn_file, outdir, num_header_rows)
        else:
            raise_error_msg("Only xls, xlsx, csv format are supported")
        print txn_df.head(3)
        csv_path = os.path.join(outdir, formatted_filepath(os.path.basename(txn_file).split(os.path.extsep)[0], sep=os.path.extsep, suffix='csv'))
        txn_df.to_csv(csv_path, index=False)
        print "Saved processed csv at", csv_path
    return

def parse_args():
    default_output = formatted_filepath('output', datestamp=True)
    default_logger = formatted_filepath(suffix='log', sep='.')
    parser = optparse.OptionParser()
    parser.add_option("", "--domain", default=None, help="Site name. Supported, hdfcsec")
    parser.add_option("", "--txn-files", default=None, help="Transaction csv files. Multiple values supported as comma-separated-values")
    parser.add_option("-o", "--outdir", default=default_output, help="Output dir name")
    parser.add_option("-l", "--logfile", default=default_logger, help="Logfile name")
    (options, args) = parser.parse_args()
    if not (options.domain and options.txn_files):
        parser.print_help()
        raise_error_msg("Mandatory arguments missing!! Please check")
    return (options, args)

if __name__ == '__main__':
    try:
        options, args = parse_args()
        logger = get_logger(options.logfile)
        logger.info("%s BEGIN %s"%('-'*40, '-'*40))
        main(options.domain, options.txn_files, options.outdir)
        logger.info("%s THE END %s"%('-'*40, '-'*40))
    except Exception, ee:
        logging.exception(str(ee))
        import traceback
        print traceback.print_exc()

