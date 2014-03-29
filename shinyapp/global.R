library(sqldf)

stcgTAXPct <- 0.15
showColNames <- c("TrdDateTime", "ScripName", "BorS", "Qty", "MktPrice", "MktValueSigned", "MktValueSignedPS", "ExtraCost", "ExtraCostPS", "ExtraCost4Gain", "ExtraCost4GainPS", "NetAmount", "NetAmountPS", "NetAmount4Gain", "NetAmount4GainPS")

globalTxn <- read.csv("/Users/Admin/Work/Mine/portfolio-manager/demat_txn.csv", header=F)

computeNetAmount <- function(tmpTxn){
	print("computeNetAmount: started...")
	colNames <- list("TrdDttt", "TrdNo", "OrderNo", "Exch", "SettNo", "SettType", "TrdTime", "OrderTime", "ScripName", "BorS", "Qty", "MktPrice", "MktValue", "SqupDel", "BrokAmt", "ServTax", "StampDuty", "TxnChrg", "STTonTC", "STT", "SebiTurnoverTax", "EduCess", "HighEduCess", "OtherChrg", "NetAmt", "Product", "SIPFlag", "SIPRefNo")
	colnames(tmpTxn) <- colNames
	#Select only rows which are buy/sell record
	tmpTxn <- tmpTxn[(tmpTxn$BorS=="B" | tmpTxn$BorS=="b" | tmpTxn$BorS=="S" | tmpTxn$BorS=="s"),]
	tmpTxn$TrdDateTime <- as.POSIXct( paste(tmpTxn$TrdDttt, tmpTxn$TrdTime), format="%d-%b-%y %H:%M:%S")
	tmpTxn$MktValueSigned <- ifelse(tmpTxn$BorS=="B" | tmpTxn$BorS=="b", -1, 1)*tmpTxn$MktValue
	tmpTxn$MktValueSignedPS <- ifelse(tmpTxn$BorS=="B" | tmpTxn$BorS=="b", -1, 1)*tmpTxn$MktPrice
	tmpTxn$ExtraCost <- tmpTxn$BrokAmt + tmpTxn$ServTax + tmpTxn$StampDuty + tmpTxn$TxnChrg + tmpTxn$STTonTC + tmpTxn$STT + tmpTxn$SebiTurnoverTax + tmpTxn$EduCess + tmpTxn$HighEduCess + tmpTxn$OtherChrg
	#tmpTxn$ExtraCost4Gain <- tmpTxn$BrokAmt + tmpTxn$ServTax + tmpTxn$StampDuty + tmpTxn$TxnChrg + tmpTxn$OtherChrg
	# count out only Brokerage cost for Capital Gains
	tmpTxn$ExtraCost4Gain <- tmpTxn$BrokAmt
	tmpTxn$NetAmount <- tmpTxn$MktValueSigned-tmpTxn$ExtraCost
	tmpTxn$NetAmount4Gain <- tmpTxn$MktValueSigned-tmpTxn$ExtraCost4Gain
	#convert to per share
	tmpTxn$ExtraCostPS <- tmpTxn$ExtraCost / tmpTxn$Qty
	tmpTxn$NetAmountPS <- tmpTxn$NetAmount / tmpTxn$Qty
	tmpTxn$ExtraCost4GainPS <- tmpTxn$ExtraCost4Gain / tmpTxn$Qty
	tmpTxn$NetAmount4GainPS <- tmpTxn$NetAmount4Gain / tmpTxn$Qty
	print("computeNetAmount: finished")
	return(tmpTxn)
}
globalTxn <- computeNetAmount(globalTxn)

computeGains <- function(allTxn){
	print("computeGains: started...")
	buyTxn <- allTxn[(allTxn$BorS=="B" | allTxn$BorS=="b"),showColNames]
	sellTxn <- allTxn[(allTxn$BorS=="S" | allTxn$BorS=="s"),showColNames]
	buyTxnSorted <- buyTxn[do.call(order,buyTxn),]
	sellTxnSorted <- sellTxn[do.call(order,sellTxn),]
	gainsData <- do.call(rbind, lapply(1:nrow(sellTxnSorted), function(row) {
		gainsRecords <- rbind()
		txn <- sellTxnSorted[row,]
		sellDate <- txn$TrdDateTime
		yearAgoDate <- as.Date(paste(as.numeric(format(sellDate,"%Y"))-1,"-",format(sellDate,"%m"),"-",format(sellDate,"%d"),sep=""))
		numDaysInYear <- as.numeric(difftime(sellDate,yearAgoDate,units="days"))
		sellScrip <- txn$ScripName
		sellQty <- txn$Qty
		sellMktValueSignedPS <- txn$MktValueSignedPS
		sellNetAmountPS <- txn$NetAmountPS
		sellNetAmount4GainPS <- txn$NetAmount4GainPS
		print(paste("Finding respective buy for sell of ", sellQty, " stocks of ", sellScrip))
		#
		for(ii in 1:nrow(buyTxnSorted)) {
			tmpBuyRow <- buyTxnSorted[ii,]
			if(tmpBuyRow$ScripName==sellScrip && buyTxnSorted[ii,"Qty"]>0) {
				print(paste("Using ", ii, " for scrip ", sellScrip, " with qty ", buyTxnSorted[ii,"Qty"]))
				buyDate <- tmpBuyRow$TrdDateTime
				buyScrip <- tmpBuyRow$ScripName
				buyQty <- tmpBuyRow$Qty
				buyMktValueSignedPS <- tmpBuyRow$MktValueSignedPS
				buyNetAmountPS <- tmpBuyRow$NetAmountPS
				buyNetAmount4GainPS <- tmpBuyRow$NetAmount4GainPS
				minQty <- min(sellQty, buyQty)
				sellMktValueSigned <- round(minQty*sellMktValueSignedPS,2)
				buyMktValueSigned <- round(minQty*buyMktValueSignedPS,2)
				#gainValue <- round(minQty*(sellMktValueSignedPS+buyMktValueSignedPS),2)
				gainValue <- round(sellMktValueSigned+buyMktValueSigned,2)
				sellNet <- round(minQty*sellNetAmount4GainPS,2)
				buyNet <- round(minQty*buyNetAmount4GainPS,2)
				#gainNet <- round(minQty*(sellNetAmount4GainPS+buyNetAmount4GainPS),2)
				gainNet <- round(sellNet+buyNet,2)
				pctReturn <- round(-100*gainNet/(minQty*buyMktValueSignedPS),2)
				numDaysOfHold <- as.numeric(difftime(sellDate,buyDate,units="days"))
				pctReturnA <- round(pctReturn*numDaysInYear/numDaysOfHold,2)
				isSTCG <- ifelse(as.Date(buyDate)>yearAgoDate,"STCG","LTCG")
				stcgTAX <- round(ifelse(as.Date(buyDate)>yearAgoDate,gainNet*stcgTAXPct,0),2)
				#
				gainsRecords <- rbind(gainsRecords, cbind(paste(sellScrip), minQty, sellQty, buyQty, paste(sellDate), sellMktValueSignedPS, sellMktValueSigned, round(sellNetAmount4GainPS,2), sellNet, paste(buyDate), buyMktValueSignedPS, buyMktValueSigned, round(buyNetAmount4GainPS,2), buyNet, gainValue, gainNet, pctReturn, pctReturnA, isSTCG, stcgTAX))
				#gainsRecords <- rbind(gainsRecords, cbind(paste(sellScrip), minQty, sellQty, buyQty, paste(sellDate), sellMktValueSignedPS, sellMktValueSigned, sellNetAmount4GainPS, sellNet, paste(buyDate), buyMktValueSignedPS, buyMktValueSigned, buyNetAmount4GainPS, buyNet, gainValue, gainNet, pctReturn, pctReturnA, isSTCG, stcgTAX))
				sellQty <- sellQty-minQty
				buyTxnSorted[ii,"Qty"] <<- (buyQty-minQty)
				print(paste("Setting qty to ", (buyQty-minQty), " for ii ", ii))
			}
			if(sellQty==0) {
				break
			}
		}
		return(gainsRecords)
	}))
	gainsColNames <- c("Scrip", "Qty", "SellQty", "BuyQty", "SellDate", "SellValuePS", "SellValue", "SellNetPS", "SellNet", "BuyDate", "BuyValuePS", "BuyValue", "BuyNetPS", "BuyNet", "GainValue", "GainNet", "PctReturn", "PctReturnAnnualized", "isSTCG", "stcgTAX")
	colnames(gainsData) <- gainsColNames
	print("computeGains: finished")
	return(gainsData)
}
gainsData <- data.frame(computeGains(globalTxn))

summarizeGains <- function(gainsData) {
	print("summarizeGains: running query...")
	gainsSummary <- sqldf("select Scrip, sum(Qty) as Qty, date(SellDate) as SellDate, sum(SellNet) as SellNet, date(BuyDate) as BuyDate, sum(BuyNet) as BuyNet, sum(GainNet) as GainNet, sum(stcgTAX) as stcgTAX, sum(SellValue) as SellValue, sum(BuyValue) as BuyValue, sum(GainValue) as GainValue from gainsData group by Scrip, SellDate, BuyDate order by SellDate, Scrip")
	return(gainsSummary)
}
gainsSummary <- summarizeGains(gainsData)

simplifyGains <- function(gainsSummary) {
	print("simplifyGains: running query...")
	simpleGains <- sqldf("select Scrip, sum(Qty) as Qty, sum(SellNet) as SellNet, sum(BuyNet) as BuyNet, sum(GainNet) as GainNet, sum(stcgTAX) as stcgTAX, sum(SellValue) as SellValue, sum(BuyValue) as BuyValue, sum(GainValue) as GainValue from gainsSummary group by Scrip")
	return(simpleGains)
}
simpleGains <- simplifyGains(gainsSummary)
