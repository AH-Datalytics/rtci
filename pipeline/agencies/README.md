This directory contains scripts to do the following:

***

1. Pull the complete list of agencies (including populations) from the FBI's Crime Data Explorer (CDE) API and snapshot that list to S3.
2. Take that snapshot and use it to interact with a Google Sheet called `agencies`.
3. Snapshot the Google Sheet to S3.
4. Query the FBI CDE API for agency-month crime counts (as far back as 1985).
5. Match agency names from the FBI to those displayed on the RTCI site.
***