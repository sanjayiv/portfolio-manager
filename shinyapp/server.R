library(shiny)
library(sqldf)

txn <- read.csv("/Users/Admin/Work/Mine/portfolio-manager/demat_txn.csv", header=T)
#txn$Date <- as.Date(txn$TrdDt, format="%d-%b-%y")
txn$NetCost <- txn$MktValue
txn$ExtraCost <- txn$BrokAmt+txn$StampDuty+txn$TxnChrg
#txn$NetCost <- sapply(txn$BorS, function(bors) { ifelse(bors=="B" | bors=="b", txn$MktValue+txn$ExtraCost, txn$MktValue-txn$ExtraCost)}) 
txn$NetMktValue <- ifelse(txn$BorS=="B" | txn$BorS=="b", txn$MktValue+txn$ExtraCost, txn$MktValue-txn$ExtraCost) 
txn$NetMktPrice <- txn$MktPrice/txn$Qty

ctxn <- sqldf("select TrdDt, ScripName, BorS, sum(Qty) as Qty, avg(MktPrice) as MktPrice, sum(MktValue) as MktValue, sum(BrokAmt) as BrokAmt, sum(StampDuty) as StampDuty, sum(TxnChrg) as TxnChrg, sum(NetMktValue) as NetMktValue from txn group by TrdDt, ScripName, BorS order by TrdDt, ScripName ")
ctxn$NetMktPrice <- ctxn$NetMktValue/ctxn$Qty

shinyServer(function(input,output) {
	#output$txntable <- renderTable({head(txn[,c("TrdDt","ScripName")], n=10)})	
	output$txntable <- renderTable({head(ctxn, n=input$obs)})
})
