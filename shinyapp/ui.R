require(shiny)

shinyUI(pageWithSidebar(
	headerPanel("Personal Portfolio Manager"),
	sidebarPanel(
		numericInput("obs", "Number of observations to view:", 10),
		sliderInput("sobs", "Number of observations to view: ", min=1, max=nrow(globalTxn), value=10)
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
