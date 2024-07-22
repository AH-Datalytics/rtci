# Load Libraries
library(tidyverse)

# Load Data
final_sample <- read_csv("data/sample_2018_present_wlinks.csv")

# Rename columns: lower case and underscores
final_sample <- final_sample %>%
    rename_with(~ str_replace_all(tolower(.), "\\.", "_"))

# Capitalize first letter of character columns, rest lowercase
final_sample <- final_sample %>%
  mutate(across(where(is.character), ~ str_to_title(.))) %>%
  mutate(across(c("agency_name", 
                  "city", 
                  "state", 
                  "state_name", 
                  "ucr_agency_name"), 
                ~ str_to_sentence(.)))

# Create 'agency_full' and 'location_full' columns
final_sample <- final_sample %>%
  mutate(agency_full = str_c(agency_name, ", ", state),
         location_full = str_c(city, ", ", state))

# Rename 'agg_assault' to 'Aggravated Assault'
final_sample <- final_sample %>%
  rename(aggravated_assault = agg_assault)

# Select and arrange columns
final_sample <- final_sample %>%
  select(date, 
         state_ucr_link,
         agency_name, 
         state_name, 
         agency_full, 
         ori_number, 
         ori_9_digit,
         location_full, 
         population, 
         murder, rape, 
         robbery, 
         aggravated_assault, 
         burglary, 
         larceny, 
         mvt, 
         arson)

# Convert to long format
final_sample_long <- final_sample %>%
  pivot_longer(cols = c(murder, 
                        rape, 
                        robbery, 
                        aggravated_assault, 
                        burglary, 
                        larceny, 
                        mvt, 
                        arson),
               names_to = "crime_type",
               values_to = "count")

# Final arrangement of columns
final_sample_long <- final_sample_long %>%
  select(date, 
         state_ucr_link, 
         agency_name, 
         state_name, 
         agency_full, 
         ori_number, 
         ori_9_digit,
         location_full, 
         population, 
         crime_type, 
         count)

# Print the first few rows of the cleaned data
head(final_sample_long)

