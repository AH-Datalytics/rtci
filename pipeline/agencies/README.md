***
[TODO: Wrap all in `__main__` funcs and make scripts 1 and 2
a single script with arguments]

[TODO: Set up scheduler for `snapshot_agencies.py`]
***

**Overview**

The `agencies/` directory establishes the set of 
agency entities for which crime stats are sampled.

***

**Sources**

*1. City Populations*

`Jeff Asher <jasher@ahdatalytics.com>` receives an 
Excel file `Populations for RTCI.xlsx` via email 
from the FBI with annual populations per city.Municipalities with populations `< 50,000`
are excluded from the sample.

The most recent file includes `2023` estimates for 
`859` cities meeting the above criterion.

*2. Included agencies*

The most recent `rtci/data/final_sample.csv` CSV file
can be used to determine the preexisting set of agencies
that have been included in the sample by the RTCI team.

***

**Scripts**

There are three basic actions executed in this directory:

1. `update_agencies.py` takes the `Populations for RTCI.xlsx`
set of cities (including populations) and left-merges the 
set of distinct agencies (including sourcing metadata) 
from the `final_sample.csv` set of agencies. The output is 
upserted into the Airtable base/table `RTCI:Metadata`.


2. `update_pops.py` takes the `Populations for RTCI.xlsx`
file and simply updates population data in the existing
Airtable base/table `RTCI:Metadata`


3. `snapshot_agencies.py` snapshots the current Airtable
base/table `RTCI:Metadata` as a JSON file to AWS as
`sample-rtci/airtable/{timestamp}.json`

***