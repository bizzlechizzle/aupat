---
title: db_verify.py.md
---

- operation
	- verifies new locations in the database
- steps
	- load database location in #user.json.md in /user folder ["db_name","db_loc","arch_loc"]
	- call #backup.py.md
	- open database check files original location, new location, do a hash to verify they all succusessfuly imported to database and match the database
	- delete files in original files [ingest folder] location and delete any empty folder/parent folders