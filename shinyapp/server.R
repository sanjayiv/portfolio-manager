library(shiny)
library(sqldf)

shinyServer(function(input,output) {
	sellColNames <- c("TrdDateTime", "ScripName", "BorS", "Qty", "SellMktPrice", "SellMktValue", "SellExtraCost", "SellExtraCost4Gain", "SellNetAmount", "SellNetAmount4Gain")
	output$txntable <- renderDataTable({globalTxn[,showColNames]})

	output$gainsummarytable <- renderDataTable({gainsSummary})

	output$gainstable <- renderDataTable({gainsData})

})
