import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.database import load_latest_profile as load_profile

st.set_page_config(
    page_title="NutriCoach",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🥗 NutriCoach")
st.subheader("Your Personal Nutrition & Fitness Companion")

if "profile" not in st.session_state:
    saved = load_profile()
    if saved:
        st.session_state.profile = saved

if "profile" not in st.session_state:
    st.info("👈 Start by completing your **Setup** in the sidebar!")
    st.markdown("""
    ### How it works
    1. **Setup** — enter your profile once (height, weight, goals, health conditions)
    2. **Dashboard** — set today's focus and log your workout to get your net calorie budget
    3. **Kitchen Mode** — pick ingredients you have at home and get healthy recipes
    4. **Dish Lookup** — type any dish and find out exactly how much you can eat
    """)
else:
    profile = st.session_state.profile
    st.success(f"Welcome back, **{profile['name']}**! Your profile is ready.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Daily Base Calories", f"{profile['base_calories']} kcal")
    col2.metric("Fitness Goal", profile["fitness_goal"])
    col3.metric("Diet", profile["diet_pref"])
    st.markdown("👈 Head to the **Dashboard** to plan today's nutrition.")
