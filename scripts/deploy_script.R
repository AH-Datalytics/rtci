# Load necessary libraries
library(rsconnect)

# Set account information
rsconnect::setAccountInfo(name='rtci',
                          token='F2BAC8C714679F856B296C5EF531E873',
                          secret='cRljIbmZ+PjFXS2NyDSAtNgSIXefE2wLHZHouq8p')

# Deploy the RMarkdown file
rsconnect::deployApp(appDir = '~/Development/rtci/scripts/',
                     appFiles = c('shiny_app_to_deploy.Rmd', '../data/final_data.csv'),
                     appPrimaryDoc = 'shiny_app_to_deploy.Rmd')
