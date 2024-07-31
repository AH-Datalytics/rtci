# Load Libraries
library(tidyverse)
library(lubridate)
library(datasets)

# Load Data
final_sample <- read_csv("../data/rtci_benjeff_sample.csv")

# Rename columns: lower case and underscores
final_sample <- final_sample %>%
  rename_with(~ str_replace_all(tolower(.), "\\s+", "_")) %>%
  rename(state_abbr = state)

# Create 'date' column formatted as 1/1/YYYY
final_sample <- final_sample %>%
  mutate(date = make_date(year = year, month = month, day = 1))

# Map state abbreviations to full state names
state_names <- data.frame(state_abbr = state.abb, state_name = state.name)
final_sample <- final_sample %>%
  left_join(state_names, by = "state_abbr")

# Create 'agency_full' and 'location_full' columns
final_sample <- final_sample %>%
  mutate(agency_full = str_c(agency_name, ", ", state_name),
         location_full = str_c(agency_name, ", ", state_name))

# Select relevant columns
final_sample <- final_sample %>%
  select(date, agency_name, state_name, agency_full, location_full, 
         murder, rape, robbery, aggravated_assault, burglary, theft, motor_vehicle_theft,
         murder_mvs_12mo, rape_mvs_12mo, robbery_mvs_12mo, aggravated_assault_mvs_12mo, 
         burglary_mvs_12mo, theft_mvs_12mo, motor_vehicle_theft_mvs_12mo)

# Convert crime data to long format for counts
final_sample_long_counts <- final_sample %>%
  pivot_longer(cols = c(murder, rape, robbery, aggravated_assault, burglary, theft, motor_vehicle_theft),
               names_to = "crime_type",
               values_to = "count")

# Convert mvs_12mo data to long format for mvs_12mo
final_sample_long_mvs <- final_sample %>%
  pivot_longer(cols = c(murder_mvs_12mo, rape_mvs_12mo, robbery_mvs_12mo, aggravated_assault_mvs_12mo, 
                        burglary_mvs_12mo, theft_mvs_12mo, motor_vehicle_theft_mvs_12mo),
               names_to = "crime_type_mvs_12mo",
               values_to = "mvs_12mo") %>%
  mutate(crime_type = str_replace(crime_type_mvs_12mo, "_mvs_12mo", "")) %>%
  select(-crime_type_mvs_12mo)

# Combine counts and mvs_12mo data
final_sample_long <- final_sample_long_counts %>%
  left_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "location_full", "crime_type"))

# Audit merge
final_sample_left <- final_sample_long_counts %>%
  left_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "location_full", "crime_type"))

final_sample_inner <- final_sample_long_counts %>%
  inner_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "location_full", "crime_type"))

final_sample_full <- final_sample_long_counts %>%
  full_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "location_full", "crime_type"))


# Add placeholder columns for state_ucr_link and population
final_sample_long <- final_sample_long %>%
  mutate(state_ucr_link = NA_character_,
         population = NA_character_)

# Final arrangement of columns
final_sample_long <- final_sample_long %>%
  select(date, state_ucr_link, agency_name, state_name, agency_full, location_full, population, crime_type, count, mvs_12mo)

# Capitalize crime types before printing and writing
final_sample_long <- final_sample_long %>%
  mutate(crime_type = ifelse(crime_type == "murder", "Murders", 
                     ifelse(crime_type == "rape", "Rapes", 
                     ifelse(crime_type == "robbery", "Robberies", 
                     ifelse(crime_type == "aggravated_assault", "Aggravated Assaults", 
                     ifelse(crime_type == "burglary", "Burglaries", 
                     ifelse(crime_type == "theft", "Thefts", 
                     ifelse(crime_type == "motor_vehicle_theft", "Motor Vehicle Thefts", crime_type))))))))


# Print the first few rows of the cleaned data with all columns
print(head(final_sample_long), width = Inf)

# Write the final_sample_long data frame to viz_data.csv
write.csv(final_sample_long, "../docs/app_data/viz_data.csv", row.names = FALSE)




# Make New Data for Table Page ----------------------------------------------------------------

# Step 1: Read the dataset
full_table_data <- final_sample_long

# Step 2: Determine the most recent date for each agency
most_recent_dates <- full_table_data %>%
  group_by(agency_full) %>%
  summarise(most_recent_date = max(date))

# Step 3: Function to calculate YTD and PrevYTD dynamically
calculate_ytd_data <- function(data, agency, most_recent_date) {
  most_recent_year <- year(most_recent_date)
  most_recent_month <- month(most_recent_date)
  
  ytd_data <- data %>%
    filter(agency_full == agency,
           year(date) == most_recent_year,
           month(date) <= most_recent_month) %>%
    group_by(crime_type) %>%
    summarise(YTD = sum(count, na.rm = TRUE))
  
  prev_ytd_data <- data %>%
    filter(agency_full == agency,
           year(date) == (most_recent_year - 1),
           month(date) <= most_recent_month) %>%
    group_by(crime_type) %>%
    summarise(PrevYTD = sum(count, na.rm = TRUE))
  
  combined_data <- ytd_data %>%
    left_join(prev_ytd_data, by = "crime_type") %>%
    mutate(Percent_Change = ((YTD - PrevYTD) / PrevYTD) * 100,
           Date_Through = most_recent_date) %>%
    select(crime_type, YTD, PrevYTD, Percent_Change, Date_Through)
  
  return(combined_data)
}

# Step 4: Apply the function to each agency
final_data_list <- lapply(1:nrow(most_recent_dates), function(i) {
  agency <- most_recent_dates$agency_full[i]
  most_recent_date <- most_recent_dates$most_recent_date[i]
  
  calculate_ytd_data(full_table_data, agency, most_recent_date) %>%
    mutate(agency_full = agency)
})

# Step 5: Combine the results into a final dataset
final_dataset <- bind_rows(final_data_list)

# View the final dataset
print(final_dataset)

# Write the final_sample_long data frame to viz_data.csv
write.csv(final_dataset, "../docs/app_data/full_table_data.csv", row.names = FALSE)
