[WIP]

**Overview**

The `agencies/` directory establishes the set of 
agency entities for which crime stats are sampled.

**Inputs**

`Jeff Asher <jasher@ahdatalytics.com>` receives an 
Excel file `Populations for RTCI.xlsx` via email 
from the FBI with annual populations per city.

Municipalities with populations `< 50,000`
are excluded from the sample.

The most recent file includes `2023` estimates for 
`859` cities meeting the above criterion.

**Outputs**

The script `update_airtable_pops.py` takes the 
populations file and updates populations in the
Airtable table `RTCI:Metadata`.