'''
Notes: Keep all COMMON UTIL functions here. Repeat, "COMMON UTIL"
'''
import os, sys, datetime
import logging
import optparse
import pandas

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

def load_txtcsvs(txncsvs):
    df_is_empty = True
    txndf = None
    for eachcsv in txncsvs.split(','):
        print eachcsv
        assert os.path.exists(eachcsv)
        tmpdf = pandas.read_csv(eachcsv, header=None)
        print tmpdf.head(1)
        print tmpdf.columns
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
    print set(txndf.buysell)
    assert set(txndf.buysell) == set(['S','B'])
    print txndf.head(1)
    print len(txndf.index)
    print len(txndf.trdno)
    print len(txndf.trdno.unique())
    return txndf

def calc_per_share_values(txndf):
    txndf['trddatetime'] = txndf.apply(lambda r: datetime.datetime.strptime(r.ix['trddate']+r.ix['trdtime'], "%d-%b-%y%H:%M:%S"), axis=1)
    txndf['price'] = txndf.apply(lambda r: -1*r.ix['price'] if 'B' == r.ix['buysell'] else r.ix['price'], axis=1)
    txndf['netamt_ps_v1'] = txndf.buysell.apply(lambda bs: -1 if 'B' == bs else 1)
    txndf['netamt_ps_v1'] = txndf.apply(lambda r: (r.ix['netamt_ps_v1']*r.ix['value']-r.ix['brokamt'])/r.ix['qty'], axis=1)
    txndf['netamt_ps_v2'] = txndf.apply(lambda r: r.ix['netamt']/r.ix['qty'], axis=1)
    txndf['netamt_ps_v1'] = txndf.netamt_ps_v1.apply(lambda v: round(v,2))
    txndf['netamt_ps_v2'] = txndf.netamt_ps_v2.apply(lambda v: round(v,2))
    buy_txndf = txndf[txndf.buysell=='B']
    print buy_txndf[['trddatetime','buysell','qty','price','value','brokamt','netamt_ps_v1','netamt_ps_v2']].head(5)
    sell_txndf = txndf[txndf.buysell=='S']
    print sell_txndf[['trddatetime','buysell','qty','price','value','brokamt','netamt_ps_v1','netamt_ps_v2']].head(5)

def match_buys_for_sells(txndf):
    gains_records = []
    sell_txndf = txndf[txndf.buysell=='S']
    buy_txndf = txndf[txndf.buysell=='B']
    sell_txndf = sell_txndf.sort('trddatetime')
    buy_txndf = buy_txndf.sort('trddatetime')
    for sell_irow, sell_txn in  sell_txndf.iterrows():
        print "Sell:", sell_txn.trddatetime, sell_txn.scrip, sell_txn.qty, sell_txn.price, sell_txn.netamt_ps_v1, sell_txn.netamt_ps_v2
        for buy_irow, buy_txn in buy_txndf.iterrows():
            if buy_txn.scrip != sell_txn.scrip:
                continue
            if sell_txn.qty > 0 and buy_txn.qty > 0:
                print buy_irow, sell_irow, buy_txn.scrip, buy_txn.qty, sell_txn.qty
                print "Buy:", buy_txn.trddatetime, buy_txn.scrip, buy_txn.qty, buy_txn.price, buy_txn.netamt_ps_v1, buy_txn.netamt_ps_v2
                min_qty = min(buy_txn.qty, sell_txn.qty)
                gains_records.append((buy_txn.scrip, min_qty, \
                        buy_txn.price+sell_txn.price, buy_txn.netamt_ps_v1+sell_txn.netamt_ps_v1, buy_txn.netamt_ps_v2+sell_txn.netamt_ps_v2, \
                        sell_txn.trddatetime, sell_txn.price, sell_txn.netamt_ps_v1, sell_txn.netamt_ps_v2, \
                        buy_txn.trddatetime, buy_txn.price, buy_txn.netamt_ps_v1, buy_txn.netamt_ps_v2))
                # updating buy_txn.qty or sell_txn.qty does NOT effect itended record, just a local change
                buy_txndf.qty[buy_irow] -= min_qty
                sell_txndf.qty[sell_irow] -= min_qty
                buy_txn.qty -= min_qty
                sell_txn.qty -= min_qty
                print buy_irow, sell_irow, buy_txn.scrip, buy_txn.qty, sell_txn.qty
                print
    return gains_records

def main(txncsvs, outdir, logger):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print "Created `%s` output dir"%outdir
    else:
        print "Output dir `%s` already exists! Overwriting content"%outdir
    txndf = load_txtcsvs(txncsvs)
    calc_per_share_values(txndf)
    gains_records = match_buys_for_sells(txndf)
    for record in gains_records:
        print "\t".join(map(str,record))

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

