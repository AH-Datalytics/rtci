# server.R

# Server Definition
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
    colors <- if (length(unique(df$`Crime Type`)) < 3) {
      brewer.pal(3, "Set1")[1:length(unique(df$`Crime Type`))]
    } else {
      brewer.pal(length(unique(df$`Crime Type`)), "Set1")
    }
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
    dt_data <- reactiveData()
    print(head(dt_data))  # Debug message to print data to R console
    datatable(dt_data, selection = 'single', options = list(
      pageLength = 10,
      scrollX = TRUE,
      initComplete = JS(
        "function(settings, json) {
          console.log('customizeDataTable called');
        }"
      ),
      dom = 'Bfrtip',
      buttons = list(
        'copy', 'csv', 'excel', 'pdf', 'print'
      )
    ), callback = JS("table.draw();"))
  })
  
  # server.R
  
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
        plotlyOutput("crimePlot", height = "100%")
      })
    }
  })
  
  # Set initial view to plot
  output$viewOutput <- renderUI({
    plotlyOutput("crimePlot", height = "100%")
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
      summarize(YTD = sum(Total_Incidents)) %>%
      pull(YTD)
    paste("Total Incidents: ", currentYTD)
  })
  
  output$currentYTDLabel <- renderText({
    paste("Crime Type: ", format_crime_type_label(input$crimeType))
  })
  
  output$previousYTD <- renderText({
    df <- reactiveData()
    previousYTD <- df %>%
      filter(Year == max(Year) - 1) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents)) %>%
      pull(YTD)
    paste("Total Incidents: ", previousYTD)
  })
  
  output$previousYTDLabel <- renderText({
    paste("Crime Type: ", format_crime_type_label(input$crimeType))
  })
  
  output$percentChangeYTD <- renderText({
    df <- reactiveData()
    currentYTD <- df %>%
      filter(Year == max(Year)) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents)) %>%
      pull(YTD)
    previousYTD <- df %>%
      filter(Year == max(Year) - 1) %>%
      group_by(`Crime Type`) %>%
      summarize(YTD = sum(Total_Incidents)) %>%
      pull(YTD)
    percentChange <- ((currentYTD - previousYTD) / previousYTD) * 100
    paste("Percent Change: ", round(percentChange, 2), "%")
  })
  
  output$percentChangeYTDLabel <- renderText({
    paste("Crime Type: ", format_crime_type_label(input$crimeType))
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
