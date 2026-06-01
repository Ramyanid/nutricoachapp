import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.database import get_all_profiles

st.set_page_config(page_title="Admin — NutriCoach", page_icon="🔐", layout="wide")
st.title("🔐 Admin Panel")

# ── Password gate ──────────────────────────────────────────────────────────────
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    pwd = st.text_input("Enter admin password", type="password")
    if st.button("Login", type="primary"):
        if pwd == st.secrets.get("ADMIN_PASSWORD", ""):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# ── Admin view ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([6, 1])
col1.subheader("All User Profiles")
if col2.button("Logout"):
    st.session_state.admin_authenticated = False
    st.rerun()

profiles = get_all_profiles()

if not profiles:
    st.info("No profiles saved yet.")
    st.stop()

st.metric("Total profiles", len(profiles))
st.divider()

DISPLAY_COLS = [
    "id", "name", "email", "age", "sex", "weight_kg", "height_cm",
    "fitness_goal", "diet_pref", "health_conditions",
    "bmr", "tdee", "base_calories", "created_at", "updated_at",
]

import pandas as pd

rows = []
for p in profiles:
    rows.append({
        "ID":             p.get("id"),
        "Name":           p.get("name"),
        "Email":          p.get("email") or "—",
        "Age":            p.get("age"),
        "Sex":            p.get("sex"),
        "Weight (kg)":    p.get("weight_kg"),
        "Height (cm)":    p.get("height_cm"),
        "Goal":           p.get("fitness_goal"),
        "Diet":           p.get("diet_pref"),
        "Health":         ", ".join(p.get("health_conditions") or []) or "None",
        "BMR":            p.get("bmr"),
        "TDEE":           p.get("tdee"),
        "Daily Calories": p.get("base_calories"),
        "Created":        p.get("created_at"),
        "Updated":        p.get("updated_at"),
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Profile Details")
selected_id = st.selectbox(
    "Select a profile to view in full",
    options=[p["id"] for p in profiles],
    format_func=lambda i: next(f"{p['name']} ({p.get('email') or 'no email'})" for p in profiles if p["id"] == i),
)

selected = next(p for p in profiles if p["id"] == selected_id)
c1, c2, c3 = st.columns(3)
c1.metric("BMR",          f"{selected['bmr']} kcal")
c2.metric("TDEE",         f"{selected['tdee']} kcal")
c3.metric("Daily Target", f"{selected['base_calories']} kcal")

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**Activity:** {selected.get('activity_level')}")
    st.markdown(f"**Cuisines:** {', '.join(selected.get('cuisine_prefs') or [])}")
with c2:
    st.markdown(f"**Health conditions:** {', '.join(selected.get('health_conditions') or ['None'])}")
    st.markdown(f"**Last updated:** {selected.get('updated_at')}")
