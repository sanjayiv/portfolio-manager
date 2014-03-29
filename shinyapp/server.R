library(shiny)
library(sqldf)

shinyServer(function(input,output) {
	sellColNames <- c("TrdDateTime", "ScripName", "BorS", "Qty", "SellMktPrice", "SellMktValue", "SellExtraCost", "SellExtraCost4Gain", "SellNetAmount", "SellNetAmount4Gain")
	output$txntable <- renderDataTable({globalTxn[,showColNames]})

	output$gainsimpletable <- renderDataTable({simpleGains})

	output$gainsummarytable <- renderDataTable({gainsSummary})

	output$gainstable <- renderDataTable({gainsData})

	output$downloadSimpleGains <- downloadHandler(
		filename = function() { paste("simple_capital_gains", '.csv', sep='') },
		content = function(file) {
			write.csv(simpleGains, file)
		}
	)

	output$downloadGainsSummary <- downloadHandler(
		filename = function() { paste("capital_gains_summary", '.csv', sep='') },
		content = function(file) {
			write.csv(gainsSummary, file)
		}
	)

	output$downloadDetailedGains <- downloadHandler(
		filename = function() { paste("detailed_capital_gains", '.csv', sep='') },
		content = function(file) {
			write.csv(gainsData, file)
		}
	)
})
