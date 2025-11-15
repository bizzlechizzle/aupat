---
title: db_ingest.py
---

- operation
	- ingests new locations in the database
- steps
	- load database location in #user.json.md in /user folder ["db_name","db_loc","arch_loc"]
	- call #backup.py.md
	- open database check [if null then namerize]
		- images - img_name
		- videos - vid_name
		- documents - doc_name
	- call #name.py.md
	- hardlink/copy new data into database at 'blank'_loc in database in respective tables
- notes
	- live videos go into 'original_other' folder under videos