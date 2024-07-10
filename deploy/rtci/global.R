# Library Imports -----------------------------------------------------------------------------
library(shiny)
library(ggplot2)
library(dplyr)
library(plotly)
library(lubridate)
library(DT)
library(RColorBrewer)
library(tidyverse)
library(rsconnect)
library(here)

# Data Loading and Transformation -------------------------------------------------------------
data <- read_csv("final_data_copy.csv")
data$Date <- as.Date(paste0(data$Year, "-", data$Month, "-01"), format = "%Y-%m-%d")
data$Month <- floor_date(data$Date, "month")

# Default selections
default_crime_type <- "Murder"
default_agency <- sort(unique(data$`Agency Name`))[1]
default_years <- unique(data$Year)
