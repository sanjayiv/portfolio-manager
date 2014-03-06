library(shiny)
library(sqldf)

shinyServer(function(input,output) {
	#showColNames <- c("TrdDateTime", "ScripName", "BorS", "Qty", "MktPrice", "MktValue", "ExtraCost", "NetAmount", "NetAmount4Gain", "BrokAmt", "ServTax", "StampDuty", "TxnChrg", "STTonTC", "STT", "SebiTurnoverTax", "EduCess", "HighEduCess", "OtherChrg", "Product")
	showColNames <- c("TrdDateTime", "ScripName", "BorS", "Qty", "MktPrice", "MktValueSigned", "ExtraCost", "ExtraCost4Gain", "NetAmount", "NetAmount4Gain")
	sellColNames <- c("TrdDateTime", "ScripName", "BorS", "Qty", "SellMktPrice", "SellMktValue", "SellExtraCost", "SellExtraCost4Gain", "SellNetAmount", "SellNetAmount4Gain")
	gainsColNames <- c("Scrip", "Qty", "SellQty", "BuyQty", "SellDate", "SellValue", "SellNet", "BuyDate", "BuyValue", "BuyNet", "GainValue", "GainNet")
	#output$txntable <- renderTable({head(txn[,c("TrdDt","ScripName")], n=10)})
	output$txntable <- renderDataTable({globalTxn[,showColNames]})

	runtimeGain <- reactive({
		buyTxn <- globalTxn[(globalTxn$BorS=="B" | globalTxn$BorS=="b"),showColNames]
		sellTxn <- globalTxn[(globalTxn$BorS=="S" | globalTxn$BorS=="s"),showColNames]
		buyTxnSorted <- buyTxn[do.call(order,buyTxn),]
		sellTxnSorted <- sellTxn[do.call(order,sellTxn),]
		gainsData <- do.call(rbind, lapply(1:nrow(sellTxnSorted), function(row) {
			gainsRecords <- rbind()
			txn <- sellTxnSorted[row,]
			sellDate <- txn$TrdDateTime
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
					print(paste(sellScrip, minQty, sellQty, buyQty))
					gainsRecords <- rbind(gainsRecords, cbind(paste(sellScrip), minQty, sellQty, buyQty, paste(sellDate), sellMktValueSigned, round(sellNetAmount4Gain,2), paste(buyDate), buyMktValueSigned, round(buyNetAmount4Gain,2), round(minQty*(sellMktValueSigned+buyMktValueSigned),2), round(minQty*(sellNetAmount4Gain+buyNetAmount4Gain),2) ))
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
		colnames(gainsData) <- gainsColNames
		return(gainsData)
	})
	output$gainstable <- renderDataTable({runtimeGain()})

	output$gainsummarytable <- renderDataTable({runtimeGain()})
})
