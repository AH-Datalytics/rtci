# Main app file to run the Shiny application

source("global.R")
source("helpers.R")
source("ui.R")
source("server.R")

shinyApp(ui = ui, server = server)
