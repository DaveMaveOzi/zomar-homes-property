import streamlit as st
import base64
import os
import sqlite3
import hashlib
import hmac
import json
import secrets as pysecrets
from contextlib import contextmanager
from pathlib import Path
from html import escape

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Zomar Homes & Property",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 2. BRAND COLOURS
# =========================================================

GOLD = "#D8A800"
GOLD_HOVER = "#A98200"
BLACK = "#171717"
WHITE = "#FFFFFF"

# =========================================================
# 3. SESSION STATE
# =========================================================

defaults = {
    "page": "Home",
    "theme": "Light",
    "selected_property": None,
    "search_query": "",
    "filter_type": "All",
    "filter_status": "All",
    "admin_authenticated": False,
    "auth_role": None,
    "auth_username": None,
    "show_forgot_password": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Mobile dropdown links use a URL change so the browser closes the popover
# immediately after a selection. Keep the selected page in session state.
VALID_PAGES = {"Home", "Properties", "About Us", "Contact Us", "Property Details", "Admin"}
requested_page = st.query_params.get("zomar_page")
if requested_page in VALID_PAGES:
    st.session_state.page = requested_page

# =========================================================
# 4. THEME SETTINGS
# =========================================================

if st.session_state.theme == "Light":

    BG = "#F8F7F3"
    SURFACE = "#FFFFFF"
    TEXT = "#171717"
    MUTED = "#77736D"
    BORDER = "#E8E5DE"
    INPUT_BG = "#292929"

else:

    BG = "#171717"
    SURFACE = "#242424"
    TEXT = "#F5F3EF"
    MUTED = "#B8B4AD"
    BORDER = "#3D3D3D"
    INPUT_BG = "#292929"

# =========================================================
# 5. PROPERTY DATA
# These are demonstration listings.
# Replace them with actual company inventory.
# =========================================================

properties = [
    {
        "id": 1,
        "name": "The Ivory Residence",
        "location": "Lekki Phase 1, Lagos",
        "price": 185000000,
        "type": "Apartment",
        "status": "For Sale",
        "bedrooms": 3,
        "bathrooms": 3,
        "area": "220 sqm",
        "image": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200",
        "description": (
            "A beautifully designed contemporary residence offering "
            "generous living spaces, elegant finishes and a comfortable "
            "modern lifestyle."
        )
    },
    {
        "id": 2,
        "name": "The Palm Residence",
        "location": "Ikoyi, Lagos",
        "price": 450000000,
        "type": "Duplex",
        "status": "For Sale",
        "bedrooms": 5,
        "bathrooms": 5,
        "area": "420 sqm",
        "image": "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=1200",
        "description": (
            "An elegant duplex with spacious interiors, premium "
            "finishing and a carefully considered architectural design."
        )
    },
    {
        "id": 3,
        "name": "Azure Heights",
        "location": "Victoria Island, Lagos",
        "price": 250000000,
        "type": "Apartment",
        "status": "For Sale",
        "bedrooms": 3,
        "bathrooms": 4,
        "area": "260 sqm",
        "image": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1200",
        "description": (
            "A refined apartment in a desirable location, designed "
            "around comfort, natural light and practical everyday living."
        )
    },
    {
        "id": 4,
        "name": "The Garden Estate",
        "location": "Ajah, Lagos",
        "price": 95000000,
        "type": "Detached House",
        "status": "For Sale",
        "bedrooms": 4,
        "bathrooms": 4,
        "area": "350 sqm",
        "image": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=1200",
        "description": (
            "A welcoming family home with a spacious layout, private "
            "outdoor space and contemporary architectural details."
        )
    },
    {
        "id": 5,
        "name": "The Oakwood Villa",
        "location": "Banana Island, Lagos",
        "price": 650000000,
        "type": "Villa",
        "status": "For Sale",
        "bedrooms": 5,
        "bathrooms": 6,
        "area": "500 sqm",
        "image": "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=1200",
        "description": (
            "A distinctive villa featuring expansive living areas, "
            "sophisticated interiors and an exclusive residential setting."
        )
    },
    {
        "id": 6,
        "name": "The Cedar Apartments",
        "location": "Oniru, Lagos",
        "price": 120000000,
        "type": "Apartment",
        "status": "For Rent",
        "bedrooms": 2,
        "bathrooms": 2,
        "area": "160 sqm",
        "image": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1200",
        "description": (
            "A modern apartment with practical living spaces, "
            "understated finishes and convenient access to key parts of Lagos."
        )
    }
]


# =========================================================
# 5A. LOCAL SQLITE PROPERTY STORE (PROTOTYPE)
# =========================================================

PROJECT_FOLDER = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_FOLDER / "zomar_properties.db"

@contextmanager
def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=20)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def initialise_property_database():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                price REAL NOT NULL,
                property_type TEXT NOT NULL,
                availability TEXT NOT NULL
                    CHECK (availability IN ('For Sale', 'For Rent', 'Shortlet')),
                booking_status TEXT NOT NULL DEFAULT 'Available'
                    CHECK (booking_status IN ('Available', 'Fully Booked')),
                bedrooms INTEGER NOT NULL DEFAULT 0,
                bathrooms INTEGER NOT NULL DEFAULT 0,
                area TEXT NOT NULL DEFAULT '',
                image TEXT NOT NULL DEFAULT '',
                images_json TEXT NOT NULL DEFAULT '[]',
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # A persistent marker prevents demo listings from being re-created after
        # the owner/admin intentionally removes every property.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
            """
        )
        # Migrate databases created by earlier versions of this prototype.
        property_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(properties)").fetchall()
        }
        if "images_json" not in property_columns:
            connection.execute("ALTER TABLE properties ADD COLUMN images_json TEXT NOT NULL DEFAULT '[]'")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()

        seeded = connection.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'demo_properties_seeded'"
        ).fetchone()
        if seeded is None:
            count = connection.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
            # Seed only on the first-ever initialisation. Deleting all listings later
            # will not cause the demo properties to return after a restart.
            if count == 0:
                for item in properties:
                    connection.execute(
                        """
                        INSERT INTO properties
                        (name, location, price, property_type, availability,
                         booking_status, bedrooms, bathrooms, area, image, images_json, description)
                        VALUES (?, ?, ?, ?, ?, 'Available', ?, ?, ?, ?, '[]', ?)
                        """,
                        (
                            item["name"], item["location"], item["price"],
                            item["type"], item["status"], item["bedrooms"],
                            item["bathrooms"], item["area"], item["image"],
                            item["description"]
                        )
                    )
            connection.execute(
                "INSERT INTO app_settings (setting_key, setting_value) VALUES ('demo_properties_seeded', '1')"
            )
            connection.commit()


def load_properties():
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM properties ORDER BY created_at DESC, id DESC"
        ).fetchall()

    loaded = []
    for row in rows:
        loaded.append({
            "id": row["id"],
            "name": row["name"],
            "location": row["location"],
            "price": row["price"],
            "type": row["property_type"],
            "status": row["availability"],
            "booking_status": row["booking_status"],
            "bedrooms": row["bedrooms"],
            "bathrooms": row["bathrooms"],
            "area": row["area"],
            "image": row["image"],
            "images": json.loads(row["images_json"] or "[]") if "images_json" in row.keys() else [],
            "description": row["description"]
        })
    return loaded


def insert_property(item):
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO properties
            (name, location, price, property_type, availability,
             booking_status, bedrooms, bathrooms, area, image, images_json, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["name"], item["location"], item["price"], item["type"],
                item["status"], item.get("booking_status", "Available"),
                item["bedrooms"], item["bathrooms"], item["area"],
                item["image"], json.dumps(item.get("images", [])), item["description"]
            )
        )
        connection.commit()


def update_shortlet_booking(property_id, booking_status):
    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE properties
            SET booking_status = ?
            WHERE id = ? AND availability = 'Shortlet'
            """,
            (booking_status, property_id)
        )
        connection.commit()


def remove_property(property_id):
    with get_db_connection() as connection:
        connection.execute("DELETE FROM properties WHERE id = ?", (property_id,))
        connection.commit()


def remove_all_properties():
    with get_db_connection() as connection:
        connection.execute("DELETE FROM properties")
        connection.commit()
        connection.commit()


initialise_property_database()
properties = load_properties()


# =========================================================
# 6. LOGO LOADING
# The logo must be beside app.py.
# =========================================================

PROJECT_FOLDER = Path(__file__).resolve().parent

LOGO_PATH = PROJECT_FOLDER / "IMG_8176-removebg-preview.png"

logo_html = """
<div class="logo-fallback">
    <div>Zomar <span>Homes</span></div>
    <small>& PROPERTY</small>
</div>
"""

if LOGO_PATH.exists():

    with open(LOGO_PATH, "rb") as logo_file:
        logo_base64 = base64.b64encode(
            logo_file.read()
        ).decode("utf-8")

    logo_theme_class = " dark-mode-logo" if st.session_state.theme == "Dark" else ""

    logo_html = f"""
    <div class="logo-container{logo_theme_class}">
        <img
            src="data:image/png;base64,{logo_base64}"
            alt="Zomar Homes & Property"
        >
    </div>
    """

# Make the complete logo a home link on desktop and mobile.
logo_html = f'<a class="zomar-logo-link" href="?zomar_page=Home" target="_self" aria-label="Zomar Homes & Property home">{logo_html}</a>'

# =========================================================
# 7. CUSTOM CSS
# =========================================================

st.html(
    f"""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

    :root {{
        --bg: {BG};
        --surface: {SURFACE};
        --text: {TEXT};
        --muted: {MUTED};
        --border: {BORDER};
        --gold: {GOLD};
        --gold-hover: {GOLD_HOVER};
        --input-bg: {INPUT_BG};
    }}

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
    }}

    .stApp {{
        background: var(--bg);
        color: var(--text);
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    #MainMenu, footer {{
        visibility: hidden;
    }}

    .block-container {{
        max-width: 1380px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }}

    h1, h2, h3, h4 {{
        font-family: 'Playfair Display', serif !important;
        color: var(--text) !important;
    }}

    /* ======================================
       LOGO
    ====================================== */

    .zomar-logo-link {{
        display: block;
        width: fit-content;
        max-width: 100%;
        text-decoration: none !important;
        line-height: 0;
    }}

    .logo-container {{
        width: 380px;
        height: 172px;
        max-width: 100%;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding: 2px 0;
        border-radius: 0;
        overflow: visible;
    }}

    .logo-container img {{
        width: 360px;
        height: 164px;
        max-width: 100%;
        object-fit: contain;
        object-position: left center;
        display: block;
        background: transparent;
    }}

    /* The source logo uses dark lettering. In dark mode, render the
       complete logo artwork white while preserving its transparency. */
    .logo-container.dark-mode-logo img {{
        filter: brightness(0) invert(1);
    }}

    .logo-fallback {{
        color: var(--text);
        font-family: 'Playfair Display', serif;
        font-size: 22px;
        font-weight: 700;
    }}

    .logo-fallback span {{
        color: var(--gold);
    }}

    .logo-fallback small {{
        display: block;
        font-family: 'DM Sans', sans-serif;
        font-size: 9px;
        letter-spacing: 3px;
    }}

    /* ======================================
       RESPONSIVE NAVIGATION
    ====================================== */

    /* Desktop navigation and theme control are visible by default. */
    .st-key-mobile_header_controls {{
        display: none;
    }}

    .st-key-desktop_theme_toggle {{
        display: block;
    }}

    .st-key-desktop_navigation {{
        display: block;
    }}

    /* Compact mobile hamburger dropdown. */
    .zomar-mobile-menu {{
        position: relative;
        display: inline-block;
        z-index: 1000;
    }}

    .zomar-mobile-menu summary {{
        list-style: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 38px;
        box-sizing: border-box;
        padding: 0;
        background: #FFFFFF !important;
        color: #171717 !important;
        border: 1px solid #D8D4CA;
        border-radius: 5px;
        box-shadow: 0 1px 4px rgba(0,0,0,.10);
        font-size: 21px;
        font-weight: 700;
        line-height: 1;
        user-select: none;
    }}

    .zomar-mobile-menu summary::-webkit-details-marker {{
        display: none;
    }}

    .zomar-mobile-menu summary:hover,
    .zomar-mobile-menu[open] summary {{
        background: #FFFFFF !important;
        color: #171717 !important;
        border-color: var(--gold);
    }}

    .zomar-menu-panel {{
        position: absolute;
        top: calc(100% + 6px);
        right: 0;
        width: 148px;
        padding: 5px;
        box-sizing: border-box;
        background: #FFFFFF !important;
        border: 1px solid var(--gold);
        border-radius: 6px;
        box-shadow: 0 8px 20px rgba(0,0,0,.14);
    }}

    .zomar-menu-panel a {{
        display: block;
        box-sizing: border-box;
        width: 100%;
        padding: 8px 9px;
        margin: 1px 0;
        border-radius: 4px;
        color: #171717 !important;
        background: #FFFFFF !important;
        text-decoration: none !important;
        font-size: 13px;
        line-height: 1.25;
    }}

    .zomar-menu-panel a:hover {{
        color: #171717 !important;
        background: #F5EBC8 !important;
    }}

    /* ======================================
       THEME BUTTON
    ====================================== */

    [class*="st-key-theme_toggle"] button {{
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 50% !important;
        width: 43px;
        height: 43px;
        min-height: 43px;
        padding: 0 !important;
        font-size: 18px !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    }}

    [class*="st-key-theme_toggle"] button:hover {{
        background: var(--bg) !important;
        border-color: var(--gold) !important;
    }}

    /* ======================================
       GENERAL BUTTONS
    ====================================== */

    .stButton > button {{
        background: var(--gold) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--gold) !important;
        border-radius: 4px !important;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        transition: all 0.2s ease;
    }}

    .stButton > button p {{
        color: #FFFFFF !important;
    }}

    .stButton > button:hover {{
        background: var(--gold-hover) !important;
        border-color: var(--gold-hover) !important;
        color: #FFFFFF !important;
        transform: translateY(-2px);
    }}


    /* ======================================
       MOBILE THEME TOGGLE — keep it distinct
       from the general gold action buttons.
    ====================================== */

    div[class*="st-key-mobile_theme_toggle"] button,
    div[class*="st-key-desktop_theme_toggle"] button {{
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 50% !important;
        width: 43px !important;
        height: 43px !important;
        min-height: 43px !important;
        padding: 0 !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08) !important;
        transform: none !important;
    }}

    div[class*="st-key-mobile_theme_toggle"] button:hover,
    div[class*="st-key-desktop_theme_toggle"] button:hover {{
        background: var(--bg) !important;
        color: var(--text) !important;
        border-color: var(--gold) !important;
    }}

    div[class*="st-key-mobile_theme_toggle"] button *,
    div[class*="st-key-desktop_theme_toggle"] button * {{
        color: var(--text) !important;
        fill: var(--text) !important;
    }}

    /* ======================================
       MOBILE HEADER ALIGNMENT
    ====================================== */

    .st-key-mobile_header_controls [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 8px !important;
        width: max-content !important;
        max-width: 100% !important;
        margin-left: auto !important;
    }}

    .st-key-mobile_header_controls [data-testid="column"] {{
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }}

    /* ======================================
       HERO
    ====================================== */

    .hero {{
        position: relative;
        min-height: 500px;
        border-radius: 5px;
        overflow: hidden;
        display: flex;
        align-items: center;
        padding: 65px;
        background:
            linear-gradient(
                90deg,
                rgba(0,0,0,0.78),
                rgba(0,0,0,0.24)
            ),
            url('https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1800')
            center/cover;
        animation: fadeIn 0.8s ease both;
    }}

    .hero-content {{
        max-width: 650px;
        animation: fadeUp 0.8s ease both;
    }}

    .hero-eyebrow {{
        color: #E8C85B !important;
        font-size: 12px;
        letter-spacing: 3px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 18px;
    }}

    .hero h1 {{
        color: #FFFFFF !important;
        font-size: clamp(40px, 5vw, 66px);
        line-height: 1.12;
        margin-bottom: 20px;
    }}

    .hero p {{
        color: #FFFFFF !important;
        font-size: 16px;
        line-height: 1.8;
        max-width: 540px;
    }}

    /* ======================================
       SECTION HEADINGS
    ====================================== */

    .section-heading {{
        font-family: 'Playfair Display', serif;
        font-size: 35px;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 5px;
    }}

    .section-subtitle {{
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 25px;
    }}

    /* ======================================
       PROPERTY CARDS
    ====================================== */

    .property-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 5px;
        overflow: hidden;
        margin-bottom: 8px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fadeUp 0.7s ease both;
    }}

    .property-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.09);
    }}

    .property-image-wrap {{
        overflow: hidden;
        height: 225px;
    }}

    .property-image {{
        width: 100%;
        height: 225px;
        object-fit: cover;
        display: block;
        transition: transform 0.5s ease;
    }}

    .property-card:hover .property-image {{
        transform: scale(1.04);
    }}

    .property-info {{
        padding: 19px;
    }}

    .property-status {{
        display: inline-block;
        background: rgba(216,168,0,0.14);
        color: var(--gold);
        padding: 5px 10px;
        border-radius: 2px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}

    .property-name {{
        font-family: 'Playfair Display', serif;
        font-size: 21px;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 7px;
    }}

    .property-location {{
        display: flex;
        align-items: center;
        gap: 7px;
        font-size: 13px;
        color: var(--muted);
        margin-bottom: 13px;
    }}

    .location-icon {{
        width: 16px;
        height: 16px;
        flex-shrink: 0;
        stroke: var(--gold);
        fill: none;
        stroke-width: 1.8;
        stroke-linecap: round;
        stroke-linejoin: round;
    }}

    .property-price {{
        color: var(--gold);
        font-size: 19px;
        font-weight: 700;
        margin-bottom: 12px;
    }}

    .property-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        border-top: 1px solid var(--border);
        padding-top: 13px;
        color: var(--muted);
        font-size: 12px;
    }}

    /* ======================================
       CONTENT PANELS
    ====================================== */

    .content-panel {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 5px;
        padding: 28px;
    }}

    /* ======================================
       CONTACT FORM
    ====================================== */

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {{
        background: var(--input-bg) !important;
        color: #FFFFFF !important;
        border: 1px solid #51483F !important;
        border-radius: 3px !important;
    }}

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {{
        color: #C8C2BA !important;
    }}

    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label {{
        color: var(--text) !important;
    }}

    [data-testid="stFormSubmitButton"] button {{
        background: var(--gold) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--gold) !important;
        border-radius: 4px !important;
    }}

    [data-testid="stFormSubmitButton"] button p {{
        color: #FFFFFF !important;
    }}

    [data-testid="stFormSubmitButton"] button:hover {{
        background: var(--gold-hover) !important;
        border-color: var(--gold-hover) !important;
    }}

    /* ======================================
       FOOTER
    ====================================== */

    .footer {{
        background: #171717;
        color: #FFFFFF;
        padding: 35px;
        border-radius: 5px;
        margin-top: 60px;
    }}

    .footer h3 {{
        color: #FFFFFF !important;
    }}

    .footer p {{
        color: #D5D1C8 !important;
        font-size: 13px;
    }}

    .footer-accent {{
        color: #E0B600 !important;
    }}

    /* ======================================
       ANIMATIONS
    ====================================== */

    @keyframes fadeUp {{
        from {{
            opacity: 0;
            transform: translateY(16px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0.6; }}
        to {{ opacity: 1; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }}
    }}

    @media (max-width: 768px) {{

        .st-key-desktop_navigation,
        .st-key-desktop_theme_toggle {{
            display: none !important;
        }}

        .st-key-mobile_header_controls {{
            display: block !important;
            width: 100%;
            margin: 0 !important;
            padding: 0 !important;
        }}

        /* Keep the logo on the left on mobile, with the controls alongside it. */
        div[data-testid="stHorizontalBlock"]:has(.st-key-mobile_header_controls) {{
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 4px !important;
            width: 100% !important;
        }}

        div[data-testid="stHorizontalBlock"]:has(.st-key-mobile_header_controls) > [data-testid="column"]:first-child {{
            flex: 0 0 65% !important;
            width: 65% !important;
            min-width: 0 !important;
        }}

        div[data-testid="stHorizontalBlock"]:has(.st-key-mobile_header_controls) > [data-testid="column"]:last-child {{
            flex: 0 0 35% !important;
            width: 35% !important;
            min-width: 0 !important;
        }}

        .st-key-mobile_header_controls {{
            width: fit-content !important;
            max-width: 100% !important;
        }}

        .st-key-mobile_header_controls [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: flex-start !important;
            column-gap: 4px !important;
            row-gap: 0 !important;
            width: max-content !important;
            max-width: max-content !important;
            margin: 0 !important;
        }}

        .st-key-mobile_header_controls [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            flex: 0 0 42px !important;
            width: 42px !important;
            max-width: 42px !important;
            min-width: 42px !important;
            padding: 0 !important;
        }}

        .st-key-mobile_header_controls [data-testid="stHorizontalBlock"] > [data-testid="column"] > div {{
            width: 42px !important;
            min-width: 42px !important;
            max-width: 42px !important;
        }}

        .block-container {{
            padding-top: 0.05rem !important;
            padding-left: 1rem;
            padding-right: 1rem;
        }}

        /* Keep the first page section close to the mobile header. */
        .block-container [data-testid="stVerticalBlock"] {{
            gap: 0.12rem !important;
        }}

        .st-key-mobile_header_controls + div {{
            margin-top: 0 !important;
        }}

        .st-key-mobile_header_controls {{
            margin: 0 !important;
            padding: 0 !important;
        }}

        .hero {{
            min-height: 400px;
            padding: 28px;
        }}

        .hero h1 {{
            font-size: 39px;
        }}

        .section-heading {{
            font-size: 28px;
        }}

        .zomar-logo-link {{
            margin-left: 0 !important;
            margin-right: 0 !important;
            max-width: 100%;
        }}

        .logo-container {{
            width: 220px;
            height: 100px;
            max-width: 100%;
            justify-content: flex-start;
            margin-left: 0 !important;
            overflow: hidden;
        }}

        .logo-container img {{
            width: 220px;
            height: 100px;
            max-width: 100%;
            object-fit: contain;
            object-position: left center;
            transform: translateX(-34px);
        }}

        .zomar-menu-panel {{
            left: 0;
            right: auto;
        }}

        .st-key-mobile_header_controls {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
    }}

    </style>
    """
)

# =========================================================
# 8. HELPER FUNCTIONS
# =========================================================

def format_price(price):
    return f"₦{price:,.0f}"


def navigate(page):
    st.session_state.page = page
    st.query_params["zomar_page"] = page
    st.rerun()


def get_property(property_id):

    for item in properties:

        if item["id"] == property_id:
            return item

    return None


def page_heading(title, subtitle):

    st.html(
        f"""
        <div style="margin:20px 0 28px;">
            <div class="section-heading">
                {escape(title)}
            </div>

            <div class="section-subtitle">
                {escape(subtitle)}
            </div>
        </div>
        """
    )


def location_icon():

    return """
    <svg class="location-icon" viewBox="0 0 24 24"
         xmlns="http://www.w3.org/2000/svg">
        <path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/>
        <circle cx="12" cy="10" r="2.5"/>
    </svg>
    """



def property_status_label(item):
    if item["status"] == "Shortlet":
        return f"Shortlet · {item.get('booking_status', 'Available')}"
    return item["status"]


def display_property_image(image_value, **kwargs):
    if isinstance(image_value, str) and image_value.startswith("data:image/"):
        try:
            encoded = image_value.split(",", 1)[1]
            st.image(base64.b64decode(encoded), **kwargs)
            return
        except Exception:
            st.warning("This uploaded property image could not be displayed.")
            return
    st.image(image_value, **kwargs)


def configured_owner_credentials():
    username = os.getenv("ZOMAR_OWNER_USERNAME")
    password = os.getenv("ZOMAR_OWNER_PASSWORD")
    try:
        owner_settings = st.secrets.get("owner", {})
        username = owner_settings.get("username", username)
        password = owner_settings.get("password", password)
    except Exception:
        pass
    return username, password


def password_digest(password, salt=None):
    salt = salt or pysecrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 310000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password, stored_hash):
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 310000
    ).hex()
    return hmac.compare_digest(actual, expected)


def find_admin_user(username):
    with get_db_connection() as connection:
        return connection.execute(
            "SELECT * FROM admin_users WHERE username = ? COLLATE NOCASE",
            (username.strip(),)
        ).fetchone()


def create_admin_user(full_name, email, username, password):
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO admin_users
            (full_name, email, username, password_hash)
            VALUES (?, ?, ?, ?)
            """,
            (
                full_name.strip(), email.strip().lower(), username.strip(),
                password_digest(password)
            )
        )
        connection.commit()


def reset_admin_user_password(user_id, new_password):
    with get_db_connection() as connection:
        connection.execute(
            "UPDATE admin_users SET password_hash = ? WHERE id = ?",
            (password_digest(new_password), user_id)
        )
        connection.commit()


def set_admin_user_active(user_id, active):
    with get_db_connection() as connection:
        connection.execute(
            "UPDATE admin_users SET is_active = ? WHERE id = ?",
            (1 if active else 0, user_id)
        )
        connection.commit()


def list_admin_users():
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT id, full_name, email, username, is_active, created_at
            FROM admin_users ORDER BY created_at DESC
            """
        ).fetchall()


def property_card(item):

    st.html(
        f"""
        <div class="property-card">

            <div class="property-image-wrap">
                <img
                    class="property-image"
                    src="{escape(item['image'], quote=True)}"
                    alt="{escape(item['name'], quote=True)}"
                >
            </div>

            <div class="property-info">

                <div class="property-status">
                    {escape(property_status_label(item))}
                </div>

                <div class="property-name">
                    {escape(item['name'])}
                </div>

                <div class="property-location">
                    {location_icon()}
                    <span>{escape(item['location'])}</span>
                </div>

                <div class="property-price">
                    {format_price(item['price'])}
                </div>

                <div class="property-meta">
                    <span>{item['bedrooms']} Bedrooms</span>
                    <span>{item['bathrooms']} Bathrooms</span>
                    <span>{escape(item['area'])}</span>
                </div>

            </div>
        </div>
        """
    )

    if st.button(
        "View Property",
        key=f"view_{item['id']}",
        use_container_width=True
    ):

        st.session_state.selected_property = item["id"]
        navigate("Property Details")


def filtered_properties():

    search = st.session_state.get(
        "search_query", ""
    ).lower()

    selected_type = st.session_state.get(
        "filter_type", "All"
    )

    selected_status = st.session_state.get(
        "filter_status", "All"
    )

    results = []

    for item in properties:

        matches_search = (
            search in item["name"].lower()
            or search in item["location"].lower()
        )

        matches_type = (
            selected_type == "All"
            or item["type"] == selected_type
        )

        matches_status = (
            selected_status == "All"
            or item["status"] == selected_status
        )

        if matches_search and matches_type and matches_status:
            results.append(item)

    return results


# =========================================================
# 9. WEBSITE HEADER
# Desktop and mobile: logo left, with mobile controls beside it.
# =========================================================

header_left, header_right = st.columns(
    [3, 1.35],
    vertical_alignment="center"
)

with header_left:
    st.html(logo_html)

with header_right:
    # Mobile: menu trigger and theme toggle share one row.
    with st.container(key="mobile_header_controls"):
        mobile_menu_col, mobile_theme_col = st.columns(
            [0.1, 0.1],
            gap="small",
            vertical_alignment="center"
        )

        with mobile_menu_col:
            # Native HTML details keeps the dropdown compact. Links navigate
            # in the same tab, so the dropdown closes as the app reruns.
            st.html(
                """
                <details class="zomar-mobile-menu">
                    <summary aria-label="Open navigation menu">☰</summary>
                    <nav class="zomar-menu-panel" aria-label="Main navigation">
                        <a href="?zomar_page=Home" target="_self">Home</a>
                        <a href="?zomar_page=Properties" target="_self">Properties</a>
                        <a href="?zomar_page=About%20Us" target="_self">About Us</a>
                        <a href="?zomar_page=Contact%20Us" target="_self">Contact Us</a>
                    </nav>
                </details>
                """
            )

        with mobile_theme_col:
            mobile_theme_icon = "☀" if st.session_state.theme == "Dark" else "☾"
            if st.button(
                mobile_theme_icon,
                key="mobile_theme_toggle",
                help="Switch between light and dark mode"
            ):
                st.session_state.theme = (
                    "Dark" if st.session_state.theme == "Light" else "Light"
                )
                st.rerun()

    # Desktop theme control; hidden on mobile by the responsive CSS.
    desktop_theme_icon = "☀" if st.session_state.theme == "Dark" else "☾"
    if st.button(
        desktop_theme_icon,
        key="desktop_theme_toggle",
        help="Switch between light and dark mode"
    ):
        st.session_state.theme = (
            "Dark" if st.session_state.theme == "Light" else "Light"
        )
        st.rerun()


# =========================================================
# 10. NAVIGATION
# =========================================================

with st.container(key="desktop_navigation"):

    nav_cols = st.columns([1, 1, 1, 1, 4])

    with nav_cols[0]:

        if st.button(
            "Home",
            key="nav_home",
            use_container_width=True
        ):
            navigate("Home")

    with nav_cols[1]:

        if st.button(
            "Properties",
            key="nav_properties",
            use_container_width=True
        ):
            navigate("Properties")

    with nav_cols[2]:

        if st.button(
            "About Us",
            key="nav_about",
            use_container_width=True
        ):
            navigate("About Us")

    with nav_cols[3]:

        if st.button(
            "Contact Us",
            key="nav_contact",
            use_container_width=True
        ):
            navigate("Contact Us")


# The desktop navigation block above is intentionally hidden on phones.
# The compact hamburger popover in the header is shown instead.

st.html(
    f"""
    <div style="
        height:1px;
        background:{BORDER};
        margin:0;
    "></div>
    """
)



# =========================================================
# 11. HOME PAGE
# =========================================================

if st.session_state.page == "Home":

    st.html(
        """
        <div class="hero">

            <div class="hero-content">

                <div class="hero-eyebrow">
                    FIND A PLACE TO CALL HOME
                </div>

                <h1>
                    Where your next chapter begins.
                </h1>

                <p>
                    Discover thoughtfully selected properties and
                    find a space that reflects the way you want to live.
                    Your next home starts here.
                </p>

            </div>

        </div>
        """
    )

    st.write("")

    if st.button(
        "Explore Properties",
        key="hero_explore"
    ):
        navigate("Properties")

    st.write("")
    st.write("")

    page_heading(
        "Featured Properties",
        "Explore a selection of properties worth considering."
    )

    featured = properties[:3]

    cols = st.columns(3)

    for index, item in enumerate(featured):

        with cols[index]:
            property_card(item)

    st.write("")
    st.write("")

    center_cols = st.columns([1, 1, 1])

    with center_cols[1]:

        if st.button(
            "Explore All Properties",
            key="explore_properties",
            use_container_width=True
        ):
            navigate("Properties")

    st.write("")
    st.write("")

    st.html(
        """
        <div class="content-panel">

            <div class="section-heading">
                A better way to find your next home.
            </div>

            <p style="
                color:var(--muted);
                line-height:1.8;
            ">
                Finding the right property should be a straightforward
                experience. We bring property discovery and helpful
                guidance together, making it easier to explore your
                options and take the next step.
            </p>

        </div>
        """
    )


# =========================================================
# 12. PROPERTIES PAGE
# =========================================================

elif st.session_state.page == "Properties":

    page_heading(
        "Explore Properties",
        "Browse available properties and find a place that suits you."
    )

    search_cols = st.columns([2, 1, 1])

    with search_cols[0]:

        st.text_input(
            "Search",
            placeholder="Search by property or location...",
            key="search_query"
        )

    with search_cols[1]:

        st.selectbox(
            "Property type",
            [
                "All",
                "Apartment",
                "Duplex",
                "Detached House",
                "Villa"
            ],
            key="filter_type"
        )

    with search_cols[2]:

        st.selectbox(
            "Availability",
            [
                "All",
                "For Sale",
                "For Rent",
                "Shortlet"
            ],
            key="filter_status"
        )

    st.write("")

    results = filtered_properties()

    st.caption(
        f"Showing {len(results)} properties"
    )

    if results:

        for start in range(0, len(results), 3):

            cols = st.columns(3)

            for index, item in enumerate(
                results[start:start + 3]
            ):

                with cols[index]:
                    property_card(item)

    else:

        st.info(
            "No properties match your search. "
            "Try changing your filters."
        )


# =========================================================
# 13. PROPERTY DETAILS PAGE
# =========================================================

elif st.session_state.page == "Property Details":

    selected = get_property(
        st.session_state.selected_property
    )

    if selected:

        if st.button(
            "← Back to Properties",
            key="back_to_properties"
        ):
            navigate("Properties")

        st.write("")

        gallery_images = selected.get("images") or []
        if gallery_images:
            display_property_image(selected["image"], use_container_width=True)
            if len(gallery_images) > 1:
                st.markdown("#### More photos")
                for start in range(0, len(gallery_images[1:]), 3):
                    photo_cols = st.columns(3)
                    for col, photo in zip(photo_cols, gallery_images[1:][start:start + 3]):
                        with col:
                            display_property_image(photo, use_container_width=True)
        else:
            display_property_image(selected["image"], use_container_width=True)

        st.write("")

        detail_cols = st.columns([1.5, 1])

        with detail_cols[0]:

            st.html(
                f"""
                <div class="section-heading">
                    {escape(selected['name'])}
                </div>

                <div class="property-location">
                    {location_icon()}
                    <span>{escape(selected['location'])}</span>
                </div>

                <div class="property-status">
                    {escape(property_status_label(selected))}
                </div>

                <div class="property-price"
                     style="font-size:27px;">
                    {format_price(selected['price'])}
                </div>
                """
            )

            st.markdown("### Property Overview")

            st.write(selected["description"])

            st.markdown("### Property Features")

            feature_cols = st.columns(3)

            feature_cols[0].metric(
                "Bedrooms",
                selected["bedrooms"]
            )

            feature_cols[1].metric(
                "Bathrooms",
                selected["bathrooms"]
            )

            feature_cols[2].metric(
                "Area",
                selected["area"]
            )

            st.write("")

            st.markdown("### Interested in this property?")

            st.write(
                "Contact our team to enquire about availability "
                "or arrange a viewing."
            )

            if st.button(
                "Enquire About This Property",
                key="property_enquiry",
                use_container_width=True
            ):

                navigate("Contact Us")

        with detail_cols[1]:

            st.html(
                f"""
                <div class="content-panel">

                    <h3>Property Information</h3>

                    <p style="color:var(--muted);">
                        Property type
                    </p>

                    <strong>{escape(selected['type'])}</strong>

                    <hr>

                    <p style="color:var(--muted);">
                        Location
                    </p>

                    <strong>{escape(selected['location'])}</strong>

                    <hr>

                    <p style="color:var(--muted);">
                        Availability
                    </p>

                    <strong>{escape(property_status_label(selected))}</strong>

                    <hr>

                    <p style="color:var(--muted);">
                        Property size
                    </p>

                    <strong>{escape(selected['area'])}</strong>

                </div>
                """
            )

    else:

        st.warning("No property has been selected.")

        if st.button("Return to Properties"):
            navigate("Properties")



# =========================================================
# 14. ADMIN DASHBOARD (LOCAL PROTOTYPE)
# =========================================================

elif st.session_state.page == "Admin":

    page_heading(
        "Private Administration",
        "Authorised company personnel only."
    )

    owner_username, owner_password = configured_owner_credentials()

    if not owner_username or not owner_password:
        st.error("The initial company owner account has not been configured.")
        st.markdown(
            """
            Create `.streamlit/secrets.toml` and add the `[owner]` credentials
            shown in the setup guide. Do not put owner credentials in app.py
            or commit secrets.toml to GitHub.
            """
        )
    elif not st.session_state.admin_authenticated:
        st.markdown("### Secure sign in")
        with st.form("zomar_private_login"):
            entered_username = st.text_input("Username")
            entered_password = st.text_input("Password", type="password")
            sign_in = st.form_submit_button("Sign in", use_container_width=False)

        if sign_in:
            if hmac.compare_digest(entered_username, str(owner_username)):
                if hmac.compare_digest(entered_password, str(owner_password)):
                    st.session_state.admin_authenticated = True
                    st.session_state.auth_role = "owner"
                    st.session_state.auth_username = str(owner_username)
                    st.rerun()
                else:
                    st.error("The username or password is incorrect.")
            else:
                user = find_admin_user(entered_username)
                if user and user["is_active"] and verify_password(
                    entered_password, user["password_hash"]
                ):
                    st.session_state.admin_authenticated = True
                    st.session_state.auth_role = "admin"
                    st.session_state.auth_username = user["username"]
                    st.rerun()
                else:
                    st.error("The username or password is incorrect, or this account is inactive.")

        if st.button("Forgot password?", key="show_password_recovery", type="tertiary"):
            st.session_state.show_forgot_password = not st.session_state.show_forgot_password

        if st.session_state.show_forgot_password:
            with st.container(border=True):
                st.markdown("**Password recovery**")
                st.write(
                    "For security, administrator password resets are handled by the "
                    "Company Owner. Contact the owner using your registered company "
                    "email address and request a password reset. The owner can issue "
                    "a new temporary password from the Owner Dashboard."
                )
                st.caption(
                    "If you are the Company Owner and have forgotten your password, "
                    "update the owner password in your private Streamlit secrets settings "
                    "and restart the application. There is no public owner password reset."
                )

    else:
        role = st.session_state.auth_role
        username = st.session_state.auth_username

        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.success(
                "Signed in as Company Owner." if role == "owner"
                else f"Signed in as Administrator: {username}"
            )
        with header_cols[1]:
            if st.button("Sign out", key="private_sign_out"):
                st.session_state.admin_authenticated = False
                st.session_state.auth_role = None
                st.session_state.auth_username = None
                st.rerun()

        properties = load_properties()
        total_count = len(properties)
        sale_count = sum(p["status"] == "For Sale" for p in properties)
        rent_count = sum(p["status"] == "For Rent" for p in properties)
        shortlet_count = sum(p["status"] == "Shortlet" for p in properties)
        booked_count = sum(
            p["status"] == "Shortlet"
            and p.get("booking_status") == "Fully Booked"
            for p in properties
        )

        metrics = st.columns(5)
        metrics[0].metric("Total listings", total_count)
        metrics[1].metric("For sale", sale_count)
        metrics[2].metric("For rent", rent_count)
        metrics[3].metric("Shortlets", shortlet_count)
        metrics[4].metric("Fully booked", booked_count)

        if role == "owner":
            st.divider()
            st.markdown("### Create administrator account")
            st.caption(
                "Only the company owner can create administrator accounts. "
                "Give the new administrator their username and temporary password privately."
            )
            with st.form("create_admin_account", clear_on_submit=True):
                new_full_name = st.text_input("Administrator's full name")
                new_email = st.text_input("Company email address")
                new_username = st.text_input("Username")
                new_password = st.text_input(
                    "Temporary password (minimum 12 characters)",
                    type="password"
                )
                create_account = st.form_submit_button(
                    "Create administrator", use_container_width=True
                )

            if create_account:
                if not all([
                    new_full_name.strip(), new_email.strip(),
                    new_username.strip(), new_password
                ]):
                    st.error("Complete all administrator account fields.")
                elif "@" not in new_email or "." not in new_email.rsplit("@", 1)[-1]:
                    st.error("Enter a valid email address.")
                elif len(new_password) < 12:
                    st.error("Use a temporary password with at least 12 characters.")
                else:
                    try:
                        create_admin_user(
                            new_full_name, new_email, new_username, new_password
                        )
                        st.success(
                            f"Administrator account created for {new_full_name}. "
                            "Share the username and temporary password privately."
                        )
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("That email address or username is already registered.")

            st.divider()
            st.markdown("### Administrator accounts")
            admin_users = list_admin_users()
            if not admin_users:
                st.info("No administrator accounts have been created yet.")
            for user in admin_users:
                with st.container(border=True):
                    info, action = st.columns([3, 1])
                    with info:
                        st.markdown(f"**{user['full_name']}**")
                        st.caption(
                            f"{user['email']} · Username: {user['username']} · "
                            f"{'Active' if user['is_active'] else 'Inactive'}"
                        )
                    with action:
                        button_label = "Deactivate" if user["is_active"] else "Activate"
                        if st.button(
                            button_label, key=f"toggle_admin_{user['id']}",
                            use_container_width=True
                        ):
                            set_admin_user_active(
                                user["id"], not bool(user["is_active"])
                            )
                            st.rerun()
                    with st.expander("Reset this administrator's password"):
                        with st.form(f"reset_admin_password_{user['id']}"):
                            reset_password = st.text_input(
                                "New temporary password (minimum 12 characters)",
                                type="password", key=f"reset_password_value_{user['id']}"
                            )
                            reset_submitted = st.form_submit_button(
                                "Save new password", use_container_width=False
                            )
                        if reset_submitted:
                            if len(reset_password) < 12:
                                st.error("Use a password with at least 12 characters.")
                            else:
                                reset_admin_user_password(user["id"], reset_password)
                                st.success(
                                    "Password reset. Share the new temporary password "
                                    "with the administrator privately."
                                )

        st.divider()
        st.markdown("### Upload a property")
        with st.form("zomar_add_property", clear_on_submit=True):
            name = st.text_input("Property name")
            location = st.text_input("Location")
            form_cols = st.columns(2)
            with form_cols[0]:
                price = st.number_input("Price (NGN)", min_value=0, step=100000, value=0)
                property_type = st.selectbox(
                    "Property type",
                    ["Apartment", "Duplex", "Detached House", "Villa", "Land", "Other"]
                )
                availability = st.selectbox(
                    "Availability", ["For Sale", "For Rent", "Shortlet"]
                )
            with form_cols[1]:
                bedrooms = st.number_input("Bedrooms", min_value=0, max_value=50, value=0)
                bathrooms = st.number_input("Bathrooms", min_value=0, max_value=50, value=0)
                area = st.text_input("Property area", placeholder="e.g. 220 sqm")
            description = st.text_area("Description")
            image_uploads = st.file_uploader(
                "Upload property photos (JPG, PNG or WEBP; up to 5 MB per image)",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                help="You can select more than 12 images. The first image is used as the main listing photo."
            )
            image_url = st.text_input("Or provide a main image URL", placeholder="https://...")
            submitted_property = st.form_submit_button("Add property", use_container_width=True)

            if submitted_property:
                if not name.strip() or not location.strip():
                    st.error("Enter both a property name and location.")
                elif price <= 0 or not description.strip():
                    st.error("Enter a price greater than zero and a description.")
                elif not image_uploads and not image_url.strip():
                    st.error("Upload at least one property photo or provide a main image URL.")
                elif any(len(upload.getvalue()) > 5 * 1024 * 1024 for upload in image_uploads):
                    st.error("One or more images are larger than 5 MB. Reduce their size and try again.")
                else:
                    gallery_values = [
                        f"data:{upload.type};base64," + base64.b64encode(upload.getvalue()).decode("ascii")
                        for upload in image_uploads
                    ]
                    image_value = gallery_values[0] if gallery_values else image_url.strip()
                    if not gallery_values and image_url.strip():
                        gallery_values = [image_url.strip()]
                    insert_property({
                        "name": name.strip(), "location": location.strip(),
                        "price": float(price), "type": property_type,
                        "status": availability, "booking_status": "Available",
                        "bedrooms": int(bedrooms), "bathrooms": int(bathrooms),
                        "area": area.strip(), "image": image_value,
                        "images": gallery_values,
                        "description": description.strip()
                    })
                    st.success(f"{name.strip()} has been added.")
                    st.rerun()

        st.divider()
        st.markdown("### Manage existing properties")
        current_inventory = load_properties()
        if current_inventory:
            with st.expander("Remove the entire property inventory"):
                st.warning(
                    "This permanently deletes every property currently stored, including demo listings. "
                    "This action cannot be undone."
                )
                confirm_all = st.checkbox(
                    "I understand that all property listings will be permanently deleted.",
                    key="confirm_delete_all_properties"
                )
                if st.button(
                    "Delete all properties", key="delete_all_properties",
                    type="secondary", disabled=not confirm_all
                ):
                    remove_all_properties()
                    st.success("All property listings have been deleted.")
                    st.rerun()
        for item in current_inventory:
            with st.container(border=True):
                row = st.columns([3, 1.2, 1.3])
                with row[0]:
                    st.markdown(f"**{item['name']}**")
                    st.caption(
                        f"{item['location']} · {item['type']} · "
                        f"{property_status_label(item)}"
                    )
                    st.write(format_price(item["price"]))
                with row[1]:
                    if item["status"] == "Shortlet":
                        booking_state = st.selectbox(
                            "Shortlet status", ["Available", "Fully Booked"],
                            index=1 if item.get("booking_status") == "Fully Booked" else 0,
                            key=f"booking_state_{item['id']}"
                        )
                        if st.button("Save status", key=f"save_booking_{item['id']}"):
                            update_shortlet_booking(item["id"], booking_state)
                            st.rerun()
                with row[2]:
                    delete_label = (
                        "Mark sold & remove" if item["status"] == "For Sale"
                        else "Mark rented & remove" if item["status"] == "For Rent"
                        else "Delete listing"
                    )
                    confirmed = st.checkbox("Confirm", key=f"confirm_delete_{item['id']}")
                    if st.button(
                        delete_label, key=f"delete_property_{item['id']}",
                        disabled=not confirmed, use_container_width=True
                    ):
                        remove_property(item["id"])
                        st.rerun()

        st.caption(
            "Property deletion is permanent. The demo listings are seeded only once and will not return "
            "after the inventory is cleared. No transaction history or audit log is retained."
        )


# =========================================================
# 15. ABOUT US PAGE
# =========================================================

elif st.session_state.page == "About Us":

    page_heading(
        "About Zomar Homes",
        "Making property discovery a more considered experience."
    )

    st.html(
        """
        <div class="content-panel">

            <h2>Helping you find a place that feels right.</h2>

            <p style="
                color:var(--muted);
                line-height:1.8;
            ">
                At Zomar Homes & Property, we believe finding a property
                is about more than selecting a building. It is about
                finding a space that supports your lifestyle, ambitions
                and plans for the future.
            </p>

            <p style="
                color:var(--muted);
                line-height:1.8;
            ">
                Our aim is to make property discovery clearer and more
                accessible by presenting property options in a simple,
                organised and helpful way.
            </p>

        </div>
        """
    )

    st.write("")
    st.write("")

    page_heading(
        "What matters to us",
        "The principles behind the Zomar Homes experience."
    )

    cols = st.columns(3)

    with cols[0]:

        st.html(
            """
            <div class="content-panel">
                <h3>Transparency</h3>
                <p style="color:var(--muted);">
                    Clear property information to help people make
                    informed decisions.
                </p>
            </div>
            """
        )

    with cols[1]:

        st.html(
            """
            <div class="content-panel">
                <h3>Quality</h3>
                <p style="color:var(--muted);">
                    A considered approach to property presentation
                    and customer experience.
                </p>
            </div>
            """
        )

    with cols[2]:

        st.html(
            """
            <div class="content-panel">
                <h3>People First</h3>
                <p style="color:var(--muted);">
                    A property journey designed around the needs
                    of the people using it.
                </p>
            </div>
            """
        )


# =========================================================
# 15. CONTACT US PAGE
# =========================================================

elif st.session_state.page == "Contact Us":

    page_heading(
        "Get in Touch",
        "Have a question or found a property you like? Send us an enquiry."
    )

    contact_cols = st.columns([1.1, 0.9])

    with contact_cols[0]:

        # No unnecessary panel around the enquiry form.

        st.markdown("### Send an Enquiry")

        with st.form("contact_form"):

            full_name = st.text_input(
                "Full name",
                placeholder="Enter your full name"
            )

            email = st.text_input(
                "Email address",
                placeholder="Enter your email address"
            )

            phone = st.text_input(
                "Phone number",
                placeholder="Enter your phone number"
            )

            subject = st.selectbox(
                "What would you like to discuss?",
                [
                    "General enquiry",
                    "Property purchase",
                    "Property rental",
                    "Property viewing",
                    "Other"
                ]
            )

            message = st.text_area(
                "Your message",
                placeholder="Tell us how we can help...",
                height=130
            )

            submitted = st.form_submit_button(
                "Submit Enquiry",
                use_container_width=True
            )

            if submitted:

                if not full_name.strip():

                    st.error("Please enter your full name.")

                elif not email.strip() or "@" not in email:

                    st.error("Please enter a valid email address.")

                elif not phone.strip():

                    st.error("Please enter your phone number.")

                elif not message.strip():

                    st.error("Please enter a message.")

                else:

                    st.success(
                        "Your enquiry has been validated. "
                        "Email or database integration is required "
                        "before enquiries can be delivered or saved."
                    )

    with contact_cols[1]:

        st.html(
            """
            <div class="content-panel">

                <h3>Contact Information</h3>

                <p style="
                    color:var(--muted);
                    line-height:1.8;
                ">
                    Have a question about a property or need help
                    with your search? Get in touch with our team.
                </p>

                <hr>

                <p><strong>Location</strong></p>

                <p style="color:var(--muted);">
                    Lagos, Nigeria
                </p>

                <hr>

                <p><strong>Email</strong></p>

                <p style="color:var(--muted);">
                    Add your official email address
                </p>

                <hr>

                <p><strong>Phone</strong></p>

                <p style="color:var(--muted);">
                    Add your official phone number
                </p>

            </div>
            """
        )


# =========================================================
# 16. FOOTER
# =========================================================

st.html(
    """
    <div class="footer">

        <h3>
            Zomar <span class="footer-accent">Homes</span>
        </h3>

        <p>
            Find a place that feels like home.
        </p>

        <hr style="border-color:#454545;">

        <p>
            © 2026 Zomar Homes & Property. All rights reserved.
        </p>

        <div style="margin-top:18px; text-align:right;">
            <a href="?zomar_page=Admin" target="_self"
               style="display:inline-block; color:#D8A800; font-size:12px;
                      text-decoration:none; border:1px solid #625321;
                      border-radius:4px; padding:7px 12px;">
                Admin Login
            </a>
        </div>

    </div>
    """
)