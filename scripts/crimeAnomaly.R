# This script identifies anomalies
# in monthly crime counts over time
# Andrew Wheeler

# These are just a few defaults I expect, I expect data in wide format per month/PD
count_fields <- c("Murder", "Rape", "Robbery", "Agg.Assault", "Burglary", "Larceny","MVT", "Arson")
year_field <- "Year"
month_field <- "Month"
prior_ytd <- 5 # if you have more data it averages multiple prior years for the YTD metrics

# this only searches for fewer, can also search for high by setting "greater", or both
# via "two.sided"
alt = "less"


# This function looks at cumulative year to date stats
# so if prior total 100 YTD (averaged over prior_max years)
# and current is 20 YTD total, this would flagged
# this expects the values in per a single PD
ytd_poisson <- function(data,cf=count_fields,month='Month',year='Year',prior_max=prior_ytd,alt='less'){
    last_row <- tail(data,1)
    last_year <- last_row[,year]
    last_month <- last_row[,month]
    # filtered for earlier months
    early_months <- data[data[,month] <= last_month,]
    form <- paste0("cbind(",paste0(cf,collapse=","),") ~ ",year)
    agg_metrics <- aggregate(as.formula(form),data=data,FUN=sum)
    # this takes the prior max number of years
    curr_year <- tail(agg_metrics,1)
    prior_years <- agg_metrics[(agg_metrics[,year] < last_year) & 
                               (agg_metrics[,year] >= (last_year - prior_max)),]
    prior_n <- nrow(prior_years)
    lc <- length(cf)
    resp <- rep(NA,lc)
    for (i in 1:lc){
        cnt <- cf[i]
        curr_val <- curr_year[,cnt]
        prior_sum <- sum(prior_years[,cnt])
        # I do this here in case of missing data for a specific crime
        prior_n <- sum(!is.na(prior_years[,cnt]))
        restest <- poisson.test(c(curr_val,prior_sum),c(1,prior_n),alternative=alt)
        resp[i] <- restest$p.value
    }
    return(resp)
}

# This function looks at the average of the prior k months
# so if average of prior 8 is 30, and current month is 10
# this will likely flag
# can set prior_max to 1 to just look at current vs prior month
priork_poisson <- function(data,cf=count_fields,month='Month',year='Year',prior_max=8,alt='less'){
    last_row <- tail(data,1)
    last_year <- last_row[,year]
    last_month <- last_row[,month]
    # filtered current/prior
    curr_year <- tail(data,1)
    prior_years <- tail(data,prior_max+1)
    prior_years <- head(prior_years,prior_max)
    prior_n <- nrow(prior_years)
    lc <- length(cf)
    resp <- rep(NA,lc)
    for (i in 1:lc){
        cnt <- cf[i]
        curr_val <- curr_year[,cnt]
        prior_sum <- sum(prior_years[,cnt])
        # I do this here in case of missing data for a specific crime
        prior_n <- sum(!is.na(prior_years[,cnt]))
        restest <- poisson.test(c(curr_val,prior_sum),c(1,prior_n),alternative=alt)
        resp[i] <- restest$p.value
    }
    return(resp)
}


# So this will loop over all PDs and return a total count column
# along with a note, if the note says
# "Burglary_ytd1 | MVT_ytd1 | Larceny_pri8"
# That means this police department was flagged for year to date burglary, year to date MVT
# and prior 8 larceny (but not prior 1 larceny)
# sorts the results, so the agencies with the most flagges are at the top of the dataframe
metrics_allpd <- function(data,agency='Agency.Name',cf=count_fields,month='Month',year='Year',flagp=0.001){
    # make sure it is sorted
    d2 <- data[order(data[,agency],data[,year],data[,month]),] 
    pds <- unique(d2[,agency])
    df_outliers <- data.frame(pds)
    col_names <- c(paste0(cf,"_ytd1"),paste0(cf,"_pri8"),paste0(cf,"_pri1"))
    for (cn in col_names){
        df_outliers[,cn] <- NA
    }
    df_outliers$Note <- ""
    df_outliers$Total <- -1
    lp <- length(pds)
    for (i in 1:lp) {
        local_pd <- d2[d2[,agency] == pds[i],]
        pvals_ytd <- ytd_poisson(local_pd,prior_max=1) # only looking at prior YTD
        pvals_prior8 <- priork_poisson(local_pd,prior_max=8)
        pvals_prior1 <- priork_poisson(local_pd,prior_max=1)
        pvals_all <- c(pvals_ytd,pvals_prior8,pvals_prior1)
        # should maybe do a correction for above (Simes to aggregate)
        # or FDR to redo all p-values
        note <- paste0(col_names[pvals_all < flagp],collapse=" | ")
        total <- sum(pvals_all < flagp)
        df_outliers[i,col_names] <- pvals_all
        df_outliers[i,'Note'] <- note
        df_outliers[i,'Total'] <- total
    }
    df_flagged <- df_outliers[order(-df_outliers[,'Total']),]
    row.names(df_flagged) <- 1:nrow(df_flagged)
    return(df_flagged[,c("pds",'Total','Note')])
}

# Example use case
#df <- read.csv('or_jan22_present.csv')
#metrics_allpd(df)