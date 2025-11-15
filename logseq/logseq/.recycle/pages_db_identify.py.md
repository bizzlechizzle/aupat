---
title: db_identify.py
---

- operation
	- generates master .json files for each location with all pertinent information
	- exports location metadata, images, videos, documents, and urls into single json
- steps
	- load database location in #user.json in /user folder ["db_name","db_loc","arch_loc"]
	- check "locations" - column "loc_update" and "json_update" if "loc_update" is newer or "json_update" is null, generate new .json
		- pull loc_uuid - search across all tables [locations, sub-locations, images, videos, documents, urls]
		- compile all data into master json structure
		- call #name.py.md for document name: loc_uuid8_master.json
		- save in location-name_loc_uuid8/documents/
	- update "json_update" column in locations table with current timestamp
	-