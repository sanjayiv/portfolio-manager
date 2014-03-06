require(shiny)

shinyUI(pageWithSidebar(
	headerPanel("Personal Portfolio Manager"),
	sidebarPanel(
		numericInput("obs", "Number of observations to view:", 10),
		sliderInput("sobs", "Number of observations to view: ", min=1, max=nrow(globalTxn), value=10)
	),
	mainPanel(
		h3("Hello World!"),
		tabsetPanel(
			tabPanel("Transactions", dataTableOutput("txntable")),
			tabPanel("Capital Gains (Detailed)", dataTableOutput("gainstable")),
			tabPanel("Capital Gains (Summary)", dataTableOutput("gainsummarytable"))
		)
	)
))
