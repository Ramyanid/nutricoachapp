import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.nutrition import (
    adjust_for_daily_focus, calculate_workout_burn,
    get_macros, apply_calorie_floor,
)
from utils.database import load_latest_profile as load_profile

st.set_page_config(page_title="Dashboard — NutriCoach", page_icon="📊", layout="wide")
st.title("📊 Daily Dashboard")

if "profile" not in st.session_state:
    saved = load_profile()
    if saved:
        st.session_state.profile = saved

if "profile" not in st.session_state:
    st.warning("⚠️ Complete your **Setup** first!")
    st.stop()

profile = st.session_state.profile
st.markdown(f"Hey **{profile['name']}**! Let's plan your nutrition for today.")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Today's Focus")
    daily_focus = st.radio(
        "What are you working towards today?",
        ["Muscle tightening", "Core + fat loss", "Overall weight loss", "Body toning", "Rest day"],
    )

    FOCUS_NOTES = {
        "Muscle tightening":   "High protein + slight surplus to support muscle repair.",
        "Core + fat loss":     "Low carb, high protein — deeper deficit day.",
        "Overall weight loss": "Significant calorie deficit with balanced macros.",
        "Body toning":         "Slight deficit, balanced macros for lean definition.",
        "Rest day":            "Maintenance-ish calories — let your body recover.",
    }
    st.caption(FOCUS_NOTES[daily_focus])

    st.subheader("Workout Today?")
    did_workout   = st.toggle("I worked out today")
    workout_burn  = 0

    if did_workout:
        workout_type = st.selectbox("Workout type", [
            "Cardio", "Strength training", "HIIT", "Yoga", "Walking", "Cycling", "Swimming",
        ])
        duration     = st.slider("Duration (minutes)", min_value=10, max_value=180, value=45, step=5)
        workout_burn = calculate_workout_burn(workout_type, duration)
        st.info(f"🔥 Estimated burn: **{workout_burn} kcal**")

with col_right:
    focus_calories = adjust_for_daily_focus(profile["base_calories"], daily_focus)
    raw_net        = focus_calories + workout_burn
    net_calories   = apply_calorie_floor(raw_net, profile["sex"])
    macros         = get_macros(net_calories, daily_focus)
    focus_delta    = focus_calories - profile["base_calories"]

    st.subheader("Your Calorie Budget Today")

    c1, c2 = st.columns(2)
    c1.metric("Base Target",      f"{profile['base_calories']} kcal")
    c2.metric("Focus Adjustment", f"{focus_delta:+} kcal")

    if workout_burn > 0:
        c1.metric("Workout Earned", f"+{workout_burn} kcal")

    st.metric(
        "Net Daily Calories",
        f"{net_calories} kcal",
        delta=f"{net_calories - profile['base_calories']:+} from base",
    )

    if net_calories != raw_net:
        st.caption(f"⚠️ Raised to minimum safe floor ({net_calories} kcal) for your profile.")

    st.divider()
    st.subheader("Macro Targets")
    cp, cc, cf = st.columns(3)
    cp.metric("Protein", f"{macros['protein_g']}g")
    cc.metric("Carbs",   f"{macros['carbs_g']}g")
    cf.metric("Fat",     f"{macros['fat_g']}g")

    st.divider()
    st.subheader("Meal Breakdown")
    meals = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30, "Snack": 0.10}
    cols  = st.columns(4)
    for i, (meal, pct) in enumerate(meals.items()):
        cols[i].metric(meal, f"{round(net_calories * pct)} kcal")

# Persist for other pages
st.session_state.daily_calories = net_calories
st.session_state.daily_focus    = daily_focus

st.divider()
st.subheader("What's next?")
c1, c2 = st.columns(2)

with c1:
    st.markdown("**🍳 Have ingredients at home?**")
    st.markdown("Pick what's in your kitchen and get healthy recipe suggestions.")
    st.page_link("pages/3_Kitchen_Mode.py", label="Go to Kitchen Mode", icon="🍳")

with c2:
    st.markdown("**🔍 Know what you want to eat?**")
    st.markdown("Type any dish and find out exactly how much you can have.")
    st.page_link("pages/3_Kitchen_Mode.py", label="Go to Dish Lookup", icon="🔍")
