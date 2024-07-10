# Library Imports -----------------------------------------------------------------------------
library(shiny)
library(ggplot2)
library(dplyr)
library(plotly)
library(lubridate)
library(DT)  # For rendering interactive data tables
library(RColorBrewer)  # For generating color palettes
library(tidyverse)
library(rsconnect) # install package if needed
library(here)


# Data Loading and Transformation -------------------------------------------------------------

# Assuming data is already loaded and transformed
data <- read_csv("final_data_web_app.csv")
data$Date <- as.Date(paste0(data$Year, "-", data$Month, "-01"), format = "%Y-%m-%d")
data$Month <- floor_date(data$Date, "month")

# Default selections
default_crime_type <- "Murder"
default_agency <- sort(unique(data$`Agency Name`))[1]
default_years <- unique(data$Year)




# Helper Functions ----------------------------------------------------------------------------

# Helper function to format crime type label
format_crime_type_label <- function(crime_types) {
  if (length(crime_types) > 1) {
    paste(crime_types[-length(crime_types)], collapse = ", ", sep = "") %>%
      paste("&", crime_types[length(crime_types)], sep = " ")
  } else {
    crime_types
  }
}

# Function to add shaded background for every even-numbered year
add_shaded_background <- function(plot, data) {
  even_years <- unique(data$Year[data$Year %% 2 == 0])
  plot + 
    geom_rect(data = data.frame(xmin = as.Date(paste0(even_years, "-01-01")),
                                xmax = as.Date(paste0(even_years, "-12-31")),
                                ymin = -Inf, ymax = Inf),
              aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax),
              fill = "grey90", alpha = 0.5, inherit.aes = FALSE)
}



# UI Definition -------------------------------------------------------------------------------

# Shiny UI
ui <- fluidPage(
  tags$head(
    tags$style(HTML("
      @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&display=swap');
      body { 
        font-family: 'Roboto Condensed', sans-serif;
        background-color: #00333a;
        color: #ffffff;  # Ensure text is readable against a dark background
      }
      .shiny-output-error { color: #ffffff; }  # Error message color
      .shiny-output-error:before { content: 'Error: '; }
      .sidebar { background-color: #2d5ef9; }  # Change sidebar background color
      .main-panel { width: 100%; }
      .well { padding: 10px; }  # Reduce the padding in wellPanel for KPI boxes
      h2.title { text-align: center; font-size: 30px; font-family: 'Roboto Condensed', sans-serif; }
    "))
  ),
  div(style = "width: 100%; text-align: center; margin-top: 20px;",  # Center the title within the container
      h2(class = "title", "Real-Time Crime Index")
  ),
  div(style = "width: 100%;",  # Ensure the top panel matches the plot width
      fluidRow(
        column(12, div(style = "padding-top: 20px; font-size: 20px;",
                       span("Show me "),
                       div(style = "display: inline-block; width: 20%; position: relative;", 
                           selectInput("crimeType", "", choices = unique(data$`Crime Type`), multiple = TRUE, selected = default_crime_type, width = '100%'),
                           div(style = "border-bottom: 1px solid #ffffff; width: 100%;")
                       ),
                       span(" for "),
                       div(style = "display: inline-block; width: 20%; position: relative;", 
                           selectInput("agencyName", "", choices = unique(data$`Agency Name`), selected = default_agency, width = '100%'),
                           div(style = "border-bottom: 1px solid #ffffff; width: 100%;")
                       ),
                       span(" from "),
                       div(style = "display: inline-block; width: 20%; position: relative;", 
                           selectInput("yearFilter", "", choices = unique(data$Year), multiple = TRUE, selected = default_years, width = '100%'),
                           div(style = "border-bottom: 1px solid #ffffff; width: 100%;")
                       )
        ))
      ),
      fluidRow(
        column(12, div(style = "padding-top: 10px; text-align: left;",
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
               style = "background-color: #004953; color: #ffffff;",
               h4("Current Year-to-Date"),
               h5(textOutput("currentYTD")),
               textOutput("currentYTDLabel")
             )
      ),
      column(4,
             wellPanel(
               style = "background-color: #004953; color: #ffffff;",
               h4("Previous Year-to-Date"),
               h5(textOutput("previousYTD")),
               textOutput("previousYTDLabel")
             )
      ),
      column(4,
             wellPanel(
               style = "background-color: #004953; color: #ffffff;",
               h4("Percent Change YTD"),
               h5(textOutput("percentChangeYTD")),
               textOutput("percentChangeYTDLabel")
             )
      )
    ),
    fluidRow(
      column(6,
             wellPanel(
               style = "background-color: #004953; color: #ffffff;",
               h4(style = "margin: 0", "Source"),
               textOutput("sourceLink", inline = TRUE)
             )
      ),
      column(6, div(style = "text-align: right;",
                    downloadButton("downloadData", "Download Table"),
                    downloadButton("downloadPlot", "Download Graph"))
      )
    )
  )
)




# Server Definition ---------------------------------------------------------------------------

# Shiny Server
server <- function(input, output, session) {
  # Reactive data based on user inputs
  reactiveData <- reactive({
    data %>%
      filter(`Crime Type` %in% input$crimeType,
             `Agency Name` %in% input$agencyName,
             Year %in% input$yearFilter) %>%
      arrange(Month)
  })
  
  # Generate plot
  output$crimePlot <- renderPlotly({
    df <- reactiveData()
    colors <- brewer.pal(n = length(unique(df$`Crime Type`)), name = "Set1")
    p <- ggplot(df, aes(x = Month, y = Total_Incidents, color = `Crime Type`)) +
      geom_line() +
      geom_point() +
      scale_color_manual(values = colors) +
      scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
      scale_y_continuous(breaks = pretty(df$Total_Incidents), labels = scales::label_number(accuracy = 1)) +
      labs(x = "Year", y = paste("Count of", format_crime_type_label(unique(df$`Crime Type`)))) +
      theme_minimal() +
      theme(
        axis.text.x = element_text(size = 12, face = "bold", family = "Roboto Condensed", hjust = 0.5),
        axis.title.x = element_text(size = 14, face = "bold", family = "Roboto Condensed"),
        axis.title.y = element_text(size = 14, face = "bold", family = "Roboto Condensed"),
        legend.position = "none"  # Remove legend
      )
    
    # Add shaded background for every even-numbered year
    p <- add_shaded_background(p, df)
    
    ggplotly(p)
  })
  
  # Render the data table
  output$dataTable <- renderDT({
    datatable(reactiveData(), selection = 'single', options = list(
      pageLength = 10,
      scrollX = TRUE,
      initComplete = JS("function(settings, json) {",
                        "$(this.api().table().header()).css({'background-color': '#2d5ef9', 'color': '#ffffff'});",
                        "$('.dataTables_wrapper').find('label').each(function() {",
                        "$(this).css('color', '#ffffff');",
                        "});",
                        "$('.dataTables_wrapper').find('.dataTables_info').css('color', '#ffffff');",
                        "$('.dataTables_wrapper').find('.paginate_button').css('color', '#ffffff');",  # Styles all pagination buttons
                        "$('.dataTables_wrapper').find('table').css('color', '#ffffff');",
                        "$('.paginate_button').not('.current').hover(function() {",
                        "$(this).css('color', '#2d5ef9').css('background-color', '#ffffff');",  # Changes button color on hover
                        "}, function() {",
                        "$(this).css('color', '#ffffff').css('background-color', '');",  # Revert on mouse out
                        "});",
                        "}"),
      dom = 'Bfrtip',
      buttons = list(
        'copy', 'csv', 'excel', 'pdf', 'print'
      )
    ), callback = JS("table.draw();"))
  })
  
  # Toggle view between plot and data table
  observeEvent(input$toggleView, {
    if (input$toggleView %% 2 == 1) {
      updateActionButton(session, "toggleView", label = "View Graph")
      output$viewOutput <- renderUI({
        DTOutput("dataTable")
      })
    } else {
      updateActionButton(session, "toggleView", label = "View Table")
      output$viewOutput <- renderUI({
        plotlyOutput("crimePlot", height = "600px")
      })
    }
  })
  
  # Set initial view to plot
  output$viewOutput <- renderUI({
    plotlyOutput("crimePlot", height = "600px") #IS THIS WHERE I EDIT THE SIZING?
  })
  
  # Reactive function to get the selected row indices
  tableRows <- reactive({
    input$dataTable_rows_selected
  })
  
  # Calculate and display YTD crime data
  output$currentYTD <- renderText({
    df <- reactiveData()
    currentYTD <- df %>%
      filter(Year == max(Year)) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    text <- paste(sapply(1:nrow(currentYTD), function(i) {
      paste(currentYTD$`Crime Type`[i], "Incidents:", currentYTD$YTD[i])
    }), collapse = "\n")
    
    text
  })
  
  output$previousYTD <- renderText({
    df <- reactiveData()
    previousYTD <- df %>%
      filter(Year == max(Year) - 1) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    text <- paste(sapply(1:nrow(previousYTD), function(i) {
      paste(previousYTD$`Crime Type`[i], "Incidents:", previousYTD$YTD[i])
    }), collapse = "\n")
    
    text
  })
  
  output$percentChangeYTD <- renderText({
    df <- reactiveData()
    currentYTD <- df %>%
      filter(Year == max(Year)) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    previousYTD <- df %>%
      filter(Year == max(Year) - 1) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    percentChange <- sapply(1:nrow(currentYTD), function(i) {
      crime_type <- currentYTD$`Crime Type`[i]
      current_value <- currentYTD$YTD[i]
      previous_value <- previousYTD$YTD[previousYTD$`Crime Type` == crime_type]
      change <- if (length(previous_value) == 0) NA else ((current_value - previous_value) / previous_value) * 100
      paste(crime_type, "Percent Change:", if (is.na(change)) "N/A" else round(change, 2), "%")
    })
    
    text <- paste(percentChange, collapse = "\n")
    
    text
  })
  
  
  # Source link output
  output$sourceLink <- renderText({
    paste("www.hyperlink.com", input$agencyName)
  })
  
  # Download handlers
  output$downloadData <- downloadHandler(
    filename = function() {
      paste("Crime-Data-", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(reactiveData(), file)
    }
  )
  
  output$downloadPlot <- downloadHandler(
    filename = function() {
      paste("Crime-Graph-", Sys.Date(), ".jpeg", sep = "")
    },
    content = function(file) {
      plotly_save(plotly_last(), file)
    }
  )
}



# Run the application ---------------------------------------------------------------------

shinyApp(ui = ui, server = server)

