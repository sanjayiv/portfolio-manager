require(shiny)

shinyUI(pageWithSidebar(
	headerPanel("Personal Portfolio Manager"),
	sidebarPanel(
		numericInput("obs", "Number of observations to view:", 10),
		selectInput("whichfy", "FY: ", c('FY13'=as.Date('2014-03-31'), 'FY14'=as.Date('2015-03-31'), 'FY15'=as.Date('2016-03-31')))
	),
	mainPanel(
		tabsetPanel(
			tabPanel("Transactions", dataTableOutput("txntable")),
			tabPanel("Capital Gains (Simple)", 
				downloadButton('downloadSimpleGains', 'Download'),
				tags$hr(),
				dataTableOutput("gainsimpletable")
			),
			tabPanel("Capital Gains (Summary)", 
				downloadButton('downloadGainsSummary', 'Download'),
				tags$hr(),
				dataTableOutput("gainsummarytable")
			),
			tabPanel("Capital Gains (Detailed)", 
				downloadButton('downloadDetailedGains', 'Download'),
				tags$hr(),
				dataTableOutput("gainstable")
			)
		)
	)
))
