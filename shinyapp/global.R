
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
