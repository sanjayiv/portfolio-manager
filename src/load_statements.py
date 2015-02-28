'''
This script would load statements from various sites. ie hdfcsec

Input:
    - xls/csv of transactions
    - domain ie hdfcsec, sharekhan, icici

Output:
    - normalized csv with following columns 
    order_datetime / trade_datetime / scrip / buy_sell / quantity / trade_rate / brokerage_amount / net_rate / trade_total / net_total

Column description:
    order_datetime  : YYYYMMDDTHHMMSS
    trade_datetime  : YYYYMMDDTHHMMSS
    scrip           : scrip name
    buy_sell        : B/S
    quantity        : number of units
    trade_rate      : price per unit
    brokerage_amount: total brokerage amount
    net_rate        : net rate per unit ie (trade_rate +/- (brokerage_amount/quantity))
    trade_total     : total price ie (quantity*trade_rate)
    net_total       : net total price ie (quantity*net_rate)

'''
import os
import pandas
import xlrd
import optparse
import logging
from utils import formatted_filepath, get_logger, raise_error_msg, graceful_exit, pretty_log

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

def handle_xls(txn_file, outdir, num_header_rows):
    df = pandas.read_excel(txn_file, 0, header=None)
    if num_header_rows > 1:
        df = adjust_multirow_header(df, num_header_rows)
    return df

def handle_csv(txn_file, outdir, num_header_rows):
    df = pandas.read_csv(txn_file, header=None)
    if num_header_rows > 1:
        df = adjust_multirow_header(df, num_header_rows)
    return df

## main function to load and parse input statements
# @param domain a string, for domain ie hdfcsec / sharekhan / icici
# @param txn_type a string, for type of transcation ie stock / mf
# @param txn_files a string, for comma-separated-values for transcation report xls/csv files
# @param outdir a path, for output directory
def main(domain, txn_type, txn_files, outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if domain not in domain_settings:
        graceful_exit("--domain `%s` is not yet supported!", domain)
    txn_type = txn_type.lower()
    if txn_type not in ['stock', 'mf']:
        graceful_exit("--txn-type must be `stock` or `mf`. `%s` not yet supported!", txn_type)
    num_header_rows = domain_settings[domain]['num_header_rows']
    txn_df = pandas.DataFrame()
    for txn_file in txn_files.split(','):
        print("Parsing `%s`"%txn_file)
        if 'xls' in txn_file:
            tmp_txn_df = handle_xls(txn_file, outdir, num_header_rows)
        elif 'csv' in txn_file:
            tmp_txn_df = handle_csv(txn_file, outdir, num_header_rows)
        else:
            graceful_exit("Only xls, xlsx, csv format are supported")
        print("Loaded %d transactions from `%s`"%(len(tmp_txn_df), txn_file))
        try:
            txn_df = txn_df.append(tmp_txn_df)
        except Exception, ee:
            logging.error(str(ee))
            graceful_exit("ERROR ALERT: Print ensure all transaction reports are of same format")
    # txn_df is ready
    outfile = os.path.join(outdir, "%s_%s.csv"%(domain, txn_type))
    txn_df.to_csv(outfile, index=False)
    print("Saved processed transactions at `%s`"%outfile)

def parse_args():
    default_output = formatted_filepath('output', datestamp=True)
    default_logger = formatted_filepath(suffix='log', sep='.')
    parser = optparse.OptionParser()
    parser.add_option("", "--domain", default=None, help="Site name. Supported, hdfcsec")
    parser.add_option("", "--txn-type", default=None, help="Stock/MF")
    parser.add_option("", "--txn-files", default=None, help="Transaction csv/xls files. Multiple values supported as comma-separated-values")
    parser.add_option("-o", "--outdir", default=default_output, help="Output dir name")
    parser.add_option("-l", "--logfile", default=default_logger, help="Logfile name")
    (options, args) = parser.parse_args()
    if not (options.domain and options.txn_type and options.txn_files):
        parser.print_help()
        graceful_exit("Mandatory arguments missing!! Please try again")
    return (options, args)

if __name__ == '__main__':
    try:
        options, args = parse_args()
        logger = get_logger(options.logfile)
        logger.info(pretty_log("LOADING TRANSACTION REPORTS "))
        print(pretty_log("LOADING TRANSACTION REPORTS "))
        main(options.domain, options.txn_type, options.txn_files, options.outdir)
        print(pretty_log("LOADED TRANSACTION REPORTS"))
        logger.info(pretty_log("LOADED TRANSACTION REPORTS"))
    except Exception, ee:
        logging.exception(str(ee))
        import traceback
        print traceback.print_exc()

