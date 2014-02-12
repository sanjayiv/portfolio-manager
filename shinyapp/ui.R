require(shiny)

shinyUI(pageWithSidebar(
	headerPanel("Personal Portfolio Manager"),
	sidebarPanel(
		numericInput("obs", "Number of observations to view:", 10)
	),
	mainPanel(
		h3("Hello World!"),
		tableOutput("txntable")
	)
))
