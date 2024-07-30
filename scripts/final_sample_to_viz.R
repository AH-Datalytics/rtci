# Load Libraries
library(tidyverse)
library(lubridate)
library(datasets)

# Load Data
final_sample <- read_csv("data/rtci_benjeff_sample.csv")

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
write.csv(final_sample_long, "app_data/viz_data.csv", row.names = FALSE)
