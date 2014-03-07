library(sqldf)

stcgTAXPct <- 0.15
showColNames <- c("TrdDateTime", "ScripName", "BorS", "Qty", "MktPrice", "MktValueSigned", "ExtraCost", "ExtraCost4Gain", "NetAmount", "NetAmount4Gain")

globalTxn <- read.csv("/Users/Admin/Work/Mine/portfolio-manager/demat_txn.csv", header=T)

computeNetAmount <- function(tmpTxn){
	colNames <- list("TrdDttt", "TrdNo", "OrderNo", "Exch", "SettNo", "SettType", "TrdTime", "OrderTime", "ScripName", "BorS", "Qty", "MktPrice", "MktValue", "SqupDel", "BrokAmt", "ServTax", "StampDuty", "TxnChrg", "STTonTC", "STT", "SebiTurnoverTax", "EduCess", "HighEduCess", "OtherChrg", "NetAmt", "Product", "SIPFlag", "SIPRefNo")
	colnames(tmpTxn) <- colNames
	tmpTxn$TrdDateTime <- as.POSIXct( paste(tmpTxn$TrdDttt, tmpTxn$TrdTime), format="%d-%b-%y %H:%M:%S")
	tmpTxn$MktValueSigned <- ifelse(tmpTxn$BorS=="B" | tmpTxn$BorS=="b", -1, 1)*tmpTxn$MktValue
	tmpTxn$ExtraCost <- tmpTxn$BrokAmt + tmpTxn$ServTax + tmpTxn$StampDuty + tmpTxn$TxnChrg + tmpTxn$STTonTC + tmpTxn$STT + tmpTxn$SebiTurnoverTax + tmpTxn$EduCess + tmpTxn$HighEduCess + tmpTxn$OtherChrg
	tmpTxn$ExtraCost4Gain <- tmpTxn$BrokAmt + tmpTxn$ServTax + tmpTxn$StampDuty + tmpTxn$TxnChrg + tmpTxn$OtherChrg
	tmpTxn$NetAmount <- tmpTxn$MktValueSigned-tmpTxn$ExtraCost
	tmpTxn$NetAmount4Gain <- tmpTxn$MktValueSigned-tmpTxn$ExtraCost4Gain
	#convert to per share
	tmpTxn$MktValueSigned <- tmpTxn$MktValueSigned / tmpTxn$Qty
	tmpTxn$ExtraCost <- tmpTxn$ExtraCost / tmpTxn$Qty
	tmpTxn$NetAmount <- tmpTxn$NetAmount / tmpTxn$Qty
	tmpTxn$ExtraCost4Gain <- tmpTxn$ExtraCost4Gain / tmpTxn$Qty
	tmpTxn$NetAmount4Gain <- tmpTxn$NetAmount4Gain / tmpTxn$Qty
	return(tmpTxn)
}
globalTxn <- computeNetAmount(globalTxn)

computeGains <- function(allTxn){
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
		sellMktValueSigned <- txn$MktValueSigned
		sellNetAmount <- txn$NetAmount
		sellNetAmount4Gain <- txn$NetAmount4Gain
		print(paste("Finding respective buy for sell of ", sellQty, " stocks of ", sellScrip))
		#
		for(ii in 1:nrow(buyTxnSorted)) {
			tmpBuyRow <- buyTxnSorted[ii,]
			if(tmpBuyRow$ScripName==sellScrip && buyTxnSorted[ii,"Qty"]>0) {
				print(paste("Using ", ii, " for scrip ", sellScrip, " with qty ", buyTxnSorted[ii,"Qty"]))
				buyDate <- tmpBuyRow$TrdDateTime
				buyScrip <- tmpBuyRow$ScripName
				buyQty <- tmpBuyRow$Qty
				buyMktValueSigned <- tmpBuyRow$MktValueSigned
				buyNetAmount <- tmpBuyRow$NetAmount
				buyNetAmount4Gain <- tmpBuyRow$NetAmount4Gain
				minQty <- min(sellQty, buyQty)
				gainValue <- round(minQty*(sellMktValueSigned+buyMktValueSigned),2)
				gainNet <- round(minQty*(sellNetAmount4Gain+buyNetAmount4Gain),2)
				pctReturn <- round(-100*gainNet/(minQty*buyMktValueSigned),2)
				numDaysOfHold <- as.numeric(difftime(sellDate,buyDate,units="days"))
				pctReturnA <- round(pctReturn*numDaysInYear/numDaysOfHold,2)
				isSTCG <- ifelse(as.Date(buyDate)>yearAgoDate,"STCG","LTCG")
				stcgTAX <- ifelse(as.Date(buyDate)>yearAgoDate,gainNet*stcgTAXPct,0)
				#
				print(paste(sellScrip, minQty, sellQty, buyQty))
				gainsRecords <- rbind(gainsRecords, cbind(paste(sellScrip), minQty, sellQty, buyQty, paste(sellDate), sellMktValueSigned, round(sellNetAmount4Gain,2), round(minQty*sellNetAmount4Gain,2), paste(buyDate), buyMktValueSigned, round(buyNetAmount4Gain,2), round(minQty*buyNetAmount4Gain,2), gainValue, gainNet, pctReturn, pctReturnA, isSTCG, stcgTAX))
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
	gainsColNames <- c("Scrip", "Qty", "SellQty", "BuyQty", "SellDate", "SellValue", "SellNetPS", "SellNet", "BuyDate", "BuyValue", "BuyNetPS", "BuyNet", "GainValue", "GainNet", "PctReturn", "PctReturnAnnualized", "isSTCG", "stcgTAX")
	colnames(gainsData) <- gainsColNames
	return(gainsData)
}
gainsData <- data.frame(computeGains(globalTxn))

summarizeGains <- function(gainsData) {
	gainsSummary <- sqldf("select Scrip, sum(Qty) as Qty, date(SellDate) as SellDate, sum(SellNet) as SellNet, date(BuyDate) as BuyDate, sum(BuyNet) as BuyNet, sum(GainNet) as GainNet, sum(stcgTAX) as stcgTAX from gainsData group by Scrip, SellDate, BuyDate order by SellDate, Scrip")
	return(gainsSummary)
}
gainsSummary <- summarizeGains(gainsData)
