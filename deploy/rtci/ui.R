# ui.R

# UI Definition
ui <- fluidPage(
  # Include external CSS and JavaScript files
  tags$head(
    tags$link(rel = "stylesheet", type = "text/css", href = "styles.css"),
    tags$script(src = "index.js")
  ),
  
  # Title section
  div(class = "center-div",  # Centered div for the title
      h2(class = "title", "Real-Time Crime Index")  # Main title
  ),
  
  # Filter section
  div(class = "full-width-div",  # Full width div to contain the filter elements
      # Flexbox container to arrange the elements horizontally and center them
      span("I want to see "),  # Text for filter sentence
      div(class = "select-wrapper",  # Wrapper div for the crime type select input
          selectInput("crimeType", "", choices = unique(data$`Crime Type`), multiple = TRUE, selected = default_crime_type, width = '100%')
      ),
      span(" for "),  # Text for filter sentence
      div(class = "select-wrapper",  # Wrapper div for the agency name select input
          selectInput("agencyName", "", choices = unique(data$`Agency Name`), selected = default_agency, width = '100%')
      ),
      span(" from "),  # Text for filter sentence
      div(class = "select-wrapper",  # Wrapper div for the year filter select input
          selectInput("yearFilter", "", choices = unique(data$Year), multiple = TRUE, selected = default_years, width = '100%')
      )
  ),
  
  # Button section
  div(class = "filter-button-container",  # Separate container for the View Table button
      actionButton("toggleView", "View Table", class = "btn-primary")  # View Table button
  ),
  
  # Main panel section
  mainPanel(
    class = "main-panel",  # Main panel container
    uiOutput("viewOutput"),  # Dynamic UI output for either the plot or the data table
    
    # KPI boxes section
    fluidRow(
      column(4,
             wellPanel(  # Well panel for Current Year-to-Date KPI
               h4("Current Year-to-Date"),
               h5(textOutput("currentYTD")),
               textOutput("currentYTDLabel")
             )
      ),
      column(4,
             wellPanel(  # Well panel for Previous Year-to-Date KPI
               h4("Previous Year-to-Date"),
               h5(textOutput("previousYTD")),
               textOutput("previousYTDLabel")
             )
      ),
      column(4,
             wellPanel(  # Well panel for Percent Change YTD KPI
               h4("Percent Change YTD"),
               h5(textOutput("percentChangeYTD")),
               textOutput("percentChangeYTDLabel")
             )
      )
    ),
    
    # Download buttons section
    div(class = "text-right",  # Right-aligned container for download buttons
        downloadButton("downloadData", "Download Table"),  # Download Table button
        downloadButton("downloadPlot", "Download Graph")  # Download Graph button
    )
  )
)
