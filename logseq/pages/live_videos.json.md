---
title: live_videos.json
---

- find matching videos/image in data base
	- compare "img_loco" "img_nameo" vs "vid_loco" "vid_nameo"
	- record image img_sha256 in "videos" table vid_imgs
	- record "vid_sha256" in images table img_vids
- alternate matching logic
	- record vid_sha256 in images table img_vids
	- record img_sha256 in videos table vid_imgs