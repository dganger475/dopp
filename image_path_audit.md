# Image Path Audit & Fix Documentation

## Objective
Fix persistent issues with user and match images not displaying due to path/URL inconsistencies, and document all attempted and implemented fixes to avoid redundant troubleshooting.

---

## 1. Standardize Image Path Storage in DB
- **Problem:** DB values for `profile_image` and match images are inconsistent (sometimes just filename, sometimes folder+filename, sometimes `/static/` prefix).
- **Solution:**
    - Decide on a single format for storing image references in the DB. **Recommended:** Store only the filename (e.g., `foo.png`).
    - Update all code to expect this format.
    - Add a migration or script to clean up existing DB entries if needed.

---

## 2. Update Normalization Logic
- **Problem:** `normalize_profile_image_path` and related helpers may not find images if the DB value format or folder is unexpected.
- **Solution:**
    - Update normalization to:
        - Always extract just the filename from the DB value.
        - Check all relevant folders: `profile_pics/`, `images/`, `faces/`, `extracted_faces/`.
        - If not found, return `None` (for search) or a default (for profile display).
    - Log every path lookup and result for debugging.

---

## 3. Audit API Responses
- **Problem:** API may return broken or `None` image URLs, causing frontend to display nothing.
- **Solution:**
    - Log the image URLs returned in all API responses (search, profile, matches).
    - Test these URLs directly in the browser to confirm they resolve to real images.
    - If a URL does not resolve, check both the returned value and the file on disk.

---

## 4. Frontend Handling
- **Problem:** Frontend may not handle `None` or broken URLs gracefully.
- **Solution:**
    - Add logic to display a clear error or fallback UI if the image URL is missing or broken, rather than a blank card.

---

## 5. Logging and Debugging Improvements
- **Problem:** Hard to trace why a particular image is not found.
- **Solution:**
    - Add debug logging to all image path normalization and URL construction code.
    - Log: input value, attempted folders, final URL/path, and whether the file was found.

---

## 6. Next Steps & Checklist
- [ ] Standardize DB storage of image paths (filename only)
- [ ] Update normalization logic to check all relevant folders
- [ ] Add/verify logging in all relevant functions
- [ ] Audit and test API responses for image URLs
- [ ] Add frontend handling for missing/broken URLs

---

## Notes
- **Do not repeat fixes that have already been attempted and documented here.**
- Update this file with every new fix or change related to image path handling.
- If a fix does not work, record the reason why here for future reference.
