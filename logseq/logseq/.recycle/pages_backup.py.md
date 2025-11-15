---
title: backup.py
---

- operation
	 - backups database

- steps
	 - load database in #user.json in /user folder ["db_name","db_loc","db_backup"]

	 - check "db_backup" for most recent backup time [keep in cache will use to verify soon]

	 - make a copy of backup database
		 - naming schema
			 - "db_name"-timestamp.db
				 - timestamp from normalization dateutil

	 - record version number in "versions" table call dateutil, record in ver_updated for script

	 - verify backup was created successfully
		 - check backup file exists at expected path

		 - verify backup file size matches or exceeds original database

		 - verify backup timestamp is current
