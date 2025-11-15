---
title: style-guide
---

- AUPAT Style Guide
	 - naming conventions and coding standards

- 

- column naming conventions
	 - format: table_columntype
		 - examples: img_name, vid_loc, doc_sha256

	 - original file columns: tableco and tablenameo [no underscore]
		 - img_loco - original image folder location

		 - img_nameo - original image file name

		 - vid_loco - original video folder location

		 - vid_nameo - original video file name

		 - doc_loco - original document folder location

		 - doc_nameo - original document file name

	 - uuid columns
		 - loc_uuid - full uuid4 for location

		 - loc_uuid8 - first 8 characters of loc_uuid

		 - sub_uuid - full uuid4 for sub-location

		 - sub_uuid8 - first 8 characters of sub_uuid

		 - url_uuid - full uuid4 for url

		 - url_uuid8 - first 8 characters of url_uuid

	 - hash columns
		 - img_sha256 - full sha256 hash stored in database

		 - vid_sha256 - full sha256 hash stored in database

		 - doc_sha256 - full sha256 hash stored in database

		 - img_sha8 - first 8 characters [used in file naming only]

		 - vid_sha8 - first 8 characters [used in file naming only]

		 - doc_sha8 - first 8 characters [used in file naming only]

- 

- file naming conventions
	 - images
		 - with sub-location: "loc_uuid8"-"sub_uuid8"-"img_sha8".extension

		 - without sub-location: "loc_uuid8"-"img_sha8".extension

	 - videos
		 - with sub-location: "loc_uuid8"-"sub_uuid8"-"vid_sha8".extension

		 - without sub-location: "loc_uuid8"-"vid_sha8".extension

	 - documents
		 - with sub-location: "loc_uuid8"-"sub_uuid8"-"doc_sha8".extension

		 - without sub-location: "loc_uuid8"-"doc_sha8".extension

	 - master json
		 - loc_uuid8_master.json

- 

- folder naming conventions
	 - location folders: "location-name"_"loc_uuid8"
		 - use hyphens to replace spaces in location names

		 - example: central-terminal_a1b2c3d4

	 - folder structure
		 - locations: arch_loc/state-type/location-name_loc_uuid8/

		 - images: location-name_loc_uuid8/photos/original_[source]/

		 - videos: location-name_loc_uuid8/videos/original_[source]/

		 - documents: location-name_loc_uuid8/documents/[type]/

		 - urls: location-name_loc_uuid8/documents/websites/domain_url_uuid8

- 

- boolean field initialization
	 - hardware detection fields start null
		 - original, camera, phone, drone, go_pro, dash_cam, other, film

	 - metadata extraction flags start false
		 - exiftool_hardware [images]

		 - ffmpeg_hardware [videos]

- 

- json1 data types
	 - use SQLite JSON1 extension for variable-length data

	 - arrays stored as json arrays: ["item1", "item2"]

	 - objects stored as json objects: {"key": "value"}

	 - see #json1.md for detailed examples

- 

- normalization requirements
	 - dates: use dateutil for all date/time normalization

	 - text: use unidecode and titlecase for text normalization

	 - addresses: use libpostal for address/state normalization

	 - states: use USPS two-letter abbreviations [AL-WY]

- 

- database standards
	 - transaction safety required for all write operations

	 - PRAGMA foreign_keys = ON must be enforced

	 - SHA256 collision checking for all media files

	 - UUID8 collision checking for location identifiers

	 - backup before all major operations

- 

- code organization
	 - follow BPA [Best Practices Always]

	 - follow BPL [Bulletproof Longterm]

	 - follow KISS [Keep it Simple Stupid]

	 - follow FAANG PE [enterprise-level engineering for personal/small business]

	 - apply WWYDD [What Would You Do Differently] only for urgent/major/fatal flaws

- 
