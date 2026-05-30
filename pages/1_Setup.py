import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.nutrition import calculate_bmr, calculate_tdee, adjust_calories_for_goal
from utils.storage import save_profile, load_profile

st.set_page_config(page_title="Setup — NutriCoach", page_icon="⚙️", layout="wide")
st.title("⚙️ Profile Setup")
st.markdown("Fill this in once. We use it to calculate your personalised daily calorie budget.")

# Restore profile from disk if session was cleared
if "profile" not in st.session_state:
    saved = load_profile()
    if saved:
        st.session_state.profile = saved

with st.form("profile_form"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("About You")
        name   = st.text_input("Name (optional)", placeholder="e.g. Priya")
        age    = st.number_input("Age", min_value=15, max_value=80, value=25, step=1)
        sex    = st.radio("Sex", ["Female", "Male"], horizontal=True)

        unit   = st.radio("Unit system", ["Metric (cm / kg)", "Imperial (ft-in / lbs)"], horizontal=True)
        if unit == "Metric (cm / kg)":
            height_cm = float(st.number_input("Height (cm)", min_value=100, max_value=250, value=165, step=1))
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=65.0, step=0.5)
        else:
            c1, c2 = st.columns(2)
            ft = c1.number_input("Feet", min_value=4, max_value=7, value=5, step=1)
            inch = c2.number_input("Inches", min_value=0, max_value=11, value=5, step=1)
            height_cm = (ft * 12 + inch) * 2.54
            lbs = st.number_input("Weight (lbs)", min_value=66.0, max_value=550.0, value=143.0, step=1.0)
            weight_kg = lbs * 0.453592

        activity = st.selectbox("General activity level", [
            "Sedentary (little/no exercise)",
            "Lightly active (1-3 days/week)",
            "Moderately active (3-5 days/week)",
            "Very active (6-7 days/week)",
            "Extremely active (athlete/physical job)",
        ])

    with col2:
        st.subheader("Goals & Preferences")
        fitness_goal = st.radio("Primary fitness goal", [
            "Overall weight loss",
            "Muscle building",
            "Body toning / inch loss",
            "Maintenance",
        ])

        health_conditions = st.multiselect(
            "Health conditions (select all that apply)",
            ["None", "Diabetes", "High Blood Pressure", "High Cholesterol",
             "PCOS", "Thyroid condition", "Gluten intolerance"],
            default=["None"],
        )

        diet_pref = st.radio("Diet preference", ["Non-vegetarian", "Vegetarian", "Vegan"], horizontal=True)

        cuisine_prefs = st.multiselect(
            "Cuisine preferences",
            ["Indian", "Mediterranean", "Asian", "American", "Mexican",
             "Italian", "Chinese", "Japanese", "Middle Eastern"],
            default=["Indian"],
        )

    submitted = st.form_submit_button("Save Profile ✅", type="primary", use_container_width=True)

if submitted:
    if "None" in health_conditions and len(health_conditions) > 1:
        health_conditions.remove("None")

    bmr           = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee          = calculate_tdee(bmr, activity)
    base_calories = adjust_calories_for_goal(tdee, fitness_goal)

    profile = {
        "name":             name.strip() or "there",
        "age":              age,
        "sex":              sex,
        "height_cm":        round(height_cm, 1),
        "weight_kg":        round(weight_kg, 1),
        "activity_level":   activity,
        "fitness_goal":     fitness_goal,
        "health_conditions":health_conditions,
        "diet_pref":        diet_pref,
        "cuisine_prefs":    cuisine_prefs,
        "bmr":              round(bmr),
        "tdee":             round(tdee),
        "base_calories":    round(base_calories),
    }
    st.session_state.profile = profile
    save_profile(profile)

    st.success("Profile saved!")
    st.balloons()

    c1, c2, c3 = st.columns(3)
    c1.metric("BMR",          f"{round(bmr)} kcal",          help="Calories burned at complete rest")
    c2.metric("TDEE",         f"{round(tdee)} kcal",         help="Total daily energy expenditure")
    c3.metric("Daily Target", f"{round(base_calories)} kcal", help=f"Adjusted for: {fitness_goal}")

elif "profile" in st.session_state:
    p = st.session_state.profile
    st.info("Profile already saved. Re-submit the form to update it.")
    c1, c2, c3 = st.columns(3)
    c1.metric("BMR",          f"{p['bmr']} kcal")
    c2.metric("TDEE",         f"{p['tdee']} kcal")
    c3.metric("Daily Target", f"{p['base_calories']} kcal")
