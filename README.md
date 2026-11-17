# Zomar Homes & Property — SQLite Admin Prototype

This version adds a local SQLite property inventory and a protected admin dashboard.

## Included

- Properties page Availability filter: All, For Sale, For Rent, Shortlet.
- SQLite database (`zomar_properties.db`) created automatically beside `app.py`.
- Existing six demo listings are copied into the database the first time it is created.
- Admin sign-in using credentials stored outside the source code.
- Add properties for sale, rent, or shortlet.
- Upload JPG, JPEG, PNG, or WEBP property images (maximum 5 MB), or provide an image URL.
- Mark shortlets as Available or Fully Booked.
- Remove sold and rented listings from public inventory.
- Public property cards and details show the shortlet booking status.

## Local setup in PyCharm (Windows)

1. Back up your current `app.py`.
2. Replace it with this package's `app.py`.
3. Keep `IMG_8176-removebg-preview.png` in the same folder as `app.py`.
4. Create a folder named `.streamlit` beside `app.py`.
5. Inside `.streamlit`, create `secrets.toml` with this structure:

```toml
[admin]
username = "choose-an-admin-username"
password = "replace-this-with-a-long-unique-password"
```

6. Do not commit `secrets.toml` to GitHub. The included `.gitignore` excludes it.
7. Install the dependency:

```powershell
py -m pip install -r requirements.txt
```

8. Run the app:

```powershell
py -m streamlit run app.py
```

9. Open the website and choose **Admin Access** in the footer or the mobile menu.

If you already have a `zomar_properties.db` file, back it up before testing this version. The app seeds the six demo listings only when the database has no records. It does not overwrite an existing inventory.

## GitHub and Streamlit Community Cloud

For local testing, keep `zomar_properties.db` out of GitHub. For a temporary Streamlit Cloud test, add the same credentials in the app's **Settings → Secrets** using TOML format:

```toml
[admin]
username = "your-admin-username"
password = "your-long-unique-password"
```

The app's local SQLite database and uploaded image data are stored in the app's local filesystem. Streamlit Community Cloud does not provide a durable persistent disk for this kind of application data. Database contents and uploaded images can be lost when the app is restarted, rebuilt, or redeployed. Do not use this SQLite version as the live company's source of truth.

## Required changes before production

1. Replace local SQLite with a managed persistent database such as PostgreSQL/Supabase.
2. Move uploaded property images to persistent object storage (for example, Supabase Storage or S3-compatible storage); store only the image URL/key in the database.
3. Use a proper authentication system with individual admin accounts, secure password hashing, role permissions, password reset, and login rate limiting. The prototype uses one shared configured admin credential.
4. Add audit history instead of permanently deleting a sold/rented listing. Production should normally record a lifecycle state such as Sold or Rented, who changed it, and when. This prototype removes those listings from the database as requested.
5. Add backups, database migrations, validation, upload scanning/limits, and monitoring.
6. Add a proper shortlet booking calendar and date-range inventory if customers will book specific dates. The current Fully Booked switch is a manual status only; it does not prevent date overlaps or process reservations.
7. Add server-side authorization checks to every admin operation and test access control before public launch.

## Prototype limitations

- No payment processing or customer reservation workflow.
- No automated shortlet calendar, booking dates, or booking conflict detection.
- Sold/rented listings are deleted, not archived.
- One shared admin account; no separate staff roles.
- Uploaded images are stored inside SQLite as base64 data, suitable only for small local prototypes.
- No email notifications, audit trail, or automatic enquiry handling.
