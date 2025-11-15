---
title: db_folder.py
---

- operation
	- creates folders for newly imported locations and their data
- steps
	- load database location in #user.json.md in /user folder ["db_name","db_loc"]
	- call #backup.py.md
	- open database check [if null then folderize]
		- locations - loc_loc
		- images - img_loc
		- videos - vid_loc
		- documents - doc_loc
		- urls - urls_loc
	- call #folder.py.md
	- record new folder in database for 'blank'_loc
	- documents folder always created by default