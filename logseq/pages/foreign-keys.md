---
title: foreign-keys
---

- AUPAT Database Relationships
	 - foreign key constraints and table relationships

- 

- locations table [parent]
	 - primary key: loc_uuid [uuid4]

	 - referenced by:
		 - sub-locations.loc_uuid

		 - images.loc_uuid

		 - videos.loc_uuid

		 - documents.loc_uuid

		 - urls.loc_uuid

- 

- sub-locations table [child of locations]
	 - primary key: sub_uuid [uuid4]

	 - foreign key: loc_uuid REFERENCES locations(loc_uuid)

	 - referenced by:
		 - images.sub_uuid

		 - videos.sub_uuid

		 - documents.sub_uuid

		 - urls.sub_uuid

- 

- images table [child of locations and sub-locations]
	 - primary key: img_sha256 [sha256 hash]

	 - foreign keys:
		 - loc_uuid REFERENCES locations(loc_uuid)

		 - sub_uuid REFERENCES sub-locations(sub_uuid) [nullable]

	 - relationships stored as json1 arrays:
		 - img_docs [json1] - array of doc_sha256 hashes

		 - img_vids [json1] - array of vid_sha256 hashes [live photos]

- 

- videos table [child of locations and sub-locations]
	 - primary key: vid_sha256 [sha256 hash]

	 - foreign keys:
		 - loc_uuid REFERENCES locations(loc_uuid)

		 - sub_uuid REFERENCES sub-locations(sub_uuid) [nullable]

	 - relationships stored as json1 arrays:
		 - vid_docs [json1] - array of doc_sha256 hashes

		 - vid_imgs [json1] - array of img_sha256 hashes [live photos]

- 

- documents table [child of locations and sub-locations]
	 - primary key: doc_sha256 [sha256 hash]

	 - foreign keys:
		 - loc_uuid REFERENCES locations(loc_uuid)

		 - sub_uuid REFERENCES sub-locations(sub_uuid) [nullable]

	 - relationships stored as json1 arrays:
		 - docs_img [json1] - array of img_sha256 hashes

		 - docs_vid [json1] - array of vid_sha256 hashes

- 

- urls table [child of locations and sub-locations]
	 - primary key: url_uuid [uuid4]

	 - foreign keys:
		 - loc_uuid REFERENCES locations(loc_uuid)

		 - sub_uuid REFERENCES sub-locations(sub_uuid) [nullable]

- 

- versions table [standalone]
	 - primary key: modules [module name]

	 - no foreign key relationships

	 - tracks version history for all scripts and configurations

- 

- relationship types
	 - one-to-many: locations → [sub-locations, images, videos, documents, urls]

	 - one-to-many: sub-locations → [images, videos, documents, urls]

	 - many-to-many: images ↔ documents [via json1 arrays]

	 - many-to-many: images ↔ videos [via json1 arrays for live photos]

	 - many-to-many: videos ↔ documents [via json1 arrays]

- 

- cascade behavior
	 - on delete location: should cascade to all related records

	 - on delete sub-location: should cascade to related media

	 - on delete image/video/document: update json1 arrays in related records

- 

- integrity constraints
	 - PRAGMA foreign_keys = ON [enforced at connection]

	 - SHA256 uniqueness enforced for images, videos, documents

	 - UUID4 uniqueness enforced for locations, sub-locations, urls

	 - UUID8 collision checking for first 8 characters

- 

- notes
	 - json1 arrays used instead of junction tables for flexibility

	 - nullable sub_uuid allows media without sub-location

	 - all relationships maintain referential integrity

	 - see #json1.md for json array structure examples

- 
