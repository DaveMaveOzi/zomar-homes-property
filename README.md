# Atelier Estates — Flask real-estate website

A responsive, editorial-style real-estate website starter built with Python/Flask, HTML, CSS and vanilla JavaScript. The interface uses DM Sans, restrained typography, large property photography, subtle motion and a warm neutral palette.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (recommended).
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   python app.py
   ```

6. Visit http://127.0.0.1:5000

## Included

- Home / animated hero landing page
- Property catalogue with category filters: sale, rent, shortlets and land
- Individual property detail pages
- About, team and contact pages
- Contact enquiry form stored in a local SQLite database (`enquiries.db`)
- Responsive navigation, reveal-on-scroll motion and mobile menu

## Before going live

- Replace the sample brand, team details, contact details and demo listings.
- Replace remote Unsplash demo images with property photography you own or are licensed to use.
- Change `app.secret_key` to a long random secret stored in an environment variable.
- Turn off Flask debug mode in production; deploy behind a production WSGI server such as Gunicorn.
- Add server-side email notifications, spam protection, image uploads and a proper property-management/admin interface if required.
- The displayed property prices and details are sample content, not live listings.
