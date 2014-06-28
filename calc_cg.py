'''
Notes:
- tbt: to-be-taxed (this is considering just price & brokamt)
- ebt: earning before tax (this is netamount)
- buy_price: is going to be -ve (its a cost)
- sell_price: is going to be +ve (its a gain)
- brokamt: +ve valued, 
    effective_price = buy_price-brokamt for buy
    effective_price = sell_price+brokamt for sell
- pat: profit after tax
'''
import os, sys, datetime
import logging
import optparse
import pandas
import numpy

# utils

STCG_NUM_DAYS = 365
STCG_TAX_PCT = 15.0

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

def load_txtcsvs(txncsvs):
    df_is_empty = True
    txndf = None
    for eachcsv in txncsvs.split(','):
        logging.info("Loading txncsv `%s`"%eachcsv)
        assert os.path.exists(eachcsv)
        tmpdf = pandas.read_csv(eachcsv, header=None)
        if df_is_empty:
            df_is_empty = False
            txndf = tmpdf
        else:
            txndf = pandas.concat([txndf, tmpdf])
    columns = [ 'trddate', 'trdno', 'orderno', 'exchange', 'settno', 'setttype', 'trdtime', 'ordertime',
        'scrip', 'buysell', 'qty', 'price', 'value', 'squpdel', 'brokamt', 'servtax', 'stampduty', 
        'txnchg', 'stotc', 'stt', 'sebitt', 'educess', 'higheducess', 'otherchg', 'netamt',
        'product', 'sipflag', 'siprefno']
    assert len(columns) == len(txndf.columns)
    txndf.columns = columns
    assert set(txndf.buysell) == set(['S','B'])
    logging.info("All txncsvs loaded in to txndf: %d records"%(len(txndf.trdno)))
    print("All txncsvs loaded in to txndf: %d records"%(len(txndf.trdno)))
    txndf.drop_duplicates(inplace=True)
    logging.info("After removing duplicates in txndf: %d records"%(len(txndf.trdno)))
    print("After removing duplicates in txndf: %d records"%(len(txndf.trdno)))
    return txndf

def calc_per_share_values(txndf):
    txndf['trddatetime'] = txndf.apply(lambda r: datetime.datetime.strptime(r.ix['trddate']+r.ix['trdtime'], "%d-%b-%y%H:%M:%S"), axis=1)
    txndf['price'] = txndf.apply(lambda r: -1*r.ix['price'] if 'B' == r.ix['buysell'] else r.ix['price'], axis=1)
    txndf['netamt_ps_tbt'] = txndf.buysell.apply(lambda bs: -1 if 'B' == bs else 1)
    txndf['netamt_ps_tbt'] = txndf.apply(lambda r: (r.ix['netamt_ps_tbt']*r.ix['value']-r.ix['brokamt'])/r.ix['qty'], axis=1)
    txndf['netamt_ps_real'] = txndf.apply(lambda r: r.ix['netamt']/r.ix['qty'], axis=1)
    # round off to 3 decimals
    txndf['netamt_ps_tbt'] = txndf.netamt_ps_tbt.apply(lambda v: round(v,3))
    txndf['netamt_ps_real'] = txndf.netamt_ps_real.apply(lambda v: round(v,3))
    return txndf

def match_buys_for_sells(txndf):
    gains_records = []
    sell_txndf = txndf[txndf.buysell=='S']
    sell_txndf = sell_txndf.sort('trddatetime')
    buy_txndf = txndf[txndf.buysell=='B']
    buy_txndf = buy_txndf.sort('trddatetime')
    for sell_irow, sell_txn in  sell_txndf.iterrows():
        logging.info("Sell-record#%s time: %s qty: %s price: %s ps_tbt: %s ps_real: %s scrip: %s"%(sell_irow, sell_txn.trddatetime, sell_txn.qty, sell_txn.price, sell_txn.netamt_ps_tbt, sell_txn.netamt_ps_real, sell_txn.scrip))
        for buy_irow, buy_txn in buy_txndf.iterrows():
            if buy_txn.scrip != sell_txn.scrip:
                continue
            if sell_txn.qty > 0 and buy_txn.qty > 0:
                logging.info("Buy-record#%s time: %s qty: %s price: %s ps_tbt: %s ps_real: %s scrip: %s"%(buy_irow, buy_txn.trddatetime, buy_txn.qty, buy_txn.price, buy_txn.netamt_ps_tbt, buy_txn.netamt_ps_real, buy_txn.scrip))
                min_qty = min(buy_txn.qty, sell_txn.qty)
                gains_records.append((buy_txn.scrip, min_qty, \
                        buy_txn.price+sell_txn.price, buy_txn.netamt_ps_tbt+sell_txn.netamt_ps_tbt, buy_txn.netamt_ps_real+sell_txn.netamt_ps_real, \
                        sell_txn.trddatetime, sell_txn.price, sell_txn.netamt_ps_tbt, sell_txn.netamt_ps_real, \
                        buy_txn.trddatetime, buy_txn.price, buy_txn.netamt_ps_tbt, buy_txn.netamt_ps_real))
                # updating buy_txn.qty or sell_txn.qty does NOT effect itended record, just a local change
                buy_txndf.qty[buy_irow] -= min_qty
                sell_txndf.qty[sell_irow] -= min_qty
                buy_txn.qty -= min_qty
                sell_txn.qty -= min_qty
                logging.info("Settled for %d qty"%min_qty)
    #
    header = ['scrip', 'qty', 'gain_price_ps', 'gain_tbt_ps', 'ebt_ps', 'sell_datetime', 'sell_price_ps', 'sell_tbt_ps', 'sell_real_ps', 'buy_datetime', 'buy_price_ps', 'buy_tbt_ps', 'buy_real_ps']
    gains_df = pandas.DataFrame(gains_records)
    assert len(gains_df.columns) == len(header)
    gains_df.columns = header
    return gains_df

def get_fy_dict(earliest_date, latest_date):
    earliest_year = earliest_date.year
    latest_year = latest_date.year
    fy_dict = {}
    for year in range(earliest_year, latest_year+2):
        fy_start = datetime.datetime(*(year-1,4,1,0,0,0))
        fy_end = datetime.datetime(*(year,3,31,23,59,59))
        fy = "FY-%d"%year
        print fy, fy_start, fy_end
        fy_dict[fy] = (fy_start, fy_end)
    return fy_dict

def fy_from_sell_datetime(sell_date):
    if sell_date.month <= 3:
        return "FY-%d"%sell_date.year
    else:
        return "FY-%d"%(sell_date.year+1)

def update_gains_df_for_summary(gains_df):
    gains_df['fy'] = gains_df.sell_datetime.apply(lambda dt: fy_from_sell_datetime(dt))
    gains_df['sell_date'] = gains_df.sell_datetime.apply(lambda dt: dt.date())
    gains_df['buy_date'] = gains_df.buy_datetime.apply(lambda dt: dt.date())
    gains_df['hold_days'] = gains_df.apply(lambda r: (r.ix['sell_datetime']-r.ix['buy_datetime']).days, axis=1)
    gains_df['sell_price'] = gains_df.apply(lambda r: r.ix['qty']*r.ix['sell_price_ps'], axis=1)
    gains_df['buy_price'] = gains_df.apply(lambda r: r.ix['qty']*r.ix['buy_price_ps'], axis=1)
    gains_df['gain_price'] = gains_df.apply(lambda r: r.ix['qty']*r.ix['gain_price_ps'], axis=1)
    gains_df['gain_tbt'] = gains_df.apply(lambda r: r.ix['qty']*r.ix['gain_tbt_ps'], axis=1)
    gains_df['ebt'] = gains_df.apply(lambda r: r.ix['qty']*r.ix['ebt_ps'], axis=1)
    gains_df['is_stcg'] = gains_df.apply(lambda r: True if (r.ix['hold_days'] <= STCG_NUM_DAYS) else False, axis=1)
    gains_df['stcg_tax'] = gains_df.apply(lambda r: STCG_TAX_PCT*r.ix['gain_tbt']/100.0 if r.ix['is_stcg'] else 0.0, axis=1)
    gains_df['pat'] = gains_df.apply(lambda r: r.ix['ebt']-r.ix['stcg_tax'], axis=1)
    #
    gains_df['gain_price_pct'] = gains_df.apply(lambda r: -100.0*r.ix['gain_price']/r.ix['buy_price'], axis=1)
    gains_df['gain_tbt_pct'] = gains_df.apply(lambda r: -100.0*r.ix['gain_tbt']/r.ix['buy_price'], axis=1)
    gains_df['ebt_pct'] = gains_df.apply(lambda r: -100.0*r.ix['ebt']/r.ix['buy_price'], axis=1)
    gains_df['pat_pct'] = gains_df.apply(lambda r: -100.0*r.ix['pat']/r.ix['buy_price'], axis=1)
    gains_df['cagr_price'] = gains_df.apply(lambda r: STCG_NUM_DAYS*r.ix['gain_price_pct']/max(1,r.ix['hold_days']), axis=1)
    gains_df['cagr_tbt'] = gains_df.apply(lambda r: STCG_NUM_DAYS*r.ix['gain_tbt_pct']/max(1,r.ix['hold_days']), axis=1)
    gains_df['cagr_ebt'] = gains_df.apply(lambda r: STCG_NUM_DAYS*r.ix['ebt_pct']/max(1,r.ix['hold_days']), axis=1)
    gains_df['cagr_pat'] = gains_df.apply(lambda r: STCG_NUM_DAYS*r.ix['pat_pct']/max(1,r.ix['hold_days']), axis=1)
    return gains_df

def apply_summary_gains(r):
    return (r.sum().qty, r.sum().sell_price, r.sum().buy_price, r.sum().gain_price, r.sum().gain_tbt, r.sum().ebt, r.sum().stcg_tax, r.mean().cagr_ebt, r.mean().cagr_pat)

def main(txncsvs, outdir, logger):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print "Created `%s` output dir"%outdir
    else:
        print "Output dir `%s` already exists! Overwriting content"%outdir
    txndf = load_txtcsvs(txncsvs)
    calc_per_share_values(txndf)
    print "Updated txndf for per-share values"
    gains_df = match_buys_for_sells(txndf)
    print "Matched sell records with buy records for txndf"
    update_gains_df_for_summary(gains_df)
    print "Updated gains_df for summary"
    fy_list = gains_df.fy.unique()
    for fy in fy_list:
        print "Processing for %s"%fy
        filename = os.path.join(outdir, 'detailed_gains_%s.csv'%fy)
        fy_gains_df = gains_df[gains_df.fy==fy]
        fy_gains_df.to_csv(filename)
        #
        summary_header = ['qty', 'sell_price', 'buy_price', 'gain_price', 'gain_tbt', 'ebt', 'stcg_tax', 'cagr_ebt', 'cagr_pat']
        filename = os.path.join(outdir, 'summary_gains_%s.csv'%fy)
        fy_gains_summary_dict = fy_gains_df.groupby(['scrip','sell_date','fy','is_stcg'], as_index=False).apply(apply_summary_gains).to_dict()
        output = open(filename, 'wb')
        output.write('%s\n'%(','.join(['scrip','sell_date','fy','is_stcg']+summary_header)))
        for key_tuple, value_tuple in fy_gains_summary_dict.iteritems():
            output.write('%s\n'%( ','.join( map(str, list(key_tuple) + map(lambda v: round(v,2),value_tuple)))))
        output.close()
        #
        filename = os.path.join(outdir, 'simple_gains_%s.csv'%fy)
        fy_gains_simple_dict = fy_gains_df.groupby(['scrip','fy','is_stcg'], as_index=False).apply(apply_summary_gains).to_dict()
        output = open(filename, 'wb')
        output.write('%s\n'%(','.join(['scrip','fy','is_stcg']+summary_header)))
        for key_tuple, value_tuple in fy_gains_simple_dict.iteritems():
            output.write('%s\n'%( ','.join( map(str, list(key_tuple) + map(lambda v: round(v,2),value_tuple)))))
        output.close()
        #print "%s: STCG: %s"%(fy, fy_gains_simple_df[fy_gains_simple_df.is_stcg==True].count())
        #print "%s: LTCG: %s"%(fy, fy_gains_simple_df[fy_gains_simple_df.is_ltcg==True].count())

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
        logger.info("%s BEGIN %s"%('-'*40, '-'*40))
        main(options.txncsvs, options.outdir, logger)
        logger.info("%s THE END %s"%('-'*40, '-'*40))
    except SystemExit, ee:
        if 1 == ee.code:
            print "Error: Mandatory arguments missing!!"
        else:
            print str(ee)
    except Exception, ee:
        import traceback
        print traceback.print_exc()

