# locations of all crosswalk files on AWS S3,
# copied over to S3 from this OneDrive directory:
#
# Ben Horwitz >
# Clients >
# Real Time Crime Index >
# Open Source Data >
# _Ben and Jeff Work >
# Ben and Jeff working files


PREFIX = "https://rtci.s3.us-east-1.amazonaws.com/crosswalks/agencies/"

ILCPD0000 = (
    PREFIX
    + "Chicago_Police_Department_-_Illinois_Uniform_Crime_Reporting__IUCR__Codes_20241106.csv"
)
LANPD0000 = PREFIX + "NOLA+Crosswalk(in).csv"
MD0172100 = PREFIX + "Prince+George+Crosswalk.xlsx"
MI8234900 = PREFIX + "Detroit+Crosswalk.csv"
VA1220000 = PREFIX + "Richmond+Crosswalk.xlsx"
