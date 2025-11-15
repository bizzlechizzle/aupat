---
title: json1
---

- JSON1 Extension
	 - SQLite JSON1 extension for storing JSON data types in database columns

- 

- data structure
	 - stored as JSON arrays or JSON objects in text format

	 - enables JSON querying and manipulation within SQLite

- 

- usage in AUPAT
	 - aka_name [json1] - array of alternative location names
		 - example: ["Central Terminal", "Buffalo Central Terminal", "BCT"]

	 - sub_uuid [json1] - array of sub-location UUIDs
		 - example: ["a1b2c3d4-...", "e5f6g7h8-..."]

	 - img_hardware [json1] - object with camera metadata
		 - example: {"Make": "Canon", "Model": "EOS 5D Mark IV"}

	 - vid_hardware [json1] - object with camera metadata
		 - example: {"Make": "DJI", "Model": "Mavic 3 Pro"}

	 - img_docs [json1] - array of related document SHA256 hashes
		 - example: ["a1b2c3d4e5f6g7h8...", "i9j0k1l2m3n4o5p6..."]

	 - img_vids [json1] - array of related video SHA256 hashes
		 - example: ["q7r8s9t0u1v2w3x4..."]

	 - vid_imgs [json1] - array of related image SHA256 hashes
		 - example: ["y5z6a7b8c9d0e1f2..."]

	 - vid_docs [json1] - array of related document SHA256 hashes
		 - example: ["g3h4i5j6k7l8m9n0..."]

	 - docs_img [json1] - array of related image SHA256 hashes
		 - example: ["o1p2q3r4s5t6u7v8..."]

	 - docs_vid [json1] - array of related video SHA256 hashes
		 - example: ["w9x0y1z2a3b4c5d6..."]

- 

- querying json1 data
	 - use SQLite json functions
		 - json_extract() - extract values from json

		 - json_array_length() - get array length

		 - json_each() - iterate over array elements

- 

- benefits
	 - flexible schema for variable-length data

	 - maintains data relationships without junction tables

	 - native JSON support in SQLite

- 
