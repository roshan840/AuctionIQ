import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sqlite3
from src.utils.logger import logger
from src.config import config, CITY_TO_STATE
from src.database.repository import DatabaseRepository
from src.services.scraper import ScraperService
from src.services.enricher import AIService
from datetime import datetime, timedelta
import hashlib
import time
import math
import json
import base64
from fpdf import FPDF
from typing import Optional, List, Dict, Any
from src.utils.auth import create_access_token, decode_access_token

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AuctionIQ — Bank Auction Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ─── Theme Configuration ─────────────────────────────────────────────────────
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'System'

# Render theme selector in sidebar early so styles apply instantly
st.sidebar.markdown("**🎨 Appearance**")
theme_mode = st.sidebar.radio("Theme", ["System", "Light", "Dark"], horizontal=True, label_visibility="collapsed")
st.session_state.theme_mode = theme_mode
st.sidebar.markdown('<hr style="border:none;border-top:1px solid var(--border-light);margin:12px 0;">', unsafe_allow_html=True)

# ─── Auth Session State ──────────────────────────────────────────────────────
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

def login_form(repo):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align:center; padding: 20px 0;">
                <h1 style="color:#FF385C; margin-bottom:0;">🏛️ AuctionIQ</h1>
                <p style="color:var(--text-muted); font-size:0.9em;">Premium Auction Intelligence</p>
            </div>
        """, unsafe_allow_html=True)
        
        auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with auth_tab1:
            with st.container(border=True):
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Sign In", use_container_width=True)
                    if submitted:
                        user = repo.verify_user(username.strip(), password)
                        if user:
                            # Generate JWT Token
                            token_data = {
                                "sub": user['username'],
                                "role": user['role'],
                                "cities": user['allowed_cities'],
                                "columns": user['allowed_columns']
                            }
                            token = create_access_token(token_data)
                            st.session_state.token = token
                            st.session_state.authenticated = True
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
        
        with auth_tab2:
            with st.container(border=True):
                with st.form("register_form"):
                    reg_name = st.text_input("Username")
                    reg_pass = st.text_input("Password", type="password")
                    reg_pass_conf = st.text_input("Confirm Password", type="password")
                    
                    st.info("💡 New accounts are pending admin approval for data access.")
                    
                    if st.form_submit_button("Create Account", use_container_width=True):
                        if not reg_name or not reg_pass:
                            st.error("Please fill all fields")
                        elif reg_pass != reg_pass_conf:
                            st.error("Passwords do not match")
                        else:
                            # Restricted default permissions
                            default_cols = "title,bank_name,reserve_price,city,area_locality,auction_start_date"
                            success = repo.save_user({
                                'username': reg_name.strip(),
                                'password': reg_pass,
                                'role': 'User',
                                'allowed_cities': '', # No cities by default
                                'allowed_columns': default_cols
                            })
                            if success:
                                st.success("Registration successful! Please login.")
                            else:
                                st.error("Username already exists or database error")

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.token = None
    st.rerun()

if theme_mode == "Dark":
    root_css = """
    :root {
        --primary-color: #FF385C;
        --background-color: #020617;
        --secondary-background-color: #1e293b;
        --text-color: #e5e7eb;
        --border-color: rgba(255, 56, 92, 0.45);
        --font: 'Inter', sans-serif;
        --bg-main: #020617;
        --bg-card: #020617;
        --text-main: #e5e7eb;
        --text-muted: #9ca3af;
        --border-alpha: rgba(255, 56, 92, 0.45);
        --border-light: rgba(255, 56, 92, 0.25);
        --card-shadow: 0 18px 45px rgba(0,0,0,0.55);
        --ring-bg: #020617;
        --ring-border: #1f2937;
    }
    """
    plotly_template = "plotly_dark"
elif theme_mode == "Light":
    root_css = """
    :root {
        --primary-color: #FF385C;
        --background-color: #f8fafc;
        --secondary-background-color: #ffffff;
        --text-color: #0f172a;
        --border-color: rgba(255, 56, 92, 0.3);
        --font: 'Inter', sans-serif;
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-alpha: rgba(255, 56, 92, 0.3);
        --border-light: rgba(255, 56, 92, 0.15);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.05);
        --ring-bg: #f1f5f9;
        --ring-border: #e2e8f0;
    }
    """
    plotly_template = "plotly_white"
else:
    root_css = """
    :root {
        --primary-color: #FF385C;
        --background-color: #f8fafc;
        --secondary-background-color: #ffffff;
        --text-color: #0f172a;
        --border-color: rgba(255, 56, 92, 0.3);
        --font: 'Inter', sans-serif;
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-alpha: rgba(255, 56, 92, 0.3);
        --border-light: rgba(255, 56, 92, 0.15);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.05);
        --ring-bg: #f1f5f9;
        --ring-border: #e2e8f0;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --primary-color: #FF385C;
            --background-color: #020617;
            --secondary-background-color: #1e293b;
            --text-color: #e5e7eb;
            --border-color: rgba(255, 56, 92, 0.45);
            --font: 'Inter', sans-serif;
            --bg-main: #020617;
            --bg-card: #020617;
            --text-main: #e5e7eb;
            --text-muted: #9ca3af;
            --border-alpha: rgba(255, 56, 92, 0.45);
            --border-light: rgba(255, 56, 92, 0.25);
            --card-shadow: 0 18px 45px rgba(0,0,0,0.55);
            --ring-bg: #020617;
            --ring-border: #1f2937;
        }
    }
    """
    plotly_template = None

def render_plotly(col, fig):
    """Render Plotly charts with theme-aware text colors."""
    if theme_mode == "System":
        col.plotly_chart(fig, theme="streamlit", width="stretch")
        return

    # Explicit styling for Light / Dark to keep labels readable
    if theme_mode == "Dark":
        text_color = "#e5e7eb"
        grid_color = "rgba(148, 163, 184, 0.35)"
    else:
        text_color = "#0f172a"
        grid_color = "rgba(148, 163, 184, 0.45)"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color),
        title_font=dict(color=text_color),
        legend=dict(font=dict(color=text_color)),
        xaxis=dict(color=text_color, gridcolor=grid_color),
        yaxis=dict(color=text_color, gridcolor=grid_color),
    )

    col.plotly_chart(fig, theme=None, width="stretch")

# ─── Premium CSS Injection ───────────────────────────────────────────────────

st.markdown('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">', unsafe_allow_html=True)

MAIN_CSS = f"""

<style>
{root_css}
* {{ box-sizing: border-box; }}
html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', sans-serif !important;
    background: var(--bg-main) !important;
    color: var(--text-main) !important;
}}
[data-testid="stHeader"] {{
    background: var(--bg-main) !important;
    color: var(--text-main) !important;
    border-bottom: 1px solid var(--border-light) !important;
}}
[data-testid="stHeader"] * {{
    color: var(--text-main) !important;
}}
[data-testid="stSidebar"] {{
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border-light) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--text-muted) !important; }}
[data-testid="stSidebar"] .stButton > button {{
    background: #FF385C !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    line-height: 1.2 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    width: 100% !important;
    padding: 0.6rem 1rem !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}}
[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stDownloadButton > button * {{
    color: #ffffff !important;
}}
[data-testid="stSidebar"] .stButton > button:disabled {{
    background: #4b5563 !important;
    color: #e5e7eb !important;
    opacity: 0.9 !important;
    cursor: not-allowed !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(255,56,92,0.3) !important;
}}
[data-testid="stMain"] {{ background: var(--bg-main) !important; }}
.block-container {{ padding: 1.5rem 2rem !important; max-width: 1600px !important; }}
[data-testid="stTabs"] [role="tablist"] {{
    background: var(--bg-card) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--border-alpha) !important;
}}
[data-testid="stTabs"] [role="tab"] {{
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    line-height: 1.2 !important;
    color: var(--text-muted) !important;
    padding: 0.45rem 0.9rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: #FF385C !important;
    color: white !important;
}}
[data-testid="stMain"] .stButton > button {{
    background: #FF385C !important;
    border: none !important;
    border-radius: 999px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    line-height: 1.2 !important;
    padding: 0.5rem 1.3rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}}
[data-testid="stMain"] .stButton > button:disabled {{
    background: #4b5563 !important;
    color: #e5e7eb !important;
    opacity: 0.9 !important;
    cursor: not-allowed !important;
}}
[data-testid="stMain"] .stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(255,56,92,0.3) !important;
}}
[data-testid="stMain"] .stDownloadButton > button,
.stDownloadButton > button {{
    background: #111827 !important;
    color: #f9fafb !important;
    border-radius: 999px !important;
    border: none !important;
    font-weight: 600 !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border-alpha) !important;
    border-radius: 8px !important;
    color: var(--text-main) !important;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: #FF385C !important;
    box-shadow: 0 0 0 2px var(--border-light) !important;
}}
[data-testid="stToggle"] span {{ color: var(--text-muted) !important; }}
[data-testid="stSlider"] > div > div > div > div {{
    background: #FF385C !important;
}}
[data-testid="stAlert"] {{
    border-radius: 10px !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border-alpha) !important;
    color: var(--text-main) !important;
}}
[data-testid="stAlert"] p, [data-testid="stAlert"] span {{
    color: var(--text-main) !important;
}}
[data-testid="stSpinner"] > div {{ border-color: #FF385C !important; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg-main); }}
::-webkit-scrollbar-thumb {{ background: #FF385C; border-radius: 3px; }}
[data-testid="stMetric"] {{ display: none; }}
[data-testid="stDataFrame"] {{ background: var(--bg-card) !important; }}

/* Premium Property Card Hover */
.prop-card {{
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
.prop-card:hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 20px 40px rgba(0,0,0,0.12), 0 0 0 1px rgba(255,56,92,0.3) !important;
    border-color: rgba(255,56,92,0.4) !important;
}}
</style>
"""
st.markdown(MAIN_CSS, unsafe_allow_html=True)


# ─── Services ────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_services():
    repo = DatabaseRepository()
    scraper = ScraperService(repo)
    enricher = AIService()
    return repo, scraper, enricher

repo, scraper, enricher = get_services()
if "cloudflare_cookie" not in st.session_state:
    st.session_state.cloudflare_cookie = ""
if st.session_state.cloudflare_cookie:
    scraper.set_cloudflare_cookie(st.session_state.cloudflare_cookie)

# ─── Columns Map ─────────────────────────────────────────────────────────────
COLUMNS_MAP = {
    "Property Title": "title",
    "Bank Name": "bank_name",
    "Reserve Price": "reserve_price",
    "EMD": "emd",
    "Area (Sqft)": "area_sqft",
    "Rate/Sqft": "rate_sqft",
    "City": "city",
    "Locality": "area_locality",
    "State": "state",
    "Auction Start": "auction_start_date",
    "Auction End": "auction_end_time",
    "Borrower": "borrower_name",
    "Notice URL": "notice_image_url",
    "Description": "description",
    "Market Rate": "market_rate_sqft",
    "Discount %": "discount_rate_percent",
    "Village": "village",
    "Property Type": "property_type",
    "Floor": "floor",
    "Society": "society_name",
    "Investment Score": "investment_score",
    "Risk Rating": "risk_rating",
    "Possession": "possession_status"
}
REVERSE_MAP = {v: k for k, v in COLUMNS_MAP.items()}

# ─── Export Functions ────────────────────────────────────────────────────────
def export_pdf(df, allowed_cols):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "AuctionIQ Intelligence Report", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%d %b %Y')}", ln=True, align='C')
    pdf.ln(10)

    # Use a subset of columns for PDF to keep it readable
    disp_cols = [c for c in allowed_cols if c in REVERSE_MAP]
    pdf.set_font("helvetica", "B", 8)
    
    col_width = 190 / max(1, len(disp_cols[:6]))
    for col in disp_cols[:6]:
        pdf.cell(col_width, 10, REVERSE_MAP[col][:15], border=1)
    pdf.ln()

    pdf.set_font("helvetica", "", 7)
    for _, row in df.head(50).iterrows(): # Limit rows for sample
        for col in disp_cols[:6]:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            pdf.cell(col_width, 8, val[:25], border=1)
        pdf.ln()
    
    return pdf.output()

# ─── Auth Session State & JWT Hydration ──────────────────────────────────────
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'token' not in st.session_state:
    st.session_state.token = None

# JWT Session Hydration
if st.session_state.token and not st.session_state.authenticated:
    decoded = decode_access_token(st.session_state.token)
    if decoded:
        # Re-fetch or reconstruct user from token
        st.session_state.authenticated = True
        # Note: We reconstruct basic info from token, but could re-query DB for fresh perms
        st.session_state.user = {
            "username": decoded['sub'],
            "role": decoded['role'],
            "allowed_cities": decoded['cities'],
            "allowed_columns": decoded['columns']
        }

# ─── Check Auth ──────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    login_form(repo)
    st.stop()

current_user = st.session_state.user
is_admin = current_user['role'] == 'Admin'

# Sidebar Branding & User Info
st.sidebar.markdown(f"""
<div style="padding:4px 0 12px;text-align:center;">
  <div style="font-size:0.85em;color:var(--text-muted);font-weight:600;">Logged in as:</div>
  <div style="font-size:1.1em;font-weight:700;color:#FF385C;">{current_user['username']} ({current_user['role']})</div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔓 Logout", use_container_width=True):
    logout()


# ─── Date Parsing ────────────────────────────────────────────────────────────
def parse_auction_date(d_str):
    if not d_str or d_str == "N/A":
        return None
    for fmt in ["%d-%m-%Y %I:%M %p", "%d-%m-%Y %H:%M:%S",
                "%d-%m-%Y %H:%M", "%d-%m-%Y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(d_str.strip(), fmt)
        except ValueError:
            continue
    return None

def auction_status_label(row, now):
    """Returns (label, color) for a property row."""
    sd = row.get('parsed_start_date')
    ed = row.get('parsed_end_time')
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if pd.notna(sd) and sd >= today:
        diff = (sd - now).days
        if diff == 0:    return "🔴 TODAY",   "#ef4444"
        elif diff <= 3:  return f"⚡ {diff}d",  "#f59e0b"
        else:            return f"🟢 {diff}d",  "#10b981"
    elif pd.notna(ed) and ed >= now:
        return "🟡 Active",  "#eab308"
    else:
        return "⬛ Ended",   "#475569"


# ─── Data Loading ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Loading auction data…")
def load_data(db_path: str, db_mtime: float):
    try:
        with sqlite3.connect(db_path, timeout=30) as conn:
            df = pd.read_sql_query(
                "SELECT * FROM properties ORDER BY crawled_at DESC", conn
            )
    except Exception as exc:
        logger.error(f"Error loading properties from database: {exc}")
        return pd.DataFrame()

    if df.empty:
        return df

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    df['parsed_start_date'] = df['auction_start_date'].apply(parse_auction_date)
    df['parsed_end_time'] = df['auction_end_time'].apply(parse_auction_date)
    df['crawled_at'] = pd.to_datetime(df['crawled_at'], errors='coerce')

    df['is_active'] = (
        (df['parsed_start_date'] >= today_start) |
        (df['parsed_end_time'] >= now)
    ).fillna(False)

    mask_na = df['parsed_start_date'].isna() & df['parsed_end_time'].isna()
    df.loc[mask_na, 'is_active'] = df.loc[mask_na, 'crawled_at'] >= (now - timedelta(days=7))

    df['state_region'] = df['city'].map(CITY_TO_STATE).fillna('Other')
    return df


def run_enrichment_batches(pending, batch_size: int = 5, on_batch=None) -> int:
    """Enrich pending properties in batches; returns success count."""
    success_count = 0
    total_batches = math.ceil(len(pending) / batch_size) if pending else 0
    for batch_idx, i in enumerate(range(0, len(pending), batch_size), start=1):
        batch = pending[i : i + batch_size]
        if on_batch:
            on_batch(batch_idx, total_batches)
        batch_data = [p.model_dump() for p in batch]
        enriched_results = enricher.enrich_properties_batch(batch_data)
        for prop, enriched_data in zip(batch, enriched_results):
            if not enriched_data:
                continue
            discount = None
            if enriched_data.market_rate_sqft and prop.rate_sqft:
                discount = round(
                    ((enriched_data.market_rate_sqft - prop.rate_sqft)
                     / enriched_data.market_rate_sqft) * 100,
                    2,
                )
            update_payload = enriched_data.model_dump()
            update_payload['discount_rate_percent'] = discount
            if repo.update_enrichment(prop.id, update_payload):
                success_count += 1
    return success_count


DATA_EXPLORER_COLUMNS = [
    "is_active", "investment_score", "risk_rating", "title", "property_type", "asset_category",
    "reserve_price", "discount_rate_percent", "emd", "area_sqft", "rate_sqft", "market_rate_sqft",
    "village", "area_locality", "city", "state", "state_region", "bank_name", "branch_name",
    "borrower_name", "auction_type", "auction_start_date", "auction_end_time",
    "application_submission_date", "possession_status", "contact_details", "description",
    "source_url", "notice_image_url",
]


def prepare_explorer_df(source_df: pd.DataFrame) -> pd.DataFrame:
    """Build a safe dataframe for Streamlit table rendering."""
    if source_df.empty:
        return source_df.copy()

    cols = [c for c in DATA_EXPLORER_COLUMNS if c in source_df.columns]
    out = source_df[cols].copy()

    for link_col in ("source_url", "notice_image_url"):
        if link_col in out.columns:
            out[link_col] = out[link_col].where(
                out[link_col].notna() & (out[link_col].astype(str).str.strip() != "N/A"),
                None,
            )

    if "investment_score" in out.columns:
        out["investment_score"] = pd.to_numeric(out["investment_score"], errors="coerce")

    return out


def safe_column_subset(source_df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Return only columns that exist in the dataframe."""
    existing = [c for c in columns if c in source_df.columns]
    return source_df[existing].copy() if existing else source_df.copy()


EXPLORER_COLUMN_CONFIG = {
    "is_active": st.column_config.CheckboxColumn("Active"),
    "investment_score": st.column_config.NumberColumn("Score", format="%d"),
    "risk_rating": st.column_config.TextColumn("Risk"),
    "title": st.column_config.TextColumn("Property Title", width="large"),
    "property_type": st.column_config.TextColumn("Type"),
    "reserve_price": st.column_config.NumberColumn("Reserve ₹", format="₹%d"),
    "emd": st.column_config.NumberColumn("EMD ₹", format="₹%d"),
    "discount_rate_percent": st.column_config.NumberColumn("Discount %", format="%.1f%%"),
    "area_sqft": st.column_config.NumberColumn("Area (sqft)", format="%.0f"),
    "rate_sqft": st.column_config.NumberColumn("Rate/sqft", format="₹%.0f"),
    "market_rate_sqft": st.column_config.NumberColumn("Market Rate", format="₹%.0f"),
    "auction_start_date": st.column_config.TextColumn("Start Date"),
    "auction_end_time": st.column_config.TextColumn("End Date"),
    "contact_details": st.column_config.TextColumn("Contact Info", width="medium"),
    "description": st.column_config.TextColumn("Description", width="large"),
    "source_url": st.column_config.LinkColumn("Property Link", display_text="View Source"),
    "notice_image_url": st.column_config.LinkColumn("Sale Notice", display_text="Download"),
}


# ─── HTML Components ─────────────────────────────────────────────────────────
def kpi_card(icon, label, value, sub="", accent="#FF385C"):
    return f"""<div style="background:var(--bg-card);border:1px solid var(--border-alpha);border-radius:14px;padding:18px 22px;position:relative;overflow:hidden;"><div style="position:absolute;top:-12px;right:-12px;width:70px;height:70px;border-radius:50%;background:{accent}10;"></div><div style="font-size:1.6em;margin-bottom:4px;">{icon}</div><div style="font-size:1.8em;font-weight:800;color:var(--text-main);letter-spacing:-0.02em;line-height:1;">{value}</div><div style="font-size:.75em;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em;margin-top:6px;">{label}</div>{f'<div style="font-size:.7em;color:{accent};margin-top:2px;font-weight:700;">{sub}</div>' if sub else ''}</div>"""



def score_ring(score):
    """SVG ring showing investment score."""
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return '<div style="width:52px;height:52px;border-radius:50%;background:var(--ring-bg);border:3px solid var(--ring-border);"></div>'
    pct   = max(0, min(100, int(score)))
    dash  = round(pct * 1.256, 1)   # circumference fraction (r=20 → C≈125.6)
    color = "#10b981" if pct >= 70 else ("#f59e0b" if pct >= 40 else "#FF385C")

    return f"""<svg width="52" height="52" viewBox="0 0 52 52">
<circle cx="26" cy="26" r="20" fill="none" stroke="var(--ring-bg)" stroke-width="5"/>
<circle cx="26" cy="26" r="20" fill="none" stroke="{color}" stroke-width="5"
        stroke-dasharray="{dash} 125.6" stroke-linecap="round"
        transform="rotate(-90 26 26)"/>
<text x="26" y="30" text-anchor="middle" font-size="11"
      font-weight="700" fill="{color}" font-family="Inter">{pct}</text>
</svg>"""

def property_card(row, now):
    """Render a premium property card matching the reference design."""
    status_label, status_color = auction_status_label(row, now)
    
    price   = f"₹{row['reserve_price']:,.0f}" if pd.notna(row.get('reserve_price')) else "N/A"
    rate    = f"₹{row['rate_sqft']:,.0f}/sqft" if pd.notna(row.get('rate_sqft')) else ""
    area    = f"{row['area_sqft']:,.0f} sqft" if pd.notna(row.get('area_sqft')) else ""
    village = str(row.get('village') or row.get('area_locality') or 'Unknown Locality')
    bank    = str(row.get('bank_name', 'Bank')).upper()[:35]
    title   = str(row.get('title', 'Property'))[:60]
    city    = str(row.get('city', 'CITY')).upper()
    src_url = str(row.get('source_url', '#'))
    
    # Dynamic badge styling based on status color
    badge_bg_map = {
        "#10b981": ("#ecfdf5", "#d1fae5"), # Green
        "#f59e0b": ("#fffbeb", "#fef3c7"), # Amber
        "#eab308": ("#fff7ed", "#ffedd5"), # Yellow
        "#ef4444": ("#fef2f2", "#fee2e2"), # Red
    }
    bg_color, border_color = badge_bg_map.get(status_color, ("#f8fafc", "#e2e8f0"))
    
    # Strip emoji for cleaner UI since we use a custom SVG dot
    display_status = status_label.split(' ')[-1] if ' ' in status_label else status_label

    # Constructing the exact replica of the user's reference Card Design
    return f"""<div class="prop-card" style="background:var(--bg-card);border:1px solid rgba(255,56,92,0.15);border-radius:12px;padding:24px 20px 20px 20px;margin-bottom:20px;position:relative;transition:all .3s ease;">
<!-- Top Red Accent Line -->
<div style="position:absolute;top:-1px;left:16px;right:16px;height:4px;background:#FF385C;border-radius:4px 4px 0 0;"></div>

<div style="display:flex;justify-content:space-between;align-items:flex-start;">
<div style="flex:1;">
<!-- Bank & City -->
<div style="font-size:0.65em;font-weight:800;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;vertical-align:middle;">
{bank} • {city}
</div>
<!-- Title -->
<div style="font-size:1.05em;font-weight:700;color:var(--text-main);line-height:1.4;margin-bottom:8px;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">
{title}
</div>
<!-- Location Pin -->
<div style="font-size:0.85em;color:var(--text-muted);display:flex;align-items:center;gap:6px;">
<span style="color:#FF385C;font-size:1.1em;">📍</span> {village}
</div>
</div>

<!-- Dynamic Investment Score Ring -->
<div style="flex-shrink:0;margin-left:12px;">
{score_ring(row.get('investment_score'))}
</div>
</div>

<!-- Faint Divider matching reference -->
<hr style="border:none;border-top:1px solid rgba(241,245,249,0.8);margin:16px 0;">

<!-- Pricing Block -->
<div style="margin-bottom:16px;">
<div style="font-size:1.55em;font-weight:900;color:var(--text-main);letter-spacing:-0.03em;line-height:1;">
{price}
</div>
<div style="font-size:0.8em;color:var(--text-muted);margin-top:6px;font-weight:500;">
{rate} {f'<span style="color:rgba(148,163,184,0.5);margin:0 4px;">|</span> {area}' if area else ''}
</div>
</div>

<!-- Footer Area -->
<div style="display:flex;justify-content:space-between;align-items:center;margin-top:20px;">
<!-- Days Remaining Badge -->
<div style="background:{bg_color};border:1px solid {border_color};color:{status_color};font-size:0.75em;font-weight:700;padding:4px 14px;border-radius:20px;display:flex;align-items:center;gap:6px;">
<div style="width:8px;height:8px;border-radius:50%;background:url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%228%22 height=%228%22><circle cx=%224%22 cy=%224%22 r=%224%22 fill=%22{status_color.replace('#', '%23')}%22/><circle cx=%223%22 cy=%223%22 r=%221.5%22 fill=%22rgba(255,255,255,0.6)%22/></svg>') no-repeat center center;"></div> 
{display_status}
</div>

<!-- Details Button -->
<a href="{src_url}" target="_blank" style="font-size:0.75em;font-weight:800;color:#FF385C;text-decoration:none;letter-spacing:0.06em;text-transform:uppercase;">Details &rarr;</a>
</div>
</div>"""




# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
# Load data
_db_mtime = os.path.getmtime(config.DB_NAME) if os.path.exists(config.DB_NAME) else 0.0
df = load_data(config.DB_NAME, _db_mtime)

# 🌍 Apply Permissions Filtering
if not is_admin:
    # Filter Cities
    allowed_cities = [c.strip() for c in current_user.get('allowed_cities', '').split(',') if c.strip()]
    if allowed_cities and "*" not in allowed_cities:
        df = df[df['city'].isin(allowed_cities)]
    elif not allowed_cities:
        # If no cities allowed, show empty DF
        df = pd.DataFrame(columns=df.columns)
    
    # Filter Columns (used later in display)
    user_granted_cols = [c.strip() for c in current_user.get('allowed_columns', '').split(',') if c.strip()]
    if not user_granted_cols or "*" in user_granted_cols:
        allowed_cols = list(COLUMNS_MAP.values())
    else:
        allowed_cols = user_granted_cols
else:
    allowed_cols = list(COLUMNS_MAP.values())

# Branding
st.sidebar.markdown("""
<div style="padding:16px 0 8px;text-align:center;">
  <div style="font-size:1.8em;font-weight:900;color:#FF385C;letter-spacing:-.02em;">🏛️ AuctionIQ</div>
  <div style="font-size:.72em;color:var(--text-muted);font-weight:600;margin-top:2px;letter-spacing:.1em;text-transform:uppercase;">
    Premium Intelligence
  </div>
</div>
<hr style="border:none;border-top:1px solid var(--border-light);margin:8px 0 16px;">
""", unsafe_allow_html=True)


# City Active Intelligence (top cities only — keeps sidebar fast)
if not df.empty:
    st.sidebar.markdown("**📍 Active by City**")
    city_active = df[df['is_active']].groupby('city').size().sort_values(ascending=False).head(10)
    for city, count in city_active.items():
        st.sidebar.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 8px;background:rgba(16,185,129,0.05);border-radius:6px;margin-bottom:4px;border:1px solid rgba(16,185,129,0.1);">
                <span style="font-size:0.75em;color:var(--text-muted);font-weight:600;">{city}</span>
                <span style="font-size:0.85em;font-weight:800;color:#10b981;">{count}</span>
            </div>
        """, unsafe_allow_html=True)
    if df[df['is_active']].groupby('city').size().shape[0] > 10:
        st.sidebar.caption("Showing top 10 cities by active auctions.")
    st.sidebar.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

# Connection status
with st.sidebar.expander("🔌 System Status", expanded=False):
    db_status = repo.ping()
    if db_status.get("ok"):
        st.success(f"Database OK — {db_status['property_count']:,} properties")
    else:
        st.error(f"Database error: {db_status.get('error', 'unknown')}")

    api_keys = config.GEMINI_API_KEYS
    if api_keys:
        st.caption(f"Gemini API keys configured: {len(api_keys)}")
    else:
        st.warning("No Gemini API keys in .env")

    active_n = int(df['is_active'].sum()) if not df.empty else 0
    st.caption(f"Loaded {len(df):,} rows · {active_n:,} active · cache TTL 5 min")



# 🌆 Scraper Engine (Admin Only)
if is_admin:
    st.sidebar.markdown("**🌆 Scraper Engine**")
    with st.sidebar.expander("🛡️ Cloudflare Security Fix", expanded=False):
        st.markdown("""
        **If scraping is blocked:**
        1. Open [eauctionsindia.com](https://www.eauctionsindia.com) in Chrome.
        2. Complete any 'Just a moment' challenge.
        3. Press `F12` -> Application -> Cookies.
        4. Copy the value of `cf_clearance` and `__cf_bm`.
        """)
        st.caption("Paste the full cookie string below:")
        cookie_input = st.text_area(
            "Cookie String",
            value=st.session_state.cloudflare_cookie,
            height=90,
            placeholder="cf_clearance=...; __cf_bm=...",
            label_visibility="collapsed",
            key="cf_cookie_input",
        )
        if st.button("Apply Cloudflare Cookie", use_container_width=True):
            if cookie_input.strip():
                st.session_state.cloudflare_cookie = cookie_input.strip()
                scraper.set_cloudflare_cookie(st.session_state.cloudflare_cookie)
                st.success("Cloudflare cookie applied for this session.")
            else:
                st.warning("Paste a valid cookie string first.")

        if st.button("Test Cloudflare Access", use_container_width=True):
            if st.session_state.cloudflare_cookie:
                scraper.set_cloudflare_cookie(st.session_state.cloudflare_cookie)
            result = scraper.test_cloudflare_access()
            if result.get("ok"):
                st.success(
                    f"✅ {result['message']} "
                    f"(HTTP {result.get('status_code')}, cookies: {result.get('cookie_count', 0)})"
                )
            else:
                st.error(
                    f"❌ {result.get('message')} "
                    f"(HTTP {result.get('status_code')}, cf_clearance: {result.get('has_cf_clearance')})"
                )

    target_state      = st.sidebar.selectbox("State", list(config.AVAILABLE_CITIES.keys()), label_visibility="collapsed")
    available_cities  = config.AVAILABLE_CITIES[target_state]
    target_city_name  = st.sidebar.selectbox("City", list(available_cities.keys()), label_visibility="collapsed")
    target_city_slug  = available_cities[target_city_name]
    pages_to_scrape   = st.sidebar.number_input("Pages", 1, 1500, 3, key="pages_scrape")

    if st.sidebar.button("🔄 Scrape " + target_city_name):
        with st.spinner(f"Scraping {target_city_name}..."):
            try:
                new_count = scraper.scrape_city_auctions(target_city_slug, pages_to_scrape, target_city_name)
                st.sidebar.success(f"✅ {new_count} new properties added!")
                load_data.clear()
                st.rerun()
            except RuntimeError as e:
                st.sidebar.error(f"❌ Scrape failed: {str(e)}")

    if st.sidebar.button("🔄 Scrape All Cities in " + target_state):
        with st.sidebar.status(f"🔄 Scraping all cities in {target_state}...", expanded=True) as status:
            total_state_new = 0
            for c_name, c_slug in available_cities.items():
                st.write(f"🔍 Scraping {c_name}...")
                try:
                    c_new = scraper.scrape_city_auctions(c_slug, pages_to_scrape, c_name)
                    total_state_new += c_new
                    if c_new > 0:
                        st.write(f"  ✅ +{c_new} properties from {c_name}")
                except RuntimeError as e:
                    st.write(f"  ⚠️ {c_name} failed: {str(e)[:60]}")
            status.update(label=f"✅ State Scrape Done! {total_state_new} total added.", state="complete")
        load_data.clear()
        st.rerun()

    # Smart Sync Button
    if st.sidebar.button("🚀 Smart Sync (Scrape + AI)", help="Scrapes new properties and automatically runs AI enrichment"):
        # (Existing Smart Sync logic remains unchanged)
        with st.sidebar.status("🔄 Running Smart Sync...", expanded=True) as status:
            st.write(f"🔍 Scraping {pages_to_scrape} pages for {target_city_name}...")
            try:
                new_count = scraper.scrape_city_auctions(target_city_slug, pages_to_scrape, target_city_name)
            except RuntimeError as e:
                status.update(label=f"❌ Scrape failed: {str(e)}", state="error")
                st.stop()
            
            st.write("🤖 Enriching new properties with AI...")
            df_fresh = load_data()
            pending_fresh = repo.get_pending_enrichment()
            if pending_fresh:
                status.update(label=f"🤖 Found {len(pending_fresh)} new properties. Enriching...", state="running")
                try:
                    success_sync = run_enrichment_batches(pending_fresh, batch_size=5)
                    status.update(label=f"✅ Sync Complete: {new_count} found, {success_sync} enriched!", state="complete")
                except RuntimeError as e:
                    status.update(label=f"❌ {str(e)}", state="error")
            else:
                status.update(label=f"✅ Scrape complete. No new properties to enrich.", state="complete")
        load_data.clear()
        st.rerun()

    # 🌐 Bulk PAN-India Scraper
    st.sidebar.markdown("**🌍 PAN-India Bulk Sync**")
    pan_india_pages = st.sidebar.number_input(
        "Pages to Scrape (PAN-India)",
        min_value=1,
        max_value=1500,
        value=5,
        step=1,
        key="pan_india_pages",
        help="Number of listing pages to scrape from the unified PAN-India search endpoint.",
    )

    if st.sidebar.button(
        f"🌍 Start PAN-India Sync ({pan_india_pages} Pages)",
        help=f"Scrapes {pan_india_pages} page(s) nationwide using the unified search endpoint",
        use_container_width=True,
    ):
        with st.sidebar.status("🌐 Running PAN-India Sync...", expanded=True) as status:
            total_new_bulk = 0
            st.write(f"🔍 Scraping {pan_india_pages} pages nationwide...")
            
            try:
                total_new_bulk = scraper.scrape_pan_india_auctions(pan_india_pages)
                if total_new_bulk:
                    st.write(f"  ✅ +{total_new_bulk} new properties added")
                status.update(
                    label=f"✅ Sync Done! {total_new_bulk} new properties added.",
                    state="complete",
                )
            except RuntimeError as e:
                st.write(f"  ⚠️ Failed: {str(e)[:60]}")
                status.update(
                    label=f"❌ Sync Failed.",
                    state="error",
                )

        load_data.clear()
        st.rerun()

    st.sidebar.markdown('<hr style="border:none;border-top:1px solid rgba(255,56,92,0.12);margin:12px 0;">', unsafe_allow_html=True)

    # API key diagnostics
    st.sidebar.markdown("**🔐 API Key Health**")
    if st.sidebar.button("Check Gemini Keys"):
        with st.sidebar.status("Checking keys...", expanded=True) as status:
            key_health = enricher.check_api_keys_health()
            ok_count = 0
            for item in key_health:
                if item.get("ok"):
                    ok_count += 1
                    st.write(f"✅ {item['key']}: {item['message']}")
                else:
                    st.write(f"❌ {item['key']}: {item['message']}")
            if ok_count > 0:
                status.update(label=f"✅ {ok_count}/{len(key_health)} key(s) usable", state="complete")
            else:
                status.update(label="❌ No usable Gemini API keys", state="error")

    st.sidebar.markdown('<hr style="border:none;border-top:1px solid rgba(255,56,92,0.12);margin:12px 0;">', unsafe_allow_html=True)

    # Target Sub-URL
    st.sidebar.markdown("**🔗 Target Sub-URL**")
    target_url = st.sidebar.text_input("Property URL", placeholder="https://www.eauctionsindia.com/properties/...", label_visibility="collapsed")
    if st.sidebar.button("Scrap Target Data"):
        if target_url:
            with st.spinner("Scraping target URL..."):
                prop = scraper.scrape_single_property(target_url)
                if prop:
                    st.sidebar.success(f"✅ Target Property scraped successfully!")
                    load_data.clear()
                    st.rerun()
                else:
                    st.sidebar.error("❌ Failed to scrape property. Please check URL.")

st.sidebar.markdown('<hr style="border:none;border-top:1px solid rgba(255,56,92,0.12);margin:12px 0;">', unsafe_allow_html=True)

# (Data already loaded at start of sidebar)

# Enrichment (Admin Only)
if is_admin and not df.empty:
    pending = repo.get_pending_enrichment()
    if pending:
        st.sidebar.markdown(f'<div style="font-size:.78em;color:#f59e0b;font-weight:600;margin-bottom:6px;">⚠️ {len(pending)} properties need enrichment</div>', unsafe_allow_html=True)
        if st.sidebar.button("🤖 Start AI Enrichment"):
            progress_bar  = st.sidebar.progress(0)
            status_text   = st.sidebar.empty()
            success_count = 0
            batch_size    = 5
            try:
                success_count = run_enrichment_batches(
                    pending,
                    batch_size,
                    on_batch=lambda n, total: (
                        status_text.text(f"Batch {n}/{total}..."),
                        progress_bar.progress(n / total),
                    ),
                )
                st.sidebar.success(f"✅ Enriched {success_count} properties!")
                load_data.clear()
                st.rerun()
            except RuntimeError as e:
                st.sidebar.error(str(e))

st.sidebar.markdown('<hr style="border:none;border-top:1px solid rgba(59,130,246,0.12);margin:12px 0;">', unsafe_allow_html=True)

# Filters
st.sidebar.markdown("**🎛️ Filters**")
only_active = st.sidebar.toggle("Active Auctions Only", value=True)
score_range = st.sidebar.slider("Min Investment Score", 0, 100, 0)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# Hero header (Conditional)
if is_admin:
    main_tabs = st.tabs(["📊 Analytics Dashboard", "👥 User Management"])
    with main_tabs[1]:
        st.subheader("User Permissions Management")
        
        # Add new user
        with st.expander("➕ Create New User"):
            with st.form("new_user"):
                nu_name = st.text_input("Username")
                nu_pass = st.text_input("Password", type="password")
                nu_role = st.selectbox("Role", ["User", "Admin"])
                
                # Dynamic city selection
                all_possible_cities = []
                for state_cities in config.AVAILABLE_CITIES.values():
                    all_possible_cities.extend(state_cities.keys())
                
                nu_cities = st.multiselect("Allowed Cities", ["*"] + sorted(all_possible_cities), default=["*"])
                nu_cols   = st.multiselect("Allowed Columns", ["*"] + list(COLUMNS_MAP.keys()), default=["*"])
                
                if st.form_submit_button("Create User"):
                    if nu_name and nu_pass:
                        city_str = ",".join(nu_cities)
                        col_str  = ",".join([COLUMNS_MAP[c] for c in nu_cols if c in COLUMNS_MAP]) if "*" not in nu_cols else "*"
                        if repo.save_user({'username': nu_name, 'password': nu_pass, 'role': nu_role, 
                                           'allowed_cities': city_str, 'allowed_columns': col_str}):
                            st.success(f"User {nu_name} created!")
                            st.rerun()
                    else:
                        st.error("Username and Password required")

        # List Users
        users = repo.get_all_users()
        for u in users:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([1.5, 1, 2, 0.6, 0.6])
                c1.markdown(f"**👤 {u['username']}**")
                c2.code(u['role'])
                
                # Formatted cities display
                cities_disp = u['allowed_cities'] if u['allowed_cities'] else "None"
                if len(cities_disp) > 30: cities_disp = cities_disp[:27] + "..."
                c3.caption(f"📍 {cities_disp}")
                
                # Edit Toggle
                with c4:
                    do_edit = st.button("📝", key=f"edit_btn_{u['username']}", help="Update Permissions")
                
                with c5:
                    if st.button("🗑️", key=f"del_{u['username']}", help="Delete User"):
                        if repo.delete_user(u['username']):
                            st.success("Deleted")
                            st.rerun()
                
                if do_edit:
                    with st.form(f"edit_form_{u['username']}"):
                        st.markdown(f"✍️ **Edit Permissions for {u['username']}**")
                        
                        # Pre-calculate defaults
                        curr_cities = [c.strip() for c in u['allowed_cities'].split(',') if c.strip()]
                        curr_cols = []
                        INV_COL_MAP = {v: k for k, v in COLUMNS_MAP.items()}
                        for c_val in u['allowed_columns'].split(','):
                            c_val = c_val.strip()
                            if c_val == "*": curr_cols.append("*")
                            elif c_val in INV_COL_MAP: curr_cols.append(INV_COL_MAP[c_val])
                        
                        # Form fields
                        new_role = st.selectbox("Role", ["User", "Admin"], index=0 if u['role'] == "User" else 1)
                        new_all_cities = []
                        for s_cities in config.AVAILABLE_CITIES.values():
                            new_all_cities.extend(s_cities.keys())
                        new_cities = st.multiselect("Cities Access", ["*"] + sorted(new_all_cities), default=curr_cities)
                        new_cols = st.multiselect("Columns Access", ["*"] + list(COLUMNS_MAP.keys()), default=curr_cols)
                        
                        if st.form_submit_button("Save Changes"):
                            city_str = ",".join(new_cities)
                            col_str = ",".join([COLUMNS_MAP[c] for c in new_cols if c in COLUMNS_MAP]) if "*" not in new_cols else "*"
                            if repo.save_user({
                                'username': u['username'],
                                'role': new_role,
                                'allowed_cities': city_str,
                                'allowed_columns': col_str
                            }):
                                st.success("Updated successfully!")
                                st.rerun()

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    ctx = main_tabs[0]
else:
    main_tabs = st.tabs(["📊 Analytics Dashboard", "💳 Subscriptions"])
    
    # 💳 Subscriptions Tab (Normal User)
    with main_tabs[1]:
        st.subheader("Subscription Plans")
        
        # Expiry Check & Notifications
        u_id = repo.get_id_by_username(current_user['username'])
        subs = repo.get_user_subscriptions(u_id)
        
        active_subs = [s for s in subs if s['status'] == 'active']
        for sub in active_subs:
            try:
                exp_date = datetime.strptime(sub['expiry_date'], "%Y-%m-%d")
                days_left = (exp_date - datetime.now()).days
                if 0 <= days_left <= 3:
                    st.warning(f"⚠️ Your subscription for **{sub['cities']}** expires in **{days_left} days**! Renew now to keep access.")
                elif days_left < 0:
                    pass
            except (ValueError, TypeError):
                pass

        # Selection & Pricing
        st.markdown("""
        <div style="background:rgba(255,56,92,0.05);padding:20px;border-radius:12px;border:1px solid rgba(255,56,92,0.2);">
            <div style="font-weight:700;color:#FF385C;margin-bottom:10px;">Select Cities to Unlock</div>
            <div style="font-size:0.85em;color:var(--text-muted);">
                • 1 City: ₹499/mo<br>
                • 2 Cities: ₹899/mo (Save ₹100)<br>
                • 3+ Cities: ₹1299/mo (Extreme Value)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        all_possible_cities = []
        for s_cities in config.AVAILABLE_CITIES.values():
            all_possible_cities.extend(s_cities.keys())
            
        selected_cities = st.multiselect("Choose Cities", sorted(all_possible_cities))
        
        if selected_cities:
            count = len(selected_cities)
            if count == 1: total = 499
            elif count == 2: total = 899
            else: total = 1299
            
            st.markdown(f"### Total Charge: **₹{total}**")
            
            # Payment Gateway Mockup
            if st.button(f"💳 Pay ₹{total} with Razorpay", use_container_width=True):
                with st.spinner("Connecting to Secure Payment Gateway..."):
                    import random
                    import string
                    time.sleep(2)
                    tx_id = "PAY_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    
                    sub_payload = {
                        'cities': ",".join(selected_cities),
                        'plan_type': 'Monthly',
                        'amount': total,
                        'transaction_id': tx_id,
                        'start_date': datetime.now().strftime("%Y-%m-%d"),
                        'expiry_date': (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    }
                    
                    if repo.create_subscription(u_id, sub_payload):
                        st.balloons()
                        st.success(f"Payment Successful! Transaction ID: {tx_id}")
                        st.info("City access has been granted automatically.")
                        time.sleep(2)
                        st.rerun()

        st.divider()
        st.write("**Current Active Subscriptions**")
        if active_subs:
            for s in active_subs:
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"📍 **{s['cities']}**")
                c2.write(f"📅 Until {s['expiry_date']}")
                c3.write(f"₹{s['amount']}")
        else:
            st.caption("No active subscriptions found.")

    ctx = main_tabs[0]

with ctx:
    # Hero header
    st.markdown("""<div style="background:var(--bg-card);border:1px solid var(--border-alpha);border-radius:18px;padding:28px 36px;margin-bottom:28px;position:relative;overflow:hidden;"><div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;border-radius:50%;background:rgba(255,56,92,0.05);pointer-events:none;"></div><div style="font-size:1.9em;font-weight:900;letter-spacing:-.03em;color:var(--text-main);">🏛️ AuctionIQ Intelligence Platform</div><div style="font-size:.88em;color:var(--text-muted);margin-top:6px;font-weight:400;">Real-time bank auction analytics · AI-powered property intelligence · <span style="color:#FF385C">Pan-India Coverage</span></div></div>""", unsafe_allow_html=True)


if df.empty:
    if is_admin:
        msg = "Use the Scraper Engine in the sidebar to fetch auction properties."
    else:
        msg = "Please contact an administrator to sync auction data for your assigned cities."
    
    st.markdown(f"""<div style="text-align:center;padding:80px 20px;"><div style="font-size:4em;margin-bottom:16px;">🏗️</div><div style="font-size:1.3em;font-weight:700;color:#f1f5f9;margin-bottom:8px;">No Data Yet</div><div style="color:#64748b;font-size:.9em;">{msg}</div></div>""", unsafe_allow_html=True)
    st.stop()

# ── Search & Filter Bar ───────────────────────────────────────────────────────
st.markdown("""<div style="background:var(--bg-card);border:1px solid rgba(255,56,92,0.18);border-radius:12px;padding:16px 20px;margin-bottom:16px;"><div style="font-size:.75em;font-weight:800;color:#FF385C;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;">🔍 Search & Filter</div>""", unsafe_allow_html=True)
sf1, sf2, sf3 = st.columns([3, 2, 2])
search_q    = sf1.text_input("Search title, location, bank…", "", label_visibility="collapsed",
                              placeholder="Search title, location, bank…")
configured_cities = []
for state_group in config.AVAILABLE_CITIES.values():
    configured_cities.extend(state_group.keys())
existing_cities = df['city'].dropna().unique().tolist()
all_cities_list = sorted(list(set(configured_cities + existing_cities)))
select_city = sf2.selectbox("City", ["All Cities"] + all_cities_list,
                             label_visibility="collapsed")
select_bank = sf3.selectbox("Bank", ["All Banks"] + sorted(df['bank_name'].dropna().unique().tolist()),
                             label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

# ── Apply Filters (CRITICAL: Before stats calculation) ────────────────────────
dff = df.copy()
if only_active:
    dff = dff[dff['is_active'] == True]
if score_range > 0:
    dff = dff[dff['investment_score'].fillna(0) >= score_range]
if search_q:
    mask = (dff['title'].str.contains(search_q, case=False, na=False) |
            dff['area_locality'].str.contains(search_q, case=False, na=False) |
            dff['village'].str.contains(search_q, case=False, na=False) |
            dff['description'].str.contains(search_q, case=False, na=False))
    dff = dff[mask]
if select_city != "All Cities":
    dff = dff[dff['city'] == select_city]
if select_bank != "All Banks":
    dff = dff[dff['bank_name'] == select_bank]

# ── Compute stats ─────────────────────────────────────────────────────────────
now          = datetime.now()
active_count = int(dff['is_active'].sum())
total_count  = len(dff)
total_val    = dff['reserve_price'].sum()
avg_rate     = dff['rate_sqft'].mean()
enriched_n   = int(dff['market_rate_sqft'].notna().sum())
avg_discount = dff['discount_rate_percent'].mean()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(kpi_card("🏠", "Total Properties", total_count, accent="#FF385C"), unsafe_allow_html=True)

k2.markdown(kpi_card("🟢", "Active Auctions",  active_count,
                     f"{round(active_count/total_count*100)}% of total" if total_count > 0 else "0% of total", "#10b981"), unsafe_allow_html=True)
k3.markdown(kpi_card("💰", "Total Reserve",
                     f"₹{total_val/1e7:.1f}Cr" if total_val >= 1e7 else f"₹{total_val:,.0f}",
                     accent="#f59e0b"), unsafe_allow_html=True)
k4.markdown(kpi_card("📐", "Avg Reserve Rate",
                     f"₹{avg_rate:,.0f}" if pd.notna(avg_rate) else "N/A",
                     "per sqft", "#FF385C"), unsafe_allow_html=True)

k5.markdown(kpi_card("🤖", "AI Enriched",
                     f"{enriched_n}/{total_count}",
                     f"Avg {avg_discount:.1f}% disc" if pd.notna(avg_discount) else "",
                     "#FF385C"), unsafe_allow_html=True)


# ── City Presence Row ────────────────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
city_active_full = dff[dff['is_active']].groupby('city').size().sort_values(ascending=False)
if not city_active_full.empty:
    st.markdown('<div style="font-size:.75em;font-weight:800;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;margin-left:4px;">📍 City-wise Active Auctions</div>', unsafe_allow_html=True)
    c_cols = st.columns(min(len(city_active_full), 6))
    for i, (city, count) in enumerate(city_active_full.items()):
        if i >= 6: break # Show top 6 in header
        with c_cols[i]:
            st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border-alpha);border-radius:12px;padding:12px 16px;display:flex;align-items:center;gap:12px;transition:transform 0.2s;">
                    <div style="width:10px;height:10px;background:#10b981;border-radius:50%;box-shadow:0 0 10px #10b981;"></div>
                    <div>
                        <div style="font-size:0.65em;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">{city}</div>
                        <div style="font-size:1.15em;font-weight:800;color:var(--text-main);line-height:1.1;">{count}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# (Filter logic moved up)

# Result count
active_label = "🟢 Active auctions only" if only_active else "📋 All properties"
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            margin-bottom:12px;padding:0 4px;">
  <span style="font-size:.8em;color:#64748b;">
    Showing <b style="color:#e2e8f0;">{len(dff)}</b> results &nbsp;·&nbsp; {active_label}
  </span>
  <span style="font-size:.75em;color:#475569;">{datetime.now().strftime('%d %b %Y, %H:%M')}</span>
</div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🃏 Property Cards",
    "📋 Data Explorer",
    "📈 Market Intelligence"
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROPERTY CARDS
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    # Top Deal Banner
    high_deals = dff[dff['investment_score'] >= 75].sort_values('investment_score', ascending=False)
    if not high_deals.empty:
        bd = high_deals.iloc[0]
        disc_val = bd['discount_rate_percent'] if pd.notna(bd.get('discount_rate_percent')) else 0
        st.markdown(f"""<div style="background:var(--bg-card);border:1px solid rgba(255,56,92,0.3);border-radius:16px;padding:20px 24px;margin-bottom:20px;position:relative;overflow:hidden;"><div style="position:absolute;top:0;right:0;bottom:0;width:4px;background:#FF385C;"></div><div style="font-size:.72em;font-weight:800;color:#FF385C;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px;">⭐ AI Top Pick of the Day</div><div style="display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;"><div style="flex:1;min-width:200px;"><div style="font-size:1.05em;font-weight:700;color:var(--text-main);margin-bottom:4px;">{bd['title']}</div><div style="font-size:.78em;color:var(--text-muted);">🏦 {bd['bank_name']} &nbsp;·&nbsp; 📍 {bd.get('area_locality','N/A')} &nbsp;·&nbsp; {bd.get('city','N/A')}</div><div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;"><span style="background:rgba(255,56,92,0.1);color:#FF385C;border:1px solid var(--border-alpha);padding:3px 12px;border-radius:20px;font-size:.72em;font-weight:800;">Score {bd['investment_score']} / 100</span><span style="background:#10b98122;color:#34d399;border:1px solid #10b98144;padding:3px 12px;border-radius:20px;font-size:.72em;font-weight:700;">{bd.get('possession_status','N/A')} Possession</span></div></div><div style="text-align:right;flex-shrink:0;"><div style="font-size:1.6em;font-weight:900;color:var(--text-main);letter-spacing:-.02em;">₹{bd['reserve_price']:,.0f}</div><div style="font-size:.78em;color:#FF385C;font-weight:800;margin-top:2px;">{disc_val:.1f}% below market</div></div></div></div>""", unsafe_allow_html=True)


    if dff.empty:
        st.markdown("""<div style="text-align:center;padding:60px;color:#475569;">
            No properties match your filters.</div>""", unsafe_allow_html=True)
    else:
        CARD_PAGE_SIZE = 24
        if "card_offset" not in st.session_state:
            st.session_state.card_offset = CARD_PAGE_SIZE
        if st.session_state.get("card_filter_key") != len(dff):
            st.session_state.card_offset = CARD_PAGE_SIZE
            st.session_state.card_filter_key = len(dff)

        visible = dff.iloc[:st.session_state.card_offset]
        cols_per_row = 3
        rows = [visible.iloc[i:i + cols_per_row] for i in range(0, len(visible), cols_per_row)]
        for row_df in rows:
            cols = st.columns(cols_per_row)
            for col, (_, prop) in zip(cols, row_df.iterrows()):
                with col:
                    st.markdown(property_card(prop, now), unsafe_allow_html=True)

        shown = len(visible)
        st.caption(f"Showing {shown:,} of {len(dff):,} matching properties")
        if shown < len(dff):
            remaining = len(dff) - shown
            if st.button(
                f"Load {min(CARD_PAGE_SIZE, remaining)} more properties",
                key="load_more_cards",
                use_container_width=True,
            ):
                st.session_state.card_offset += CARD_PAGE_SIZE
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — DATA EXPLORER (original table view, enhanced)
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""<div style="margin-bottom:12px;">
      <span style="font-size:.78em;color:#64748b;">
        Full dataset view with all fields. Click column headers to sort.
      </span></div>""", unsafe_allow_html=True)

    if dff.empty:
        st.info("No properties match your current filters. Try turning off **Active Auctions Only** in the sidebar.")
    else:
        EXPLORER_PAGE_SIZE = 200
        display_df = prepare_explorer_df(dff)
        total_pages = max(1, math.ceil(len(display_df) / EXPLORER_PAGE_SIZE))
        ep1, ep2 = st.columns([1, 3])
        with ep1:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
        with ep2:
            st.caption(
                f"Showing rows {(page - 1) * EXPLORER_PAGE_SIZE + 1:,}"
                f"–{min(page * EXPLORER_PAGE_SIZE, len(display_df)):,}"
                f" of {len(display_df):,} properties"
            )

        start = (page - 1) * EXPLORER_PAGE_SIZE
        page_df = display_df.iloc[start:start + EXPLORER_PAGE_SIZE]
        table_cols = [c for c in page_df.columns if c in EXPLORER_COLUMN_CONFIG]
        column_config = {c: EXPLORER_COLUMN_CONFIG[c] for c in table_cols}

        st.dataframe(
            page_df,
            column_config=column_config,
            use_container_width=True,
            height=600,
            hide_index=True,
        )

        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export All Filtered Data (CSV)", csv,
            "auction_export.csv", "text/csv",
            use_container_width=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — MARKET INTELLIGENCE (advanced analytics)
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""<div style="background:var(--bg-card);border-radius:12px;padding:18px 24px;margin-bottom:20px;border-left:4px solid #FF385C;"><div style="font-size:1.1em;font-weight:900;color:var(--text-main);">📊 Advanced Market Intelligence</div><div style="font-size:.78em;color:var(--text-muted);margin-top:3px;">Multi-dimensional analytics for smarter investment decisions</div></div>""", unsafe_allow_html=True)

    chart_df = dff
    if len(chart_df) > 3000:
        chart_df = chart_df.sample(3000, random_state=42)

    # 🤖 AI Summary Brief
    with st.container():
        st.markdown("### 🤖 Market Intelligence Brief")
        if st.toggle("Generate Real-time AI Briefing", value=False, key="gen_summary"):
            with st.spinner("AI analyzing localized trends..."):
                market_brief = enricher.generate_market_summary(dff.head(100).to_dict('records'))
                st.markdown(f"""<div style="background:rgba(255,56,92,0.02);padding:24px;border-radius:16px;border:1px solid var(--border-alpha);margin-bottom:30px;font-size:0.95em;color:var(--text-main);box-shadow:var(--card-shadow);">{market_brief}</div>""", unsafe_allow_html=True)


        else:
            st.info("💡 Toggle above to generate an AI-driven investment briefing based on live data.")

    # ── SECTION 1: PRICE INTELLIGENCE ────────────────────────────────────────

    st.markdown("### 💰 Price Intelligence")
    pi_c1, pi_c2 = st.columns(2)

    scatter_df = chart_df.dropna(subset=['reserve_price','market_rate_sqft','rate_sqft']).copy()
    if not scatter_df.empty:
        area_med = scatter_df['area_sqft'].median()
        scatter_df['area_sqft'] = scatter_df['area_sqft'].fillna(
            area_med if pd.notna(area_med) else 500).clip(lower=1)
        fig_sc = px.scatter(scatter_df, x='rate_sqft', y='market_rate_sqft',
                            size='area_sqft', size_max=45, color='city',
                            hover_name='title',
                            hover_data={'bank_name':True,'reserve_price':':.0f',
                                        'discount_rate_percent':':.1f','area_sqft':':.0f',
                                        'rate_sqft':False,'market_rate_sqft':False},
                            title='Reserve Rate vs Market Rate',
                            labels={'rate_sqft':'Reserve Rate (₹/sqft)',
                                    'market_rate_sqft':'Market Rate (₹/sqft)'},
                            template=plotly_template)
        mx = max(scatter_df['rate_sqft'].max(), scatter_df['market_rate_sqft'].max())
        fig_sc.add_shape(type='line', x0=0, y0=0, x1=mx, y1=mx,
                          line=dict(color='#ef4444',dash='dash',width=1.5))
        fig_sc.add_annotation(x=mx*.85, y=mx*.92, text="Fair Value Line",
                               showarrow=False, font=dict(color='#ef4444',size=11))
        fig_sc.update_layout()
        render_plotly(pi_c1, fig_sc)
    else:
        pi_c1.info("Run AI Enrichment to unlock this chart.")

    box_df = chart_df.dropna(subset=['reserve_price','property_type']).copy()
    box_df = box_df[box_df['property_type'].str.strip() != '']
    if not box_df.empty:
        fig_bx = px.box(box_df, x='property_type', y='reserve_price',
                        color='property_type', points='outliers',
                        title='Price Spread by Property Type',
                        labels={'reserve_price':'Reserve (₹)','property_type':'Type'},
                        template=plotly_template)
        fig_bx.update_layout(showlegend=False,xaxis_tickangle=-30)
        render_plotly(pi_c2, fig_bx)
    else:
        hdf = chart_df.dropna(subset=['reserve_price'])
        if not hdf.empty:
            fig_h = px.histogram(hdf, x='reserve_price', nbins=25,
                                  title='Reserve Price Distribution',
                                  color_discrete_sequence=['#FF385C'],
                                  template=plotly_template)
            fig_h.update_layout()
            render_plotly(pi_c2, fig_h)

    st.markdown("---")

    # ── SECTION 2: OPPORTUNITY RADAR ─────────────────────────────────────────
    st.markdown("### 🎯 Opportunity Radar")
    or_c1, or_c2 = st.columns(2)

    radar_df = chart_df.dropna(subset=['investment_score','discount_rate_percent'])
    if not radar_df.empty:
        fig_mx = px.scatter(radar_df, x='discount_rate_percent', y='investment_score',
                            color='risk_rating', size='reserve_price',
                            color_discrete_map={'Low':'#10b981','Medium':'#f59e0b','High':'#FF385C'},
                            hover_name='title',
                            hover_data={'bank_name':True,'city':True,'reserve_price':':.0f',
                                        'discount_rate_percent':':.1f','investment_score':True},
                            title='Risk vs Reward Matrix',
                            labels={'discount_rate_percent':'Discount Below Market (%)',
                                    'investment_score':'Investment Score','risk_rating':'Risk'},
                            template=plotly_template)
        fig_mx.add_hline(y=50, line_dash='dot', line_color='#333333', line_width=1)
        fig_mx.add_vline(x=0, line_dash='dot', line_color='#333333', line_width=1)
        fig_mx.add_annotation(x=25, y=85, text="🏆 Sweet Spot", showarrow=False,
                               font=dict(color='#10b981',size=12))
        fig_mx.update_layout()
        render_plotly(or_c1, fig_mx)
    else:
        or_c1.info("Run AI Enrichment to unlock the Risk vs Reward Matrix.")

    top_disc = chart_df.dropna(subset=['discount_rate_percent']).sort_values('discount_rate_percent', ascending=False).head(10)
    if not top_disc.empty:
        fig_td = px.bar(top_disc, x='discount_rate_percent',
                        y=top_disc['title'].str[:30].str.cat(top_disc['city'].fillna(''), sep=' · '),
                        orientation='h', color='discount_rate_percent',
                        color_continuous_scale='RdYlGn',
                        title='Top 10 Discount Opportunities',
                        template=plotly_template)
        fig_td.update_layout(yaxis_autorange='reversed',
                              coloraxis_showscale=False)
        render_plotly(or_c2, fig_td)
    else:
        or_c2.info("Discount data unavailable. Run AI Enrichment first.")

    st.markdown("---")

    # ── SECTION 3: BANK INTELLIGENCE ─────────────────────────────────────────
    st.markdown("### 🏦 Bank Intelligence")
    bi_c1, bi_c2 = st.columns(2)

    bank_agg = (dff.groupby('bank_name')
                  .agg(count=('id','count'), avg_price=('reserve_price','mean'))
                  .sort_values('count', ascending=False).head(12).reset_index())
    if not bank_agg.empty:
        fig_bk = go.Figure()
        fig_bk.add_trace(go.Bar(x=bank_agg['bank_name'], y=bank_agg['count'],
                                name='Auctions', marker_color='#FF385C', opacity=.85, yaxis='y1'))
        fig_bk.add_trace(go.Scatter(x=bank_agg['bank_name'], y=bank_agg['avg_price'],
                                    name='Avg Reserve ₹', mode='lines+markers',
                                    line=dict(color='#f59e0b',width=2.5), marker=dict(size=8), yaxis='y2'))
        fig_bk.update_layout(title='Auction Volume & Avg Reserve per Bank',
                              xaxis=dict(tickangle=-35),
                              yaxis=dict(title='Auctions',showgrid=False),
                              yaxis2=dict(title='Avg Reserve (₹)',overlaying='y',side='right',showgrid=False),
                              legend=dict(orientation='h',y=1.12,x=0),
                              template=plotly_template)
        render_plotly(bi_c1, fig_bk)

    risk_df = dff.dropna(subset=['risk_rating'])
    risk_df = risk_df[risk_df['risk_rating'].str.strip() != '']
    if not risk_df.empty:
        rp = risk_df.groupby(['bank_name','risk_rating']).size().reset_index(name='count')
        rp = rp[rp['bank_name'].isin(bank_agg['bank_name'].head(10).tolist())]
        fig_rk = px.bar(rp, x='bank_name', y='count', color='risk_rating',
                        color_discrete_map={'Low':'#10b981','Medium':'#f59e0b','High':'#FF385C'},
                        title='Risk Profile by Bank', barmode='stack',
                        labels={'count':'Properties','bank_name':'Bank','risk_rating':'Risk'},
                        template=plotly_template)
        fig_rk.update_layout(xaxis_tickangle=-35,)
        render_plotly(bi_c2, fig_rk)
    else:
        bpie = dff['bank_name'].value_counts().reset_index()
        fig_pie = px.pie(bpie, values='count', names='bank_name',
                         title='Auction Volume by Bank', template=plotly_template,
                         color_discrete_sequence=px.colors.sequential.Reds_r)
        fig_pie.update_layout()
        render_plotly(bi_c2, fig_pie)

    st.markdown("---")

    # ── SECTION 4: LOCATION INTELLIGENCE ─────────────────────────────────────
    st.markdown("### 📍 Location Intelligence")
    loc_c1, loc_c2 = st.columns([3, 2])

    # Geographically visualized bubble map (Approximate centroids)
    city_coords = {
        "Pune": [18.5204, 73.8567], "Mumbai": [19.0760, 72.8777], "Thane": [19.2183, 72.9781],
        "Navi Mumbai": [19.0330, 73.0297], "Raigad": [18.5144, 73.1812], "Bengaluru": [12.9716, 77.5946],
        "Chennai": [13.0827, 80.2707], "Kolkata": [22.5726, 88.3639], "Hyderabad": [17.3850, 78.4867],
        "Ahmedabad": [23.0225, 72.5714], "New Delhi": [28.6139, 77.2090], "Lucknow": [26.8467, 80.9462],
        "Jaipur": [26.9124, 75.7873], "Indore": [22.7196, 75.8577], "Patna": [25.5941, 85.1376],
        "Bhopal": [23.2599, 77.4126], "Surat": [21.1702, 72.8311], "Nagpur": [21.1458, 79.0882],
        "Coimbatore": [11.0168, 76.9558], "Kochi": [9.9312, 76.2673], "Bhubaneswar": [20.2961, 85.8245],
        "Ludhiana": [30.9010, 75.8573], "Kanpur": [26.4499, 80.3319], "Agra": [27.1767, 78.0081],
        "Mysuru": [12.2958, 76.6394], "Nashik": [19.9975, 73.7898], "Belagavi": [15.8497, 74.4977],
        "Aurangabad": [19.8762, 75.3433], "Vadodara": [22.3072, 73.1812], "Rajkot": [22.3039, 70.8022]
    }
    
    map_data = dff.groupby('city').size().reset_index(name='count')
    map_data['lat'] = map_data['city'].map(lambda x: city_coords.get(x, [0,0])[0])
    map_data['lon'] = map_data['city'].map(lambda x: city_coords.get(x, [0,0])[1])
    map_data = map_data[map_data['lat'] != 0]

    if not map_data.empty:
        fig_map = px.scatter_mapbox(map_data, lat="lat", lon="lon", size="count",
                                    color="count", color_continuous_scale="Reds",
                                    size_max=30, zoom=7, mapbox_style="carto-darkmatter",
                                    title="Auction Concentration Map",
                                    hover_name="city",
                                    labels={"count": "Properties"})
        fig_map.update_layout(margin=dict(l=0,r=0,t=40,b=0), paper_bgcolor='var(--bg-main)')
        render_plotly(loc_c1, fig_map)
    else:
        tree_df = dff.copy()
        tree_df['village'] = tree_df['village'].fillna('Unknown')
        tree_df['city']    = tree_df['city'].fillna('Unknown')
        tree_df['count']   = 1
        fig_tr = px.treemap(tree_df, path=[px.Constant('All Cities'),'city','village'],
                            values='count', color='reserve_price',
                            color_continuous_scale='Reds',
                            color_continuous_midpoint=tree_df['reserve_price'].median(),
                            title='City → Village Drill-down',
                            template=plotly_template)
        fig_tr.update_layout( margin=dict(t=50,l=5,r=5,b=5))
        render_plotly(loc_c1, fig_tr)

    # 📊 State Summary
    state_agg = dff.groupby('state_region').size().reset_index(name='count').sort_values('count', ascending=False)
    if not state_agg.empty:
        fig_st = px.bar(state_agg, x='state_region', y='count', color='state_region',
                         title='Auctions by State',
                         labels={'count':'Auctions','state_region':'State'},
                         template=plotly_template,
                         color_discrete_sequence=px.colors.sequential.Reds_r)
        fig_st.update_layout(showlegend=False)
        render_plotly(loc_c2, fig_st)

    city_sum = (dff.groupby('city').agg(
        Properties=('id','count'),
        Avg_Reserve=('reserve_price','mean'),
        Avg_Discount=('discount_rate_percent','mean'),
        Avg_Score=('investment_score','mean'),
        Active=('is_active','sum')
    ).sort_values('Properties', ascending=False).reset_index())
    city_sum.columns = ['City','Properties','Avg Reserve ₹','Avg Discount %','Avg Score','Active']
    city_sum['Avg Reserve ₹']   = city_sum['Avg Reserve ₹'].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else '—')
    city_sum['Avg Discount %']  = city_sum['Avg Discount %'].map(lambda x: f"{x:.1f}%" if pd.notna(x) else '—')
    city_sum['Avg Score']       = city_sum['Avg Score'].map(lambda x: f"{x:.0f}" if pd.notna(x) else '—')
    city_sum['Active']          = city_sum['Active'].astype(int)
    
    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.markdown("**Property Intelligence Data Explorer**")
    
    # Export options
    e1, e2 = st.columns([1, 4])
    csv = safe_column_subset(dff, allowed_cols).to_csv(index=False).encode('utf-8')
    e1.download_button("📥 Export CSV", csv, "auctions.csv", "text/csv", use_container_width=True)
    
    if st.button("📄 Generate Intelligence PDF"):
        with st.spinner("Preparing PDF report..."):
            pdf_data = export_pdf(dff, allowed_cols)
            st.download_button("⬇️ Download PDF Report", pdf_data, "AuctionIQ_Report.pdf", "application/pdf")

    intel_df = prepare_explorer_df(safe_column_subset(dff, allowed_cols))
    if intel_df.empty:
        st.info("No data available for the selected filters.")
    else:
        st.dataframe(intel_df, hide_index=True, height=500, use_container_width=True)

    st.markdown("---")

    # ── SECTION 5: AUCTION TIMELINE ───────────────────────────────────────────
    st.markdown("### 📅 Upcoming Auction Timeline")
    tl_df   = dff.dropna(subset=['parsed_start_date']).copy()
    future  = tl_df[tl_df['parsed_start_date'] >= now].sort_values('parsed_start_date').head(30)

    if not future.empty:
        tl_c1, tl_c2 = st.columns([3, 1])
        future = future.copy()
        future['end_dt']      = future['parsed_end_time'].fillna(
            future['parsed_start_date'] + pd.Timedelta(hours=2))
        future['short_title'] = future['title'].str[:40]
        fig_g = px.timeline(future, x_start='parsed_start_date', x_end='end_dt',
                            y='short_title', color='city',
                            hover_name='title',
                            hover_data={'bank_name':True,'reserve_price':':.0f',
                                        'city':False,'parsed_start_date':False,'end_dt':False},
                            title=f'Next {len(future)} Upcoming Auctions',
                            template=plotly_template)
        fig_g.update_yaxes(autorange='reversed')
        fig_g.update_layout(xaxis_title='',yaxis_title='',
                             height=max(320, len(future)*28))
        render_plotly(tl_c1, fig_g)

        future['date_only'] = future['parsed_start_date'].dt.date
        cal = future.groupby('date_only').size().reset_index(name='count')
        cal['date_only'] = pd.to_datetime(cal['date_only'])
        fig_cal = px.bar(cal, x='date_only', y='count', title='Auctions per Day',
                         color='count', color_continuous_scale='Reds',
                         labels={'date_only':'Date','count':'Auctions'}, template=plotly_template)
        fig_cal.update_layout(
                               coloraxis_showscale=False)
        render_plotly(tl_c2, fig_cal)

        tl_c2.markdown("**⚡ Nearest 5**")
        for _, row in future.head(5).iterrows():
            dt_s  = row['parsed_start_date'].strftime('%d %b, %I:%M %p')
            tl_c2.markdown(
                f"<div style='background:var(--bg-card);border-left:3px solid #FF385C;"
                f"padding:8px 12px;border-radius:6px;margin-bottom:6px;font-size:.78em;'>"
                f"<b style='color:var(--text-main);'>{row['title'][:42]}</b><br>"
                f"<span style='color:var(--text-muted);'>🏦 {row['bank_name']} · 📅 {dt_s}</span></div>",
                unsafe_allow_html=True)
    else:
        st.info("No upcoming auctions with parseable dates found.")
