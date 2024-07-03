# ui.R

# UI Definition
ui <- fluidPage(
  tags$head(
    tags$link(rel = "stylesheet", type = "text/css", href = "styles.css"),
    tags$script(src = "index.js")
  ),
  div(class = "center-div",  
      h2(class = "title", "Real-Time Crime Index")
  ),
  div(class = "full-width-div",  
      fluidRow(
        column(12, div(class = "action-button",
                       span("I want to see "),
                       div(class = "select-wrapper", 
                           selectInput("crimeType", "", choices = unique(data$`Crime Type`), multiple = TRUE, selected = default_crime_type, width = '100%')
                       ),
                       span(" for "),
                       div(class = "select-wrapper", 
                           selectInput("agencyName", "", choices = unique(data$`Agency Name`), selected = default_agency, width = '100%')
                       ),
                       span(" from "),
                       div(class = "select-wrapper", 
                           selectInput("yearFilter", "", choices = unique(data$Year), multiple = TRUE, selected = default_years, width = '100%')
                       )
        ))
      ),
      fluidRow(
        column(12, div(class = "action-button",
                       actionButton("toggleView", "View Table", class = "btn-primary")
        ))
      )
  ),
  mainPanel(
    class = "main-panel",
    uiOutput("viewOutput"),
    fluidRow(
      column(4,
             wellPanel(
               h4("Current Year-to-Date"),
               h5(textOutput("currentYTD")),
               textOutput("currentYTDLabel")
             )
      ),
      column(4,
             wellPanel(
               h4("Previous Year-to-Date"),
               h5(textOutput("previousYTD")),
               textOutput("previousYTDLabel")
             )
      ),
      column(4,
             wellPanel(
               h4("Percent Change YTD"),
               h5(textOutput("percentChangeYTD")),
               textOutput("percentChangeYTDLabel")
             )
      )
    ),
    div(class = "text-right",
        downloadButton("downloadData", "Download Table"),
        downloadButton("downloadPlot", "Download Graph"))
  )
)
