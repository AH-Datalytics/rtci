# Load Libraries
library(tidyverse)
library(lubridate)
library(datasets)
library(janitor)
library(stringr)

# Load Data
final_sample <- read_csv("../data/final_sample.csv")

# Clean column names to make them unique
final_sample <- final_sample %>%
  clean_names()

# Keep the first "state" column and remove the other "state" column
final_sample <- final_sample %>%
  select(-state_ref, -agency)

# Rename column state to state_abbr
final_sample <- final_sample %>%
  rename(state_abbr = state)

# Create 'date' column formatted as 1/1/YYYY
final_sample <- final_sample %>%
  mutate(date = make_date(year = year, month = month, day = 1))

# Map state abbreviations to full state names
state_names <- data.frame(state_abbr = state.abb, state_name = state.name)

dc <- c("DC", "District of Columbia")

state_names <- rbind(state_names, dc)

final_sample <- final_sample %>%
  left_join(state_names, by = "state_abbr")


# Fix Nationwide Naming
final_sample <- final_sample %>% 
  mutate(agency_name = ifelse(agency_name == "Nationwide Count", "Full Sample", agency_name),
         state_name = ifelse(agency_name == "Full Sample", "Nationwide", state_name))
  

# Create 'agency_full' and 'location_full' columns
final_sample <- final_sample %>%
  mutate(agency_full = str_c(agency_name, ", ", state_name),
         location_full = str_c(agency_name, ", ", state_name),
         agency_abbr = str_c(agency_name, ", ", state_abbr))

# Select relevant columns
final_sample <- final_sample %>%
  select(date, agency_name, state_name, agency_full, agency_abbr, location_full, 
         murder, rape, robbery, aggravated_assault, violent_crime, 
         burglary, theft, motor_vehicle_theft, property_crime,
         murder_mvs_12mo, rape_mvs_12mo, robbery_mvs_12mo, aggravated_assault_mvs_12mo, violent_crime_mvs_12mo,
         burglary_mvs_12mo, theft_mvs_12mo, motor_vehicle_theft_mvs_12mo, property_crime_mvs_12mo, 
         population, 
         # population_grouping, 
         source_link, agency_num, source_type, source_method)



# Convert crime data to long format for counts
final_sample_long_counts <- final_sample %>%
  pivot_longer(cols = c(murder, rape, robbery, aggravated_assault, violent_crime, 
                        burglary, theft, motor_vehicle_theft, property_crime),
               names_to = "crime_type",
               values_to = "count")

# Convert mvs_12mo data to long format for mvs_12mo
final_sample_long_mvs <- final_sample %>%
  pivot_longer(cols = c(murder_mvs_12mo, rape_mvs_12mo, robbery_mvs_12mo, aggravated_assault_mvs_12mo, violent_crime_mvs_12mo,
                        burglary_mvs_12mo, theft_mvs_12mo, motor_vehicle_theft_mvs_12mo, property_crime_mvs_12mo),
               names_to = "crime_type_mvs_12mo",
               values_to = "mvs_12mo") %>%
  mutate(crime_type = str_replace(crime_type_mvs_12mo, "_mvs_12mo", "")) %>%
  select(-crime_type_mvs_12mo)



# Combine counts and mvs_12mo data
final_sample_long <- final_sample_long_counts %>%
  left_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "crime_type",
                                          "population",
                                          # "population_grouping",
                                          "source_link", "agency_num"))

# Audit merge
final_sample_left <- final_sample_long_counts %>%
  left_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "crime_type",
                                          "population",
                                          # "population_grouping",
                                          "source_link", "agency_num"))

final_sample_inner <- final_sample_long_counts %>%
  inner_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "crime_type",
                                           "population", 
                                           # "population_grouping", 
                                           "source_link", "agency_num"))

final_sample_full <- final_sample_long_counts %>%
  full_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "crime_type",
                                          "population", 
                                          # "population_grouping", 
                                          "source_link", "agency_num"))



# Rename state_ucr_link
final_sample_long <- final_sample_long %>%
  rename(state_ucr_link = source_link,
         number_of_agencies = agency_num)

# Final arrangement of columns
final_sample_long <- final_sample_long %>%
  select(date, state_ucr_link, agency_name, state_name, agency_full, agency_abbr, location_full, population, crime_type, count, mvs_12mo,
         # population_grouping, 
         number_of_agencies)

# Capitalize crime types before printing and writing
final_sample_long <- final_sample_long %>%
  mutate(crime_type = ifelse(crime_type == "murder", "Murders", 
                             ifelse(crime_type == "rape", "Rapes", 
                                    ifelse(crime_type == "robbery", "Robberies", 
                                           ifelse(crime_type == "aggravated_assault", "Aggravated Assaults", 
                                                  ifelse(crime_type == "burglary", "Burglaries", 
                                                         ifelse(crime_type == "theft", "Thefts", 
                                                                ifelse(crime_type == "motor_vehicle_theft", "Motor Vehicle Thefts", 
                                                                       ifelse(crime_type == "violent_crime", "Violent Crimes", 
                                                                              ifelse(crime_type == "property_crime", "Property Crimes", crime_type))))))))))


# Fix State Full Sample Agency Naming
final_sample_long <- final_sample_long %>% 
  mutate(agency_name = ifelse(str_detect(agency_name, "Full Sample"), "Full Sample", agency_name))

# Fix Agency_Full Column
final_sample_long <- final_sample_long %>%
  mutate(agency_full = ifelse(str_detect(agency_full, "^[A-Z]{2}, "), 
                              str_sub(agency_full, 5, nchar(agency_full)),
                              agency_full))

# Remove Full Sample agencies for states where there is just one agency

# Step 1: Identify states (excluding "Nationwide") where there are exactly two agencies, one of which is "Full Sample"
states_with_full_sample <- final_sample_long %>%
  filter(state_name != "Nationwide") %>%
  group_by(state_name) %>%
  filter(n_distinct(agency_name) == 2 & "Full Sample" %in% agency_name) %>%
  pull(state_name) %>%
  unique()

# Step 2: Filter out the "Full Sample" agency for those states
final_sample_long <- final_sample_long %>%
  filter(!(state_name %in% states_with_full_sample & agency_name == "Full Sample"))


# Add in source for full samples (nationwide and states, eventually)
final_sample_long$state_ucr_link[final_sample_long$state_name == "Nationwide"] <- "https://realtimecrstg.wpenginepowered.com/how-does-this-work/#sources"


## PRE LAUNCH: REMOVE STATE FULL SAMPLES 
full_states <- final_sample_long %>%
  filter((agency_name == "Full Sample" & state_name != "Nationwide"))

final_sample_long <- final_sample_long %>%
  filter(!(agency_name == "Full Sample" & state_name != "Nationwide"))


# Fix Agency Abbr Column for Tooltip
final_sample_long$agency_abbr <- ifelse(
  final_sample_long$state_name == "Nationwide",
  final_sample_long$agency_full,
  final_sample_long$agency_abbr
)


# Print the first few rows of the cleaned data with all columns
print(head(final_sample_long), width = Inf)

# Write the final_sample_long data frame to viz_data.csv
write.csv(final_sample_long, "../docs/app_data/viz_data.csv", row.names = FALSE)



# Source Page Data ----------------------------------------------------------------------------
sources <- final_sample 

# Assuming your dataframe is named df and your date column is named date_column
sources$month_year <- format(as.Date(sources$date), "%B %Y")

# Select columns that do not start with any of the specified crime types
sources <- sources %>% select(-starts_with("murder"),
                              -starts_with("rape"),
                              -starts_with("robbery"),
                              -starts_with("aggravated_assault"),
                              -starts_with("violent_crime"),
                              -starts_with("burglary"),
                              -starts_with("theft"),
                              -starts_with("motor_vehicle_theft"),
                              -starts_with("property_crime"))

# Fix State Full Sample Agency Naming
sources <- sources %>% 
  mutate(agency_name = ifelse(str_detect(agency_name, "Full Sample"), "Full Sample", agency_name))


# Remove Full Sample agencies for states where there is just one agency

# Step 1: Identify states (excluding "Nationwide") where there are exactly two agencies, one of which is "Full Sample"
sources_with_full_sample <- sources %>%
  filter(state_name != "Nationwide") %>%
  group_by(state_name) %>%
  filter(n_distinct(agency_name) == 2 & "Full Sample" %in% agency_name) %>%
  pull(state_name) %>%
  unique()

# Step 2: Filter out the "Full Sample" agency for those states
sources <- sources %>%
  filter(!(state_name %in% sources_with_full_sample & agency_name == "Full Sample"))

## PRE LAUNCH: REMOVE STATE FULL SAMPLES 
sources <- sources %>%
  filter(!(agency_name == "Full Sample" & state_name != "Nationwide"))

# Group by agency_full and filter to keep only the row with the latest date
sources <- sources %>%
  group_by(agency_full) %>%
  filter(date == max(date)) %>%
  ungroup()

sources <- sources %>% 
  rename(most_recent_month = month_year)


## Create Agency Full List ----
sample_cities <- read_csv("../data/sample_cities.csv")

sample_cities <- sample_cities %>% 
  rename(state_abbr = State)

# Map state abbreviations to full state names
state_names <- data.frame(state_abbr = state.abb, state_name = state.name)

dc <- c("DC", "District of Columbia")

state_names <- rbind(state_names, dc)

sample_cities <- sample_cities %>%
  left_join(state_names, by = "state_abbr")

sample_cities <- sample_cities %>% 
  mutate(agency_full = paste(`Agency Name`, state_name, sep = ", "))


# Create the new column in sources
sources$in_national_sample <- sources$agency_full %in% sample_cities$agency_full

write.csv(sources, "../docs/app_data/sources.csv", row.names = FALSE)


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

# Step 6: Deal with NAs for % change
final_dataset <- final_dataset %>% 
  mutate(Percent_Change = ifelse((YTD == 0 & PrevYTD == 0 & is.na(Percent_Change)), 0, Percent_Change))

final_dataset <- final_dataset %>% 
  mutate(Percent_Change = ifelse(Percent_Change == "Inf", 9999, Percent_Change))

# Audit 
na_percents <- final_dataset %>% filter(is.na(Percent_Change) | Percent_Change == "Inf") 

# Remove NAs in PrevYTD
final_dataset <- final_dataset %>% 
  filter(!is.na(PrevYTD))

# Step 7: Reformat Month Column
# Assuming final_dataset has a column named Date_Through in date format
final_dataset <- final_dataset %>% 
  mutate(Month_Through = as.character(month(Date_Through, label = TRUE, abbr = FALSE)))

# Remove State Full Samples
# Filter out rows where "agency_full" contains "Full Sample" unless it also contains "Nationwide"
final_dataset <- final_dataset %>%
  filter(!(str_detect(agency_full, "Full Sample") & !str_detect(agency_full, "Nationwide")))


# View the final dataset
print(final_dataset)

# Write the final_sample_long data frame to viz_data.csv
write.csv(final_dataset, "../docs/app_data/full_table_data.csv", row.names = FALSE)




# Write Wide Format For All Agency Table ------------------------------------------------------
final_sample <- final_sample %>% 
  select(date,
         agency_name,
         state_name,
         agency_full,
         aggravated_assault,
         burglary,
         motor_vehicle_theft,
         murder,
         rape,
         robbery,
         theft,
         violent_crime,
         property_crime
         )

# Fix State Full Sample Agency Naming
final_sample <- final_sample %>% 
  mutate(agency_name = ifelse(str_detect(agency_name, "Full Sample"), "Full Sample", agency_name))


# Remove Full Sample agencies for states where there is just one agency

# Step 1: Identify states (excluding "Nationwide") where there are exactly two agencies, one of which is "Full Sample"
states_with_full_sample <- final_sample %>%
  filter(state_name != "Nationwide") %>%
  group_by(state_name) %>%
  filter(n_distinct(agency_name) == 2 & "Full Sample" %in% agency_name) %>%
  pull(state_name) %>%
  unique()

# Step 2: Filter out the "Full Sample" agency for those states
final_sample <- final_sample %>%
  filter(!(state_name %in% states_with_full_sample & agency_name == "Full Sample"))


# Month formatting
final_sample <- final_sample %>% 
  mutate(month_year = paste(month(date, label = TRUE, abbr = FALSE), year(date), sep = " "))

## PRE LAUNCH: REMOVE STATE FULL SAMPLES 
final_sample <- final_sample %>%
  filter(!(agency_name == "Full Sample" & state_name != "Nationwide"))


write.csv(final_sample, "../docs/app_data/by_agency_table.csv", row.names = FALSE)


