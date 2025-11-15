---
title: gen_uuid.py
---

- operation
	- creates a unique uuid4 when called
- steps
	- generate a uuid4 in python when called
	- load database in #user.json in /user folder ["db_name","db_loc"]
	- check "locations" table - column "loc_uuid" and "sub-locations" table - "sub_uuid" and verify the first 8 characters of our new key are unique
		- if uuid is not unique generate a new uuid4 until this step passes
	-