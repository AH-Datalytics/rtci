# This script identifies anomalies
# in monthly crime counts over time
# Andrew Wheeler

# These are just a few defaults I expect, I expect data in wide format per month/PD
count_fields <- c("Murder", "Rape", "Robbery", "Agg.Assault", "Burglary", "Theft","MVT")
year_field <- "Year"
month_field <- "Month"
prior_ytd <- 5 # if you have more data it averages multiple prior years for the YTD metrics

# this only searches for fewer, can also search for high by setting "greater", or both
# via "two.sided"
alt = "less"

# Rename columns
data <- cleaned_data2 %>%
  rename(
    Agg.Assault = `Aggravated Assault`,
    #Agency.Name = `Agency Name`,
    MVT = `Motor Vehicle Theft`
  )

# narrow it down further
data <- data %>% 
          select(Month, Year,
                  Murder, Agg.Assault, Rape,
                   Burglary, Robbery, MVT, Theft, city_state_id)

#drop row names
row.names(data) <- NULL

# drop NA's
data <- na.omit(data)

# This function looks at cumulative year to date stats
# so if prior total 100 YTD (averaged over prior_max years)
# and current is 20 YTD total, this would flagged
# this expects the values in per a single PD
ytd_poisson <- function(data, cf = count_fields, month = 'Month', year = 'Year', prior_max = prior_ytd, alt = 'less') {
  # Drop rows with NA in any of the specified crime fields
  data <- data %>% 
    filter(!is.na(!!sym(month)) & !is.na(!!sym(year)) & rowSums(is.na(data[cf])) == 0)
  
  # Ensure the data is sorted by year and month
  data <- data[order(data[[year]], data[[month]]),]
  
  # Get the last row of the data to determine the current year and month
  last_row <- tail(data, 1)
  last_year <- last_row[[year]]
  last_month <- last_row[[month]]
  
  # Filter data for earlier months within the same year
  early_months <- data[data[[month]] <= last_month & data[[year]] == last_year, ]
  
  # Define the formula for aggregation
  form <- paste0("cbind(", paste0(cf, collapse = ","), ") ~ ", year)
  
  # Aggregate metrics by year for the specified crime fields
  agg_metrics <- aggregate(as.formula(form), data = early_months, FUN = sum, na.action = na.pass)
  
  # Filter for the current year and prior years within the specified range
  curr_year <- tail(agg_metrics, 1)
  prior_years <- agg_metrics[agg_metrics[[year]] < last_year & agg_metrics[[year]] >= (last_year - prior_max),]
  
  # Initialize response vector
  lc <- length(cf)
  resp <- rep(NA, lc)
  
  for (i in 1:lc) {
    cnt <- cf[i]
    
    # Extract current value and sum of prior values
    curr_val <- curr_year[[cnt]]
    prior_sum <- sum(prior_years[[cnt]], na.rm = TRUE)

    # Calculate the number of valid prior observations
    prior_n <- sum(!is.na(prior_years[[cnt]]))

    # Perform Poisson test and store the p-value
    resp[i] <- poisson.test(c(curr_val, prior_sum), c(1, prior_n), alternative = alt)$p.value
  }
  
  return(resp)
}


results<- ytd_poisson(data)
# This function looks at the average of the prior k months
# so if average of prior 8 is 30, and current month is 10
# this will likely flag
# can set prior_max to 1 to just look at current vs prior month
priork_poisson <- function(data, cf = count_fields, month = 'Month', year = 'Year', prior_max = 1, alt = 'less') {
  # Drop rows with NA in any of the specified crime fields
  data <- data %>% 
    filter(!is.na(!!sym(month)) & !is.na(!!sym(year)) & rowSums(is.na(data[cf])) == 0)
  
  # Ensure the data is sorted by year and month
  data <- data[order(data[[year]], data[[month]]),]
  
  # Get the last row of the data to determine the current year and month
  last_row <- tail(data, 1)
  last_year <- last_row[[year]]
  
  # Filter for current and prior years based on prior_max
  curr_year <- tail(data, 1)
  prior_years <- data[data[[year]] < last_year & data[[year]] >= (last_year - prior_max), ]
  
  # Initialize response vector
  lc <- length(cf)
  resp <- rep(NA, lc)
  
  for (i in 1:lc) {
    cnt <- cf[i]
    
    # Extract current value and sum of prior values
    curr_val <- curr_year[[cnt]]
    prior_sum <- sum(prior_years[[cnt]], na.rm = TRUE)

    # Calculate the number of valid prior observations
    prior_n <- sum(!is.na(prior_years[[cnt]]))
    
    # Perform Poisson test and store the p-value
    resp[i] <- poisson.test(c(curr_val, prior_sum), c(1, prior_n), alternative = alt)$p.value
  }
  
  return(resp)
}


results1 <- priork_poisson(data)
# So this will loop over all PDs and return a total count column
# along with a note, if the note says
# "Burglary_ytd1 | MVT_ytd1 | Larceny_pri8"
# That means this police department was flagged for year to date burglary, year to date MVT
# and prior 8 larceny (but not prior 1 larceny)
# sorts the results, so the agencies with the most flagges are at the top of the dataframe
# Define a function to clean the data
clean_crime_data <- function(data, crime_columns) {
  # Use dplyr to filter out rows with infinite or negative values in the specified columns
  cleaned_data <- data %>%
    filter(across(all_of(crime_columns), ~ is.finite(.) & . >= 0))
  
  return(cleaned_data)
}

data <- clean_crime_data(data, count_fields)

metrics_allpd <- function(data, agency = 'city_state_id', cf = count_fields, month = 'Month', year = 'Year', flagp = 0.001) {
  # Drop rows with NA in any of the specified fields
  data <- data %>% 
    filter(!is.na(!!sym(agency)) & !is.na(!!sym(month)) & !is.na(!!sym(year)) & rowSums(is.na(data[cf])) == 0)
  
  # Ensure the data is sorted by agency, year, and month
  data <- data[order(data[[agency]], data[[year]], data[[month]]),]
  
  # Unique agencies
  pds <- unique(data[[agency]])
  df_outliers <- data.frame(pds)
  col_names <- c(paste0(cf, "_ytd1"), paste0(cf, "_pri8"), paste0(cf, "_pri1"))
  
  # Initialize columns in the output data frame
  df_outliers[, col_names] <- NA
  df_outliers$Note <- ""
  df_outliers$Total <- -1
  
  # Iterate over each agency
  for (i in seq_along(pds)) {
    local_pd <- data[data[[agency]] == pds[i],]
    
    # Calculate p-values using the poisson functions
    pvals_ytd <- ytd_poisson(local_pd, cf = cf, month = month, year = year, prior_max = 1) 
    pvals_prior8 <- priork_poisson(local_pd, cf = cf, month = month, year = year, prior_max = 8)
    pvals_prior1 <- priork_poisson(local_pd, cf = cf, month = month, year = year, prior_max = 1)
    
    # Combine p-values
    pvals_all <- c(pvals_ytd, pvals_prior8, pvals_prior1)
    
    # Create notes and calculate total flagged p-values
    note <- paste0(col_names[pvals_all < flagp], collapse = " | ")
    total <- sum(pvals_all < flagp)
    
    # Store results in the output data frame
    df_outliers[i, col_names] <- pvals_all
    df_outliers[i, 'Note'] <- note
    df_outliers[i, 'Total'] <- total
  }
  
  # Sort and return the flagged results
  df_flagged <- df_outliers[order(-df_outliers$Total),]
  row.names(df_flagged) <- seq_len(nrow(df_flagged))
  
  return(df_flagged[, c("pds", 'Total', 'Note')])
}

results3 <- metrics_allpd(data)


#write out a dataframe to review
# Specify the folder path
folder_path <- "C:\\OneDrive\\OneDrive - ahdatalytics.com\\Clients\\Real Time Crime Index\\Data Auditing and Validation"

# Create the full file path
file_path <- file.path(folder_path, "wheeler_audit_agency_review.csv")

# Write the data frame locally to jeff
write.csv(results3, file = file_path, row.names = FALSE)

# Write the data frame to the data folder in Github repo
write.csv(results3, "scripts/auditing/wheeler_audit_agency_review.csv")
