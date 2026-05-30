import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.edamam import analyze_dish

st.set_page_config(page_title="Dish Lookup — NutriCoach", page_icon="🔍", layout="wide")
st.title("🔍 Dish Lookup")
st.markdown("Type any dish and we'll tell you **exactly how much to eat** to stay within your calorie budget.")

if "profile" not in st.session_state:
    st.warning("⚠️ Complete your **Setup** first!")
    st.stop()

profile        = st.session_state.profile
daily_calories = st.session_state.get("daily_calories", profile["base_calories"])

st.info(f"Today's calorie budget: **{daily_calories} kcal**")

MEAL_FRACTIONS = {
    "Breakfast  (25% of daily)": 0.25,
    "Lunch / Dinner  (35% of daily)": 0.35,
    "Snack  (10% of daily)": 0.10,
}

c1, c2 = st.columns([2, 1])
with c1:
    dish_name = st.text_input(
        "Dish name",
        placeholder="e.g. butter chicken, idli sambar, caesar salad, pasta carbonara",
    )
with c2:
    meal_label    = st.selectbox("Meal slot", list(MEAL_FRACTIONS.keys()))
    meal_fraction = MEAL_FRACTIONS[meal_label]

analyze_btn = st.button(
    "🔍 Analyse",
    type="primary",
    disabled=not dish_name,
    use_container_width=True,
)

if analyze_btn:
    with st.spinner(f"Analysing '{dish_name}'…"):
        result = analyze_dish(dish_name.strip(), daily_calories, meal_fraction)

    if not result:
        st.error(f"Couldn't find **'{dish_name}'**. Try a different spelling or a more common name.")
    else:
        st.success(f"Found: **{result['name']}**")

        left, right = st.columns([1, 1])

        with left:
            if result.get("image"):
                st.image(result["image"], use_container_width=True)

        with right:
            st.subheader("Your Portion")
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #1a472a, #2d6a4f);
                    border-radius: 12px;
                    padding: 24px;
                    text-align: center;
                    margin-bottom: 12px;
                ">
                    <div style="color: #95d5b2; font-size: 14px; margin-bottom: 4px;">You can have</div>
                    <div style="color: #52b788; font-size: 36px; font-weight: bold;">{result['serving_display']}</div>
                    <div style="color: #95d5b2; font-size: 13px; margin-top: 6px;">
                        for your {result['meal_budget']} kcal meal budget
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            ca, cb = st.columns(2)
            ca.metric("Calories / serving", f"{result['cal_per_serving']} kcal")
            cb.metric("Your meal budget",   f"{result['meal_budget']} kcal")

            st.markdown("**Nutrition per serving:**")
            nc = result["nutrients_per_serving"]
            cp, cc, cf = st.columns(3)
            cp.metric("Protein", f"{nc['protein']}g")
            cc.metric("Carbs",   f"{nc['carbs']}g")
            cf.metric("Fat",     f"{nc['fat']}g")

        with st.expander("📋 Recipe ingredients"):
            ings = result.get("ingredients", [])
            if ings:
                for ing in ings:
                    st.markdown(f"- {ing}")
            else:
                st.caption("No ingredient data available.")
