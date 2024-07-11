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
library(shinyWidgets)


# Data Loading and Transformation -------------------------------------------------------------

# Load the data
bigger_data <- read_csv("rtci_sample_extracted.csv")

# Data Cleaning: Remove rows with NA in the Agency.Name column
cleaned_data <- bigger_data %>%
  filter(!is.na(Agency.Name))

# Identify rows where the year is in the month column and the month is in the year column
incorrect_date_rows <- cleaned_data %>%
  filter(Month > 12)

# Correct the year and month for these rows
cleaned_data <- cleaned_data %>%
  mutate(
    corrected_year = if_else(Month > 12, Month, Year),
    corrected_month = if_else(Month > 12, Year, Month)
  ) %>%
  select(-Year, -Month) %>%
  rename(Year = corrected_year, Month = corrected_month)

# Fill NA values in the State column with "Not Sorted"
cleaned_data <- cleaned_data %>%
  mutate(State = if_else(is.na(State), "Not Sorted", State))

# Transform the data from wide to long format
data <- cleaned_data %>%
  pivot_longer(cols = c(Murder, Rape, Robbery, Agg.Assault, Burglary, Larceny, MVT, Arson),
               names_to = "Crime Type",
               values_to = "Total_Incidents") %>%
  mutate(Date = as.Date(paste0(Year, "-", Month, "-01"), format = "%Y-%m-%d")) %>%
  select(`Agency Name` = Agency.Name, State, Month, Year, `Crime Type`, Total_Incidents, Date)

# Default selections
default_crime_type <- "Murder"
default_state <- sort(unique(data$State))[1]
default_agency <- sort(unique(data$`Agency Name`[data$State == default_state]))[1]
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
      .main-panel { 
        width: 100%; 
      }
      .well { padding: 10px; }  # Reduce the padding in wellPanel for KPI boxes
      h2.title { text-align: center; font-size: 30px; font-family: 'Roboto Condensed', sans-serif; }
      .content-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        padding-left: 15px; /* Adjust the padding as needed */
      }
      .main-content {
        width: 100%; 
      }
      .selectize-control .selectize-input, .selectize-dropdown-content {
        font-size: 20px;  # Adjust the font size as needed
        font-family: 'Roboto Condensed', sans-serif;
      }
      .bootstrap-select .dropdown-menu li a {
        font-size: 14px;  # Adjust the font size as needed for dropdown options
        font-family: 'Roboto Condensed', sans-serif;
      }
      .bootstrap-select .dropdown-toggle .filter-option {
        font-size: 20px;  # Adjust the font size as needed for selected item text
        font-family: 'Roboto Condensed', sans-serif;
      }
    "))
  ),
  div(style = "width: 100%; text-align: center; margin-top: 20px;",  # Center the title within the container
      h2(style = "font-size: 25px;", "Monthly UCR Part One Crimes by Agency & Year")
  ),
  div(class = "content-container",
      div(style = "width: 100%;",  # Ensure the top panel matches the plot width
          fluidRow(
            column(12, div(style = "padding-top: 1px; font-size: 20px; text-align: center;",
                           span("Show me "),
                           div(style = "display: inline-block; width: 20%; position: relative; text-align: left;", 
                               pickerInput("crimeType", "", choices = unique(data$`Crime Type`), multiple = TRUE, selected = default_crime_type, width = '100%',
                                           options = list(
                                             `live-search` = TRUE,
                                             `live-search-placeholder` = "Select Crime Type"
                                           )),
                               div(style = "border-bottom: 1px solid #ffffff; width: 100%;")
                           ),
                           span(" for "),
                           div(style = "display: inline-block; width: 20%; position: relative; text-align: left;", 
                               pickerInput("agencyName", "", choices = NULL, multiple = FALSE, width = '100%',
                                           options = list(
                                             `live-search` = TRUE,
                                             `live-search-placeholder` = "Select State and Agency"
                                           )),
                               div(style = "border-bottom: 1px solid #ffffff; width: 100%;")
                           ),
                           span(" from "),
                           div(style = "display: inline-block; width: 20%; position: relative; text-align: left;", 
                               pickerInput("yearFilter", "", choices = unique(data$Year), multiple = TRUE, selected = default_years, width = '100%',
                                           options = list(
                                             `live-search` = TRUE,
                                             `live-search-placeholder` = "Select Year"
                                           )),
                               div(style = "border-bottom: 1px solid #ffffff; width: 100%;")
                           )
            ))
          )
      ),
      mainPanel(
        class = "main-panel main-content",
        fluidRow(
          column(12, div(style = "padding-top: 10px; text-align: left;",
                         actionButton("toggleView", "View Table", class = "btn-primary")
          ))
        ),
        uiOutput("viewOutput"),
        fluidRow(
          column(4,
                 wellPanel(
                   style = "background-color: #004953; color: #ffffff;",
                   uiOutput("currentYTD")
                 )
          ),
          column(4,
                 wellPanel(
                   style = "background-color: #004953; color: #ffffff;",
                   uiOutput("previousYTD")
                 )
          ),
          column(4,
                 wellPanel(
                   style = "background-color: #004953; color: #ffffff;",
                   uiOutput("percentChangeYTD")
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
)


# Server Definition ---------------------------------------------------------------------------


server <- function(input, output, session) {
  # Reactive data based on user inputs
  reactiveData <- reactive({
    data %>%
      filter(`Crime Type` %in% input$crimeType,
             `Agency Name` %in% input$agencyName,
             Year %in% input$yearFilter) %>%
      arrange(Month)
  })
  
  # Update agency list based on the selected state
  nested_choices <- reactive({
    data %>%
      group_by(State) %>%
      summarize(Agencies = list(unique(`Agency Name`))) %>%
      split(.$State) %>%
      map(~setNames(.$Agencies[[1]], .$Agencies[[1]])) %>%
      setNames(names(.))
  })
  
  observe({
    updatePickerInput(session, "agencyName", choices = nested_choices(), selected = default_agency)
  })
  
  # Helper function to format the date range
  format_date_range <- function(year, months) {
    min_month <- min(months)
    max_month <- ifelse(length(unique(months)) == 12, 12, max(months))  # Handle full years correctly
    paste0("(", month.abb[min_month], " '", substr(year, 3, 4), " - ", month.abb[max_month], " '", substr(year, 3, 4), ")")
  }
  
  # Calculate and display YTD crime data
  output$currentYTD <- renderUI({
    df <- reactiveData()
    current_year <- max(df$Year)
    current_months <- unique(month(df$Month[df$Year == current_year]))
    currentYTD <- df %>%
      filter(Year == current_year) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    date_range <- format_date_range(current_year, current_months)
    
    tagList(
      h4("Current Year-to-Date"),
      h5(date_range),
      HTML(paste(sapply(1:nrow(currentYTD), function(i) {
        paste(currentYTD$`Crime Type`[i], "Incidents:", currentYTD$YTD[i])
      }), collapse = "<br>"))
    )
  })
  
  output$previousYTD <- renderUI({
    df <- reactiveData()
    current_year <- max(df$Year)
    current_months <- unique(month(df$Month[df$Year == current_year]))
    previous_year <- current_year - 1
    previousYTD <- df %>%
      filter(Year == previous_year & month(Month) %in% current_months) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    date_range <- format_date_range(previous_year, current_months)
    
    tagList(
      h4("Previous Year-to-Date"),
      h5(date_range),
      HTML(paste(sapply(1:nrow(previousYTD), function(i) {
        paste(previousYTD$`Crime Type`[i], "Incidents:", previousYTD$YTD[i])
      }), collapse = "<br>"))
    )
  })
  
  output$percentChangeYTD <- renderUI({
    df <- reactiveData()
    current_year <- max(df$Year)
    current_months <- unique(month(df$Month[df$Year == current_year]))
    previous_year <- current_year - 1
    currentYTD <- df %>%
      filter(Year == current_year) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    previousYTD <- df %>%
      filter(Year == previous_year & month(Month) %in% current_months) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents))
    
    percentChange <- sapply(1:nrow(currentYTD), function(i) {
      crime_type <- currentYTD$`Crime Type`[i]
      current_value <- currentYTD$YTD[i]
      previous_value <- previousYTD$YTD[previousYTD$`Crime Type` == crime_type]
      change <- if (length(previous_value) == 0) NA else ((current_value - previous_value) / previous_value) * 100
      paste(crime_type, "Percent Change:", if (is.na(change)) "N/A" else round(change, 2), "%")
    })
    
    date_range <- format_date_range(current_year, current_months)
    
    tagList(
      h4("Percent Change YTD"),
      h5(date_range),
      HTML(paste(percentChange, collapse = "<br>"))
    )
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
  
  # Generate plot
  output$crimePlot <- renderPlotly({
    df <- reactiveData()
    
    # Ensure the Month column is properly transformed to Date
    df$Month <- as.Date(paste0(df$Year, "-", df$Month, "-01"), format = "%Y-%m-%d")
    
    colors <- brewer.pal(n = length(unique(df$`Crime Type`)), name = "Set1")
    
    # Calculate the y-axis limits and breaks manually
    y_max <- max(df$Total_Incidents, na.rm = TRUE)
    y_breaks <- seq(0, y_max, by = max(1, ceiling(y_max / 10))) # Adjust 'by' value as needed
    
    p <- ggplot(df, aes(x = Month, y = Total_Incidents, color = `Crime Type`)) +
      geom_line() +
      geom_point() +
      scale_color_manual(values = colors) +
      scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
      scale_y_continuous(breaks = y_breaks, labels = scales::label_number(accuracy = 1)) +
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
        plotlyOutput("crimePlot", height = "55vh")
      })
    }
  })
  
  # Set initial view to plot
  output$viewOutput <- renderUI({
    plotlyOutput("crimePlot", height = "55vh")
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
