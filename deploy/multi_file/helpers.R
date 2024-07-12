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
