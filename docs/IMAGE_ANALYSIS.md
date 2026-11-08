# Image-based emergency evidence

## Pipeline

1. **Upload** (`POST /incidents/{id}/media`, multipart `files`, tracking token or authorised user). Up to `MAX_IMAGES_PER_INCIDENT` (6), `MAX_IMAGE_MB` (8) each. The incident already exists, so image problems never block a report.
2. **Validation:** size; Pillow `verify()` + decode (rejects non-images and truncated files); format JPEG/PNG/WebP only; pixel-count limit.
3. **Cleaning:** re-encoded to JPEG, resized to ≤1600 px. This **drops all EXIF metadata including GPS** and neutralises polyglot payloads. Whether GPS was present is recorded (`exif_gps_present`) but never used as location.
4. **Quality and reuse checks:** sha256 duplicate in the same report (returns the existing item), same file in another report (`reused_image_seen_in_other_report`), edge-variance blur score (`possibly_blurry`), perceptual hash stored.
5. **Private storage:** `UPLOAD_DIR/<incident>/<uuid>.jpg`; served only through an authorised endpoint with `no-store` caching; `purge_after` = retention date.
6. **Vision analysis (background):** provider from `VISION_PROVIDER`. Status: `UPLOAD_RECEIVED → PROCESSING → ANALYSIS_COMPLETED | REVIEW_REQUIRED | PROCESSING_FAILED`, or `NOT_ANALYZED` when disabled.
7. **Validation of model output:** findings restricted to an allow-list (`damaged_vehicle`, `visible_flames`, `flooded_road`, `person_on_ground`, …); descriptions containing identity or medical words are blanked; `injury_assessment` is always `cannot_be_determined_from_image`; confidence kept as the model's own high/medium/low and labelled uncalibrated.
8. **Review flag** when: image unrelated/unclear, blurry, reused, all findings low confidence, or the scene contradicts the reported category.
9. **Use:** findings that support the incident category add capped corroboration points to priority; visible flames/smoke and road obstruction are routing inputs; each department sees only relevant findings (police do not see `person_on_ground`).

## Privacy rules given to the model

No identification, no faces/age/gender/ethnicity, no injury or death claims, no location guessing, ignore text inside the image. The citizen UI states that photos are used for the emergency, not to identify people.

## Not done / next steps

- No antivirus scanner (re-encoding is the mitigation; add ClamAV if accepting other file types).
- Video: schema supports `kind`, but frame extraction is not implemented.
- Evaluate the chosen vision model on a labelled set (clear/blurry accident, fire, flood, irrelevant, manipulated) before relying on it.
