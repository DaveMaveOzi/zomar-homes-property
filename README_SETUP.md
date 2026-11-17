# Zomar Homes & Property — Owner-Controlled Admin Prototype

## What this package includes

- Existing Zomar website and responsive layout.
- Public website does not display Admin Access, Admin Login, or Create Account links.
- Private administration route: `?zomar_page=Admin`.
- Company owner signs in using credentials stored in Streamlit Secrets.
- Only the owner can create administrator accounts.
- Owner can activate/deactivate administrator accounts.
- Admins can upload property listings for Sale, Rent, and Shortlet.
- Admins can set shortlets to Available or Fully Booked.
- Admins can remove sold/rented listings.
- Passwords for administrator accounts are stored as PBKDF2-HMAC-SHA256 hashes, not plain text.
- SQLite stores properties and admin accounts locally.

## Local setup (PyCharm on Windows)

1. Back up your current project folder and `app.py`.
2. Extract this package.
3. Copy the package's `app.py`, `requirements.txt`, `.gitignore`, and `.streamlit` folder into your existing Zomar project folder.
4. Keep `IMG_8176-removebg-preview.png` beside `app.py`.
5. Open `.streamlit/secrets.toml.example`, change the owner username and password, and save a copy named `secrets.toml` in the same `.streamlit` folder. The final path must be `.streamlit/secrets.toml`.
6. Use a long, unique owner password. Never send it to anyone or put it in app.py.
7. Do not commit `.streamlit/secrets.toml` or `zomar_properties.db` to GitHub.
8. In PyCharm Terminal:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

9. The public site will not show an admin link. To open the private login, enter this URL directly in the same browser:

`http://localhost:8501/?zomar_page=Admin`

10. Sign in with the owner credentials from `.streamlit/secrets.toml`.
11. In the Owner Dashboard, use **Create administrator account**. Enter the staff member's name, company email, username, and a temporary password of at least 12 characters. Give those credentials to the staff member privately.
12. The administrator signs in at the same private URL. The owner can deactivate or reactivate their account from **Administrator accounts**.

## Streamlit Community Cloud setup

The owner credentials must also be entered in the deployed app's Streamlit Cloud Settings → Secrets, using the same TOML format:

```toml
[owner]
username = "your-owner-username"
password = "your-long-unique-password"
```

Never commit secrets.toml to GitHub.

## Important prototype limitations

This is a local SQLite prototype, not production-ready hosted inventory:

- Streamlit Community Cloud local filesystem is not durable. SQLite records and uploaded image data can be lost on restart, rebuild, or redeploy.
- The app currently stores uploaded image data in SQLite as base64, intended only for a small prototype.
- Admin accounts are stored in SQLite; on Streamlit Cloud they can also be lost if the database file is lost.
- The owner account is configured through secrets, not stored in the users table.
- The private route is intentionally unlinked from the public UI, but a hidden URL is not a security boundary. Authentication and server-side role checks protect it.
- No password reset or invitation email is implemented; the owner shares a temporary password privately.
- There is no forced password change on first admin login.
- No audit trail exists.
- Sold/rented properties are deleted rather than archived.
- Shortlet Fully Booked is a manual flag, not a date-based booking calendar. It does not prevent overlapping reservations.
- Uploaded files have basic type/size limits but no malware scanning.

## Required before production

1. Migrate SQLite to a persistent managed database (e.g. PostgreSQL/Supabase).
2. Move image uploads to persistent object storage; keep image references in the database.
3. Use managed authentication or a properly designed authentication service with individual accounts, MFA where appropriate, password reset, invite flows, rate limiting, session expiry, and audit logging.
4. Add forced password change on first login and secure email invitation/verification.
5. Archive sold/rented properties with status, timestamps, and actor instead of deleting them.
6. Implement date-based shortlet availability and reservation conflict handling if customers will book dates.
7. Add automated backups, restore testing, database migrations, monitoring, and security review.
8. Test access control, deployment behaviour, uploads, and recovery before using it for company operations.

## Existing local database

If you already have a `zomar_properties.db`, back it up before testing. This app creates the admin users table if missing and preserves existing property records in the expected schema. If your database was created by an older or different schema, use a backup and test migration before relying on it.
