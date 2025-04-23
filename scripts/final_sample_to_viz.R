# Setup ---------------------------------------------------------------------------------------
# Load Libraries
library(tidyverse)
library(lubridate)
library(datasets)
library(janitor)
library(stringr)
library(tidygeocoder)
library(sf)
library(readxl)

# Get the current date and time
last_updated <- format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")

# Load Data
final_sample <- read_csv("../data/final_sample.csv")


# add in dummy variable into id column
final_sample <- final_sample %>% 
  mutate(city_state_id = ifelse(is.na(city_state_id), 
                                "Not Provided",
                                city_state_id))

# Add in "County" into agency name and city_state for counties
final_sample <- final_sample %>%
  mutate(`Agency Name` = if_else(str_detect(city_state_id, "County"),
                                 paste0(`Agency Name`, " County"),
                                 `Agency Name`))


final_sample <- final_sample %>%
  mutate(city_state = if_else(str_detect(city_state_id, "County"),
                              str_replace(city_state, "^(.*?),", "\\1 County,"),
                              city_state))



# # Population for the aggregate ones and pop23 for individual agencies
# final_sample <- final_sample %>%
#   mutate(pop23 = ifelse(str_detect(State, "All Agencies") | str_detect(`Agency Name`, "Sample Counts"), Population, pop23)) %>%
#   select(-Population) %>%
#   mutate(Population = pop23) %>%
#   select(-pop23)


## DROP COLUMNS FROM DAVE
# # Rename only if "State" doesn't exist and "State.y" does
# if (!"State" %in% names(final_sample) && "State.x" %in% names(final_sample)) {
#   final_sample <- final_sample %>%
#     rename(State = State.x)
# }
# 
# 
# # Rename only if "Agency_Type" doesn't exist and "Agency_Type.x.y" does
# if (!"Agency_Type" %in% names(final_sample) && "Agency_Type.x.y" %in% names(final_sample)) {
#   final_sample <- final_sample %>%
#     rename(Agency_Type = Agency_Type.x.y)
# }

# Drop unwanted columns
final_sample <- final_sample %>%
  select(-c(region_name, state_abbr, pop23, pub_agency_name), -matches("\\.(x|y)$"))


# Capitalize population column 
final_sample <- final_sample %>% 
  rename(Population = population)


## Other cleaning
# final_sample <- final_sample %>% # TEMPORARY UNTIL DAVE PROVIDES ONE STATE COLUMN
#   mutate(State = ifelse(is.na(State),
#                         State_ref,
#                         State))

# Drop NA/other states still in data
# final_sample <- final_sample %>% 
#   filter(!is.na(State))


# Regional Mutation 
final_sample <- final_sample %>%
  mutate(
    # Step 1: If `Agency Name` is "Regional Sample Counts" and `State` is NA, update them
    State = if_else(`Agency Name` == "Regional Sample Counts", "Nationwide", State),
    `Agency Name` = if_else(`Agency Name` == "Regional Sample Counts", Region, `Agency Name`),
    
    # # Step : If `Agency Name` is "Regional Sample Counts", update `Agency Name`
    # `Agency Name` = if_else(`Agency Name` == "Regional Sample Counts", State, `Agency Name`),
    
    # # Step : If `State` is "Midwest", "Northeast", "South", or "West", set it to "Nationwide"
    # State = if_else(State %in% c("Midwest", "Northeast", "South", "West"), "Nationwide", State),
    
    # Step 2: If `State` is "Nationwide" and `Agency Name` is one of the regions, concatenate them; otherwise, keep `city_state` unchanged
    city_state = if_else(State == "Nationwide" & `Agency Name` %in% c("Midwest", "Northeast", "South", "West"),
                         paste(State, `Agency Name`, sep = ", "), city_state)
  )


# Define region vectors
midwest <- c("IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI")
northeast <- c("CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT")
south <- c("AL", "AR", "DE", "DC", "FL", "GA", "KY", "LA", "MD", "MS", "NC", "OK", "SC", "TN", "TX", "VA", "WV")
west <- c("AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NV", "NM", "OR", "UT", "WA", "WY")

# Assign regions based on `State` and `Agency Name`
final_sample <- final_sample %>%
  mutate(
    Region = case_when(
      is.na(State) ~ "All",  # If `State` contains "All"
      `Agency Name` %in% c("West", "Northeast", "Midwest", "South") ~ `Agency Name`,  # If `Agency Name` matches one of these regions
      State %in% midwest ~ "Midwest",  # Assign regions based on `State` abbreviations
      State %in% northeast ~ "Northeast",
      State %in% south ~ "South",
      State %in% west ~ "West",
      TRUE ~ "Other"  # Default to "Other"
    )
  )


# Deal with NA states (remove NA Full Samples, reassign MoCo, then rest must be PR)
final_sample <- final_sample %>% 
  filter(!(is.na(State) & `Agency Name` == "State Sample Counts")) %>% 
  mutate(State = ifelse(`Agency Name` == "Montgomery County" & is.na(State),
                        "MD",
                        State),
         State = ifelse(is.na(State) & is.na(Population),
                        "PR",
                        State))

# Fix Jefferson Parish
final_sample <- final_sample %>% 
  mutate(`Agency Name` = ifelse(State == "LA" & `Agency Name` == "Jefferson County",
                                "Jefferson Parish", 
                                `Agency Name`))



# Download Button Data ------------------------------------------------------------------------
final_sample_download <- final_sample 

# Light Cleaning
final_sample_download <- final_sample_download %>%
  mutate(`Last Updated` = last_updated,
         date = format(as.Date(date), "%B %Y")) %>% 
  select(!(Last.Updated | Agency)) %>% 
  rename(FBI.Population.Covered = Population,
         Number.of.Agencies = Agency_num,
         Agency_State = city_state,
         Agency = `Agency Name`,
         Date = date) %>% 
  select(Month, Year, Date, Agency, State, Region, Agency_State, Murder, Rape, Robbery, `Aggravated Assault`, Burglary, Theft, 
         `Motor Vehicle Theft`, `Violent Crime`, `Property Crime`, Murder_mvs_12mo, Burglary_mvs_12mo, 
         Rape_mvs_12mo, Robbery_mvs_12mo, `Aggravated Assault_mvs_12mo`, `Motor Vehicle Theft_mvs_12mo`, Theft_mvs_12mo, 
         `Violent Crime_mvs_12mo`, `Property Crime_mvs_12mo`, Source.Link, Source.Type, Source.Method, 
         FBI.Population.Covered, Number.of.Agencies, Latitude, Longitude, Comment, `Last Updated`)


# Pop Group Agency Naming
final_sample_download <- final_sample_download %>%
  mutate(Agency = str_replace_all(Agency,
                                  c("100k-250k" = "Agencies of 100K - 250K",
                                    "250k-1mn" = "Agencies of 250K - 1M",
                                    "1mn+" = "Agencies of 1M",
                                    "<100k" = "Agencies of < 100K")))

# Pop Group State Naming
final_sample_download <- final_sample_download %>%
  mutate(
    State = ifelse(Agency %in% c("Agencies of 100K - 250K",
                                 "Agencies of 250K - 1M",
                                "Agencies of 1M+",
                                "Agencies of < 100K"), 
                   "Nationwide", 
                   State),
  )

# Format Our National Sample 
final_sample_download <- final_sample_download %>%
  mutate(State = ifelse(Agency == "Nationwide Count", "Nationwide", State),
         Agency = ifelse(Agency == "Nationwide Count", "Full Sample", Agency),
         Agency_State = ifelse(State == "Nationwide", paste(Agency, "Nationwide", sep = ", "), Agency_State),
         Source.Link = ifelse(State == "Nationwide", "https://ah-datalytics.github.io/rtci/list/list.html", Source.Link),
         Source.Type = ifelse(State == "Nationwide", "Aggregate", Source.Type),
         Source.Method = ifelse(State == "Nationwide", "All agencies with complete data through most recent month.", Source.Method))

# Format Our State Samples 
final_sample_download <- final_sample_download %>%
  mutate(Agency_State = ifelse(Agency == "State Sample Counts", paste("Full Sample", State, sep = ", "), Agency_State),
         Source.Link = ifelse(Agency == "State Sample Counts", "https://ah-datalytics.github.io/rtci/list/list.html", Source.Link),
         Source.Type = ifelse(Agency == "State Sample Counts", "Aggregate", Source.Type),
         Source.Method = ifelse(Agency == "State Sample Counts", "All agencies in state with complete data through most recent month.", Source.Method),
         Agency = ifelse(Agency == "State Sample Counts", "Full Sample", Agency))




# Write to app_data folder for full download
write.csv(final_sample_download, "../docs/app_data/final_sample.csv", row.names = FALSE)



# Graph Data ----------------------------------------------------------------------------------

# Clean column names to make them unique
final_sample <- final_sample %>%
  clean_names()

# Keep the first "state" column and remove the other "state" column
final_sample <- final_sample %>%
  select(-agency)

# Rename column state to state_abbr
final_sample <- final_sample %>%
  rename(state_abbr = state)

# Create 'date' column formatted as 1/1/YYYY
final_sample <- final_sample %>%
  mutate(date = make_date(year = year, month = month, day = 1))

# Map state abbreviations to full state names
state_names <- data.frame(state_abbr = state.abb, state_name = state.name)

dc <- c("DC", "District of Columbia")
pr <- c("PR", "Puerto Rico")

state_names <- rbind(state_names, dc, pr)

final_sample <- final_sample %>%
  left_join(state_names, by = "state_abbr")


# Fix Nationwide Naming
final_sample <- final_sample %>% 
  mutate(agency_name = ifelse(agency_name == "Nationwide Count", "Full Sample", agency_name),
         state_name = ifelse(agency_name == "Full Sample", "Nationwide", state_name))
  
# # Pop Group Naming
# final_sample <- final_sample %>%
#   mutate(
#     agency_name = ifelse(state_abbr == "All Agencies in Grouping", paste("Cities of", agency_name), agency_name),
#     state_name = ifelse(state_abbr == "All Agencies in Grouping", "Nationwide", state_name)
#   )
# 
# # Edit Pop Group Naming Further
# final_sample <- final_sample %>%
#   mutate(agency_name = str_replace_all(agency_name, 
#                                        c("Cities of 100k-250k" = "Cities of 100K - 250K",
#                                          "Cities of 1mn+" = "Cities of 1M",
#                                          "Cities of 250k-1mn" = "Cities of 250K - 1M",
#                                          "Cities of <100k" = "Cities of < 100K")))


# Pop Group Agency Naming
final_sample <- final_sample %>%
  mutate(agency_name = str_replace_all(agency_name,
                                  c("100k-250k" = "Agencies of 100K - 250K",
                                    "250k-1mn" = "Agencies of 250K - 1M",
                                    "1mn+" = "Agencies of 1M",
                                    "<100k" = "Agencies of < 100K")))

# Pop Group State Naming
final_sample <- final_sample %>%
  mutate(
    state_name = ifelse(agency_name %in% c("Agencies of 100K - 250K",
                                           "Agencies of 250K - 1M",
                                           "Agencies of 1M+",
                                           "Agencies of < 100K"), 
                   "Nationwide", 
                   state_name),
  )


# Create 'agency_full' and 'location_full' columns
final_sample <- final_sample %>%
  mutate(agency_full = str_c(agency_name, ", ", state_name),
         location_full = str_c(agency_name, ", ", state_name),
         agency_abbr = str_c(agency_name, ", ", state_abbr))

# Select relevant columns
final_sample <- final_sample %>%
  select(date, agency_name, state_name, agency_full, agency_abbr, location_full, region,
         murder, rape, robbery, aggravated_assault, violent_crime, 
         burglary, theft, motor_vehicle_theft, property_crime,
         murder_mvs_12mo, rape_mvs_12mo, robbery_mvs_12mo, aggravated_assault_mvs_12mo, violent_crime_mvs_12mo,
         burglary_mvs_12mo, theft_mvs_12mo, motor_vehicle_theft_mvs_12mo, property_crime_mvs_12mo, 
         population, 
         # population_grouping, 
         source_link, agency_num, source_type, source_method)


# Fix Regions columns
final_sample <- final_sample %>%
  mutate(
    # If `agency_name` is "Midwest", "Northeast", "South", "West", or "Other" and `state_name` is NA, set `state_name` to "Nationwide"
    state_name = if_else(agency_name %in% c("Midwest", "Northeast", "South", "West", "Other") & is.na(state_name), 
                         "Nationwide", state_name),
    
    # Concatenate `agency_name` and `state_name` for `agency_full`
    agency_full = if_else(agency_name %in% c("Midwest", "Northeast", "South", "West", "Other") & state_name == "Nationwide",
                          paste(agency_name, state_name, sep = ", "), agency_full),
    
    # Concatenate `agency_name` and `state_name` for `location_full`
    location_full = if_else(agency_name %in% c("Midwest", "Northeast", "South", "West", "Other") & state_name == "Nationwide",
                            paste(agency_name, state_name, sep = ", "), location_full)
  )



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
  left_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "region", "crime_type",
                                          "population",
                                          # "population_grouping",
                                          "source_link", "agency_num"))

# Audit merge
final_sample_left <- final_sample_long_counts %>%
  left_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "region", "crime_type",
                                          "population",
                                          # "population_grouping",
                                          "source_link", "agency_num"))

final_sample_inner <- final_sample_long_counts %>%
  inner_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "region", "crime_type",
                                           "population", 
                                           # "population_grouping", 
                                           "source_link", "agency_num"))

final_sample_full <- final_sample_long_counts %>%
  full_join(final_sample_long_mvs, by = c("date", "agency_name", "state_name", "agency_full", "agency_abbr", "location_full", "region", "crime_type",
                                          "population", 
                                          # "population_grouping", 
                                          "source_link", "agency_num"))



# Rename state_ucr_link
final_sample_long <- final_sample_long %>%
  rename(state_ucr_link = source_link,
         number_of_agencies = agency_num)

# Final arrangement of columns
final_sample_long <- final_sample_long %>%
  select(date, state_ucr_link, agency_name, state_name, agency_full, agency_abbr, location_full, region, population, crime_type, count, mvs_12mo,
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
  mutate(
    agency_abbr = ifelse(
      str_detect(agency_name, "State Sample Counts"), 
      str_replace(agency_abbr, "State Sample Counts", "Full Sample"), 
      agency_abbr
    ),
    agency_full = ifelse(
      str_detect(agency_name, "State Sample Counts"), 
      str_replace(agency_full, "State Sample Counts", "Full Sample"), 
      agency_full
    ),
    agency_name = ifelse(
      str_detect(agency_name, "State Sample Counts"), 
      "Full Sample", 
      agency_name
    )
  )



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
final_sample_long$state_ucr_link[final_sample_long$state_name == "Nationwide" | 
                                   final_sample_long$agency_name == "Full Sample"] <- "https://ah-datalytics.github.io/rtci/list/list.html"


## Post Launch -- include state samples
full_states <- final_sample_long %>%
  filter((agency_name == "Full Sample" & state_name != "Nationwide"))

# final_sample_long <- final_sample_long %>%
#   filter(!(agency_name == "Full Sample" & state_name != "Nationwide"))


# Fix Agency Abbr Column for Tooltip
final_sample_long$agency_abbr <- ifelse(
  final_sample_long$state_name == "Nationwide",
  final_sample_long$agency_full,
  final_sample_long$agency_abbr
)

# Add the "Last Updated" column to final_sample_long
final_sample_long <- final_sample_long %>%
  mutate(`Last Updated` = last_updated)

# Print the first few rows of the cleaned data with all columns
print(head(final_sample_long), width = Inf)


# REMOVE PR FROM GRAPH 
# final_sample_long <- final_sample_long %>% 
#   filter(state_name != "Puerto Rico")

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

# # Fix State Full Sample Agency Naming
# sources <- sources %>% 
#   mutate(agency_name = ifelse(str_detect(agency_name, "Full Sample"), "Full Sample", agency_name))
# 

# Remove Full Sample agencies for states where there is just one agency
# 
# # Step 1: Identify states (excluding "Nationwide") where there are exactly two agencies, one of which is "Full Sample"
# sources_with_full_sample <- sources %>%
#   filter(state_name != "Nationwide") %>%
#   group_by(state_name) %>%
#   filter(n_distinct(agency_name) == 2 & "Full Sample" %in% agency_name) %>%
#   pull(state_name) %>%
#   unique()
# 
# # Step 2: Filter out the "Full Sample" agency for those states
# sources <- sources %>%
#   filter(!(state_name %in% sources_with_full_sample & agency_name == "Full Sample"))

## REMOVE STATE FULL SAMPLES 
sources <- sources %>%
  filter(!(agency_name == "State Sample Counts"))

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
pr <- c("PR", "Puerto Rico")

state_names <- rbind(state_names, dc, pr)

sample_cities <- sample_cities %>%
  left_join(state_names, by = "state_abbr")

# Add in counties to agency_full for merging 
sample_cities <- sample_cities %>% 
  mutate(`Agency Name` = ifelse(Agency_Type == "County",
                                paste0(`Agency Name`, " ", Agency_Type),
                                `Agency Name`))

# Fix Jefferson Parish Issue 
sample_cities <- sample_cities %>%
  mutate(`Agency Name` = if_else(
    state_name == "Louisiana" & str_detect(`Agency Name`, "County"),
    str_replace(`Agency Name`, "County", "Parish"),
    `Agency Name`
  ))

sample_cities <- sample_cities %>% 
  mutate(agency_full = paste(`Agency Name`, state_name, sep = ", "))


# Create the new column in sources
sources$in_national_sample <- sources$agency_full %in% sample_cities$agency_full

# Change values for nationwide full sample 
sources <- sources %>% 
  mutate(source_type = ifelse(agency_full == "Full Sample, Nationwide", "Aggregate", source_type),
         source_method = ifelse(agency_full == "Full Sample, Nationwide", "All agencies with complete data through most recent month.", source_method),
         source_link = ifelse(agency_full == "Full Sample, Nationwide", "https://ah-datalytics.github.io/rtci/list/list.html", source_link),
         agency_abbr = ifelse(agency_full == "Full Sample, Nationwide", "Full Sample, Nationwide", agency_abbr)
         ) 

# Remove Pop Grouping & Region Agencies for Nationwide
sources <- sources %>% 
  filter(!(state_name == "Nationwide" & agency_name != "Full Sample"))

# Add the "Last Updated" column to sources
sources <- sources %>%
  mutate(`Last Updated` = last_updated)

write.csv(sources, "../docs/app_data/sources.csv", row.names = FALSE)


# Make New Data for Full Sample Table Page ----------------------------------------------------------------

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
    summarise(YTD = sum(count, na.rm = FALSE))
  
  prev_ytd_data <- data %>%
    filter(agency_full == agency,
           year(date) == (most_recent_year - 1),
           month(date) <= most_recent_month) %>%
    group_by(crime_type) %>%
    summarise(PrevYTD = sum(count, na.rm = FALSE))
  
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
  mutate(Percent_Change = ifelse(Percent_Change == "Inf", "Undefined", Percent_Change))

# Audit 
na_percents <- final_dataset %>% filter(is.na(Percent_Change) | Percent_Change == "Undefined" | is.na(YTD) | is.na(PrevYTD)) 

na_kpi_agencies <- unique(na_percents$agency_full)

# Remove NAs in PrevYTD
final_dataset <- final_dataset %>%
  filter(!is.na(PrevYTD),
         !is.na(YTD),
         !is.na(Percent_Change))

# Step 7: Reformat Month Column
final_dataset <- final_dataset %>% 
  mutate(Month_Through = format(Date_Through, "%b %Y"))

# Remove State Full Samples -- commented out 
# Filter out rows where "agency_full" contains "Full Sample" unless it also contains "Nationwide"
# final_dataset <- final_dataset %>%
#   filter(!(str_detect(agency_full, "Full Sample") & !str_detect(agency_full, "Nationwide")))

# View the final dataset
print(final_dataset)

# Add the "Last Updated" column to final_dataset
final_dataset <- final_dataset %>%
  mutate(`Last Updated` = last_updated)

# Add population back in
# Extract unique agency and population pairs
agency_population <- final_sample_long %>%
  select(agency_full, population) %>%
  distinct()

# Merge population data into final_dataset
final_dataset <- final_dataset %>%
  left_join(agency_population, by = "agency_full")

final_dataset <- final_dataset %>% 
  mutate(population = ifelse(is.na(population), "Unknown", population))


# Extract number_of_agencies and ensure unique agency values:
agency_agency_count <- final_sample_long %>%
  select(agency_full, number_of_agencies) %>%
  distinct()

# Merge number_of_agencies into final_dataset:
final_dataset <- final_dataset %>%
  left_join(agency_agency_count, by = "agency_full")

final_dataset <- final_dataset %>%
  mutate(number_of_agencies = ifelse(is.na(number_of_agencies), "Unknown", number_of_agencies))


# Add in type column to then create a filter button for
final_dataset <- final_dataset %>% 
  mutate(type = case_when(
    str_detect(agency_full, "Full Sample") & !str_detect(agency_full, "Nationwide") ~ "State Samples",
    str_detect(agency_full, "Nationwide") ~ "National Samples",
    TRUE ~ "Individual Agencies"
  ))


# Remove agencies that don't have any data in the most recent year
latest_year <- year(max(final_dataset$Date_Through, na.rm = TRUE))

final_dataset <- final_dataset %>%
  filter(year(Date_Through) == latest_year)


# Write the final_sample_long data frame to viz_data.csv
write.csv(final_dataset, "../docs/app_data/full_table_data.csv", row.names = FALSE)




# Write Wide Format For All Agency Table ------------------------------------------------------
final_sample <- final_sample %>% 
  select(date,
         agency_name,
         agency_abbr,
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
  mutate(agency_name = ifelse(str_detect(agency_name, "State Sample"), "Full Sample", agency_name))


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
  mutate(month_year = paste(month(date, label = TRUE, abbr = TRUE), year(date), sep = " "))

## REMOVE STATE FULL SAMPLES 
# final_sample <- final_sample %>%
#   filter(!(agency_name == "Full Sample" & state_name != "Nationwide"))

# Correct state full sample naming
final_sample <- final_sample %>%
  mutate(agency_name = ifelse(agency_name == "State Sample Counts", "Full Sample", agency_name),
         agency_abbr = ifelse(agency_name == "Full Sample" & state_name != "Nationwide", 
                              paste(agency_name, substr(agency_abbr, nchar(agency_abbr) - 1, nchar(agency_abbr)), sep = ", "),
                              agency_abbr),
         agency_full = ifelse(agency_name == "Full Sample" & state_name != "Nationwide", 
                              paste(agency_name, state_name, sep = ", "),
                              agency_full)
         )

## Remove Full Sample agencies for states where there is just one agency
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

final_sample <- final_sample %>% 
  mutate(state_abbr = if_else(state_name == "Nationwide", 
                              "Nationwide", 
                              substr(agency_abbr, nchar(agency_abbr) - 1, nchar(agency_abbr))),
         agency_abbr = if_else(state_name == "Nationwide", 
                               agency_full,
                               agency_abbr))

# Add the "Last Updated" column to final_sample
final_sample <- final_sample %>%
  mutate(`Last Updated` = last_updated)

# REMOVE PR FROM TABLE 
# final_sample <- final_sample %>% 
#   filter(state_name != "Puerto Rico")

write.csv(final_sample, "../docs/app_data/by_agency_table.csv", row.names = FALSE)







# Scorecard Dataframe -------------------------------------------------------------------------

# Load the data from the specified path
data <- read.csv("../docs/app_data/by_agency_table.csv")

# Convert the 'date' column to Date type
data$date <- as.Date(data$date, format = "%Y-%m-%d")

# Remove any rows with NA dates
data <- data %>% filter(!is.na(date))

# Extract the year from the 'date' column
data <- data %>% mutate(year = year(date))

# Reshape the data from wide to long format to handle each crime type
data_long <- data %>%
  pivot_longer(
    cols = c(aggravated_assault, burglary, motor_vehicle_theft, murder, rape, robbery, theft, violent_crime, property_crime),
    names_to = "crime_type",
    values_to = "count"
  )

# Calculate the most recent year for each agency
most_recent_year_data <- data_long %>%
  group_by(agency_name) %>%
  summarise(
    most_recent_year = max(year, na.rm = TRUE)
  )

# Get the current maximum year across all agencies
max_year <- max(most_recent_year_data$most_recent_year, na.rm = TRUE)

# Filter to include only agencies with data in the max year (most recent year)
agencies_with_current_year_data <- most_recent_year_data %>%
  filter(most_recent_year == max_year) %>%
  pull(agency_name)

# Filter data_long to include only rows from agencies with data in the most recent year
data_long <- data_long %>%
  filter(agency_name %in% agencies_with_current_year_data)

# Calculate the most recent month in the most recent year for each agency
most_recent_month_data <- data_long %>%
  filter(year == max_year) %>%
  group_by(agency_name) %>%
  summarise(
    most_recent_month = max(month(date), na.rm = TRUE),
    most_recent_year = unique(year)
  ) %>%
  mutate(
    most_recent_month_name = month.abb[most_recent_month],
    ytd_month_range = paste0("Jan", " ", "-", " ", most_recent_month_name, " ",  most_recent_year)  # Include only months in the range
  )

# Join `most_recent_month_data` with `data_long` to include `ytd_month_range`
data_filtered <- data_long %>%
  inner_join(most_recent_month_data, by = "agency_name") %>%
  filter((year < most_recent_year) |
           (year == most_recent_year & month(date) <= most_recent_month))

# Define the years of interest based on the latest available year in the dataset
current_year <- max(data$year, na.rm = TRUE)
previous_year <- current_year - 1
two_years_prior <- current_year - 2

# Summarize full-year and YTD data for each crime type and agency, including most recent month info
summary_data <- data_filtered %>%
  filter(year %in% c(two_years_prior, previous_year, current_year)) %>%
  group_by(agency_name, state_name, crime_type, year) %>%
  summarise(
    full_year_total = sum(count, na.rm = TRUE),
    ytd_total = sum(count[month(date) <= most_recent_month], na.rm = TRUE)
  ) %>%
  ungroup() %>%
  pivot_wider(
    names_from = year,
    values_from = c(full_year_total, ytd_total),
    names_glue = "{.value}_{year}"
  ) %>%
  left_join(most_recent_month_data %>% select(agency_name, most_recent_month_name, ytd_month_range), by = "agency_name")

# Calculate percent changes with updated column names using `get(paste0(...))`
summary_data <- summary_data %>%
  mutate(
    two_years_prior_previous_year_full_pct_change = (get(paste0("full_year_total_", previous_year)) - get(paste0("full_year_total_", two_years_prior))) / get(paste0("full_year_total_", two_years_prior)) * 100,
    two_years_prior_current_year_ytd_pct_change = (get(paste0("ytd_total_", current_year)) - get(paste0("ytd_total_", two_years_prior))) / get(paste0("ytd_total_", two_years_prior)) * 100,
    previous_year_current_year_ytd_pct_change = (get(paste0("ytd_total_", current_year)) - get(paste0("ytd_total_", previous_year))) / get(paste0("ytd_total_", previous_year)) * 100
  ) %>%
  select(
    agency_name, state_name, crime_type, ytd_month_range,
    paste0("full_year_total_", two_years_prior), paste0("full_year_total_", previous_year), 
    two_years_prior_previous_year_full_pct_change,
    paste0("ytd_total_", two_years_prior), paste0("ytd_total_", previous_year), paste0("ytd_total_", current_year), 
    two_years_prior_current_year_ytd_pct_change, previous_year_current_year_ytd_pct_change
  ) %>%
  rename_with(~ c(
    "agency_name", "state_name", "crime_type", "ytd_month_range",
    "two_years_prior_full", "previous_year_full",
    "two_years_prior_previous_year_full_pct_change",
    "two_years_prior_ytd", "previous_year_ytd", "current_year_ytd",
    "two_years_prior_current_year_ytd_pct_change", "previous_year_current_year_ytd_pct_change"
  ))

# summary_data <- summary_data %>% 
#   mutate(state_name = ifelse(is.na(state_name), "Puerto Rico", state_name))

viz_data <- read_csv("../docs/app_data/viz_data.csv")

# Preprocess viz_data to keep only relevant columns and ensure distinct rows
viz_data_processed <- viz_data %>%
  select(agency_name, state_name, population, number_of_agencies) %>%
  distinct()

summary_data <-  summary_data %>%
  left_join(
    viz_data_processed,
    by = c("agency_name", "state_name") # Join on agency_name and state_name
  ) %>%
  mutate(last_updated = last_updated)


# Save the final dataset
write.csv(summary_data, "../docs/app_data/scorecard.csv", row.names = FALSE)





# Map data ------------------------------------------------------------------------------------

map <- read_csv("../docs/app_data/viz_data.csv")

agency_addresses <- read_excel("../docs/app_data/agency_addresses.xlsx")

# Generate a unique list of cities
unique_cities <- map %>%
  select(agency_name, state_name) %>%  # Select city and state columns
  distinct()                           # Remove duplicates

# Remove full sample agencies and nationwide states
unique_cities <- unique_cities %>% 
  filter(state_name != "Nationwide", agency_name != "Full Sample")

# Add County Flag
unique_cities <- unique_cities %>%
  mutate(is_county = str_detect(agency_name, "County$"))

# Create Location Column
unique_cities <- unique_cities %>%
  mutate(address = if_else(
    is_county,
    paste0(agency_name, ", ", state_name),  # Keep as "__ County, State"
    paste0(agency_name, ", ", state_name)   # Same for city, but you can adjust if needed
  ))

# Geocode each unique city using OpenStreetMap
# unique_cities_coords <- unique_cities %>%
#   geocode(city = agency_name, state = state_name, method = 'osm')

unique_cities_coords <- unique_cities %>%
  geocode(address = address, method = 'osm')


write.csv(unique_cities_coords, "../docs/app_data/unique_cities_coords.csv", row.names = FALSE)

unique_cities_coords <- read_csv("../docs/app_data/unique_cities_coords.csv")


# Rename columns in sample_cities to match those in unique_cities_coords and map
sample_cities <- sample_cities %>%
  rename(agency_name = `Agency Name`, state_name = `state_name`) %>%
  mutate(national_sample = TRUE) %>%  # Add a column to indicate national sample
  select(agency_name, state_name, national_sample)


ref_data <- read_csv("../docs/app_data/sources.csv")

# Perform a left join to add the source_type and source_method columns
map <- map %>%
  left_join(
    ref_data %>% select(agency_full, source_type, source_method),
    by = "agency_full" # Match on "agency_full"
  )


# Add back population data and national sample status
unique_cities_coords <- unique_cities_coords %>%
  left_join(map %>% select(agency_name, state_name, population, source_type, source_method, state_ucr_link), 
            by = c("agency_name", "state_name")) %>%
  left_join(sample_cities, by = c("agency_name", "state_name")) %>%
  mutate(national_sample = if_else(is.na(national_sample), FALSE, national_sample)) %>% # Set FALSE if NA
  distinct()  # Keep only unique rows


# Save the results to a CSV
write.csv(unique_cities_coords, "../docs/app_data/cities_coordinates.csv", row.names = FALSE)

# Load your RTCI cities data to extract unique states
rtci_data <- read.csv("../docs/app_data/cities_coordinates.csv")  # Update path as necessary
rtci_states <- unique(rtci_data$state_name)  # Extract unique states

# Load the U.S. states GeoJSON file
us_states <- st_read("../docs/app_data/us-states.json")  # Update path to your GeoJSON file



## Region shapefiles ----

# Define full region mappings (even if a state isn't in RTCI)
region_mapping <- list(
  Northeast = c("Connecticut", "Maine", "Massachusetts", "New Hampshire", "New Jersey", "New York", "Pennsylvania", "Rhode Island", "Vermont"),
  Midwest = c("Illinois", "Indiana", "Iowa", "Kansas", "Michigan", "Minnesota", "Missouri", "Nebraska", "North Dakota", "Ohio", "South Dakota", "Wisconsin"),
  South = c("Alabama", "Arkansas", "Delaware", "District of Columbia", "Florida", "Georgia", "Kentucky", "Louisiana", "Maryland", "Mississippi", "North Carolina", "Oklahoma", "South Carolina", "Tennessee", "Texas", "Virginia", "West Virginia"),
  West = c("Alaska", "Arizona", "California", "Colorado", "Hawaii", "Idaho", "Montana", "Nevada", "New Mexico", "Oregon", "Utah", "Washington", "Wyoming")
)

# Ensure each region contains all its states, not just RTCI states
for (region in names(region_mapping)) {
  region_states <- us_states %>%
    filter(name %in% region_mapping[[region]])  # Select ALL states for the region
  
  # Save the full region shapefiles
  st_write(region_states, paste0("../docs/app_data/", tolower(region), "_states.json"), driver = "GeoJSON", delete_dsn = TRUE)
}


## RTCI states/countries ----
# Filter the GeoDataFrame to include only states in the RTCI project
rtci_states_gdf <- us_states %>% filter(name %in% rtci_states)

# Filter to get only the states NOT in the RTCI project
non_rtci_states_gdf <- us_states %>% filter(!(name %in% rtci_states))

# Save the filtered GeoDataFrame as a new GeoJSON file for non-RTCI states
st_write(non_rtci_states_gdf, "../docs/app_data/non_rtci_states.json", driver = "GeoJSON")
st_write(rtci_states_gdf, "../docs/app_data/rtci_states.json", driver = "GeoJSON")


# Load the world countries GeoJSON file
world_countries <- st_read("../docs/app_data/countries.geo.json")  # Update path to your downloaded GeoJSON

# Filter to get only the countries NOT in the RTCI project
non_rtci_countries <- world_countries %>% filter(!(name %in% c("United States of America", "Puerto Rico")))

# Save the filtered GeoDataFrame as a new GeoJSON file for non-RTCI countries
st_write(non_rtci_countries, "../docs/app_data/non_rtci_countries.geo.json", driver = "GeoJSON")


