***
[TODO: Set up scheduler for `snapshot_agencies.py`]
***

**Overview**

The `agencies/` directory establishes the set of 
agency entities for which crime stats are sampled.

From an external source list of thousands of agencies,
the following criteria are used to reduce to a reasonable
set:

1. Use the latest `data_year` (currently `2023`).
2. Only keep records with `agency_type = "City"`.
3. Only keep locales with `population >= 40_000`.

After filtering, this data is matched to the existing
`RTCI` dataset, and a series of manual cleaning operations
are conducted (e.g., `"St Charles" -> "St. Charles"`).

Once 100% matching is achieved, data are interacted with
Airtable.

***

**Source**

*1. External participation file*

`Jeff Asher <jasher@ahdatalytics.com>` receives a CSV
file `CDE Participation 2000-{YYYY}.csv` via email 
from the FBI, which is stashed to AWS S3 (`rtci/sources/`).

The most recent file includes `2023` estimates.

*2. Internal included agencies file*

The most recent `final_sample.csv` CSV file
can be used to determine the preexisting set of agencies
that have been included in the sample by the RTCI team
(this is also stashed to AWS S3).

***

**Scripts**

There are two basic actions executed in this directory:

1. `update_agencies.py` takes the `CDE Participation 2000-{YYYY}.csv`
set of cities (including populations) and left-merges the 
set of distinct agencies (including sourcing metadata) 
from the `final_sample.csv` set of agencies. The output is 
upserted into the Airtable base/table `RTCI:Metadata`.


2. `snapshot_agencies.py` snapshots the current Airtable
base/table `RTCI:Metadata` as a JSON file to AWS as
`sample-rtci/airtable/{timestamp}.json`

***