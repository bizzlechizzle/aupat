---
title: locations.json.md
---

- rows
	 - blank

- columns
	 - loc_name: location name - based off folder name
		 - normalization: unidecode, titlecase

	 - aka_name: also known as name [json1]
		 - normalization: unidecode, titlecase

	 - state: USPS Two-Letter State Code - based off folder name
		 - normalization: libpostal

	 - type: location type - based off folder name
		 - normalization: unidecode, titlecase

	 - sub_type: sub-location type - based off folder name
		 - normalization: unidecode, titlecase

	 - loc_uuid: uuid4 for location

	 - loc_uuid8: first 8 characters of uuid

	 - sub_uuid: uuid4 for sub-location [json1]

	 - org_loc: original folder location [absolute path]

	 - loc_loc: folder location [absolute path]

	 - loc_add: date added to database
		 - normalization: dateutil

	 - loc_update: date anytime anything was updated for location including import
		 - normalization: dateutil

	 - imp_author: import author

	 - json_update: last time .json was generated
