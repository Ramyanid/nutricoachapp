import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.edamam import search_recipes, analyze_dish
from utils.database import load_latest_profile as load_profile

st.set_page_config(page_title="Kitchen Mode — NutriCoach", page_icon="🍳", layout="wide")
st.title("🍳 Meal Planner")

if "profile" not in st.session_state:
    saved = load_profile()
    if saved:
        st.session_state.profile = saved

if "profile" not in st.session_state:
    st.warning("⚠️ Complete your **Setup** first!")
    st.stop()

profile        = st.session_state.profile
daily_calories = st.session_state.get("daily_calories", profile["base_calories"])

st.info(f"Calorie budget today: **{daily_calories} kcal** · Diet: **{profile['diet_pref']}**")

# ── Mode selector ──────────────────────────────────────────────────────────────
mode = st.radio(
    "What would you like to do?",
    ["🍳 Find recipes from my kitchen ingredients", "🔍 Look up how much of a dish I can eat"],
    horizontal=True,
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# KITCHEN MODE
# ══════════════════════════════════════════════════════════════════════════════
if mode == "🍳 Find recipes from my kitchen ingredients":
    st.subheader("What's in your kitchen?")

    INGREDIENT_CATEGORIES = {
        "🥩 Proteins": [
            "Chicken", "Eggs", "Tofu", "Paneer", "Fish", "Shrimp",
            "Lentils", "Chickpeas", "Kidney beans", "Turkey", "Lamb", "Tuna",
        ],
        "🥦 Vegetables": [
            "Spinach", "Broccoli", "Tomatoes", "Onions", "Garlic",
            "Bell peppers", "Zucchini", "Carrots", "Cauliflower", "Peas",
            "Mushrooms", "Eggplant", "Cabbage", "Kale", "Cucumber",
        ],
        "🌾 Grains & Carbs": [
            "Rice", "Pasta", "Oats", "Bread", "Quinoa",
            "Sweet potato", "Potatoes", "Noodles", "Wheat flour",
        ],
        "🥛 Dairy": [
            "Milk", "Yogurt", "Cheese", "Butter",
            "Almond milk", "Coconut milk", "Greek yogurt",
        ],
        "🫙 Pantry": [
            "Olive oil", "Coconut oil", "Soy sauce", "Tomato paste",
            "Canned tomatoes", "Vegetable broth", "Cumin", "Turmeric",
            "Coriander", "Ginger", "Chilli",
        ],
    }

    selected = []
    cols = st.columns(len(INGREDIENT_CATEGORIES))
    for i, (cat, items) in enumerate(INGREDIENT_CATEGORIES.items()):
        with cols[i]:
            st.markdown(f"**{cat}**")
            picks = st.multiselect("pick", items, key=f"ing_{i}", label_visibility="collapsed")
            selected.extend(picks)

    custom = st.text_input("Other ingredients (comma-separated)", placeholder="e.g. avocado, lime, coriander")
    if custom:
        selected.extend([x.strip() for x in custom.split(",") if x.strip()])

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        km_meal_label = st.selectbox(
            "Meal slot",
            ["🌅 Breakfast  (25%)", "☀️ Lunch / Dinner  (35%)", "🍎 Snack  (10%)"],
            key="km_meal_slot",
        )
        KM_MEAL_FRACTIONS = {
            "🌅 Breakfast  (25%)":      0.25,
            "☀️ Lunch / Dinner  (35%)": 0.35,
            "🍎 Snack  (10%)":          0.10,
        }
        km_meal_budget = round(daily_calories * KM_MEAL_FRACTIONS[km_meal_label])
        st.caption(f"Budget for this slot: **{km_meal_budget} kcal**")
    with c2:
        cuisine_options = ["Any"] + (profile.get("cuisine_prefs") or ["Indian", "Mediterranean"])
        cuisine = st.selectbox("Cuisine for today", cuisine_options)
    with c3:
        num_recipes = st.slider("Number of recipes", min_value=1, max_value=5, value=3)

    if selected:
        st.caption(f"Selected: {', '.join(selected)}")

    if st.button("🔍 Find Recipes", type="primary", disabled=not selected, use_container_width=True):
        with st.spinner("Finding recipes…"):
            recipes, api_error = search_recipes(
                ingredients=selected,
                meal_budget=km_meal_budget,
                diet_pref=profile["diet_pref"],
                health_conditions=profile.get("health_conditions", []),
                cuisine=cuisine,
                num_results=num_recipes,
            )

        if api_error:
            st.error(f"API error: {api_error}")
        elif not recipes:
            st.warning("No recipes matched. Try changing cuisine to 'Any' or adding more ingredients.")
        else:
            st.success(f"Found {len(recipes)} recipe{'s' if len(recipes) > 1 else ''}!")
            for recipe in recipes:
                with st.expander(f"🍽️ **{recipe['name']}** — {recipe['cal_per_serving']} kcal / serving", expanded=True):
                    rc1, rc2, rc3 = st.columns(3)

                    with rc1:
                        if recipe["image"]:
                            st.image(recipe["image"], use_container_width=True)

                    with rc2:
                        st.markdown(f"**Cuisine:** {recipe['cuisine'] or '—'}")
                        st.markdown(f"**Servings:** {recipe['servings']}")
                        st.markdown(f"**Total:** {recipe['calories']} kcal")
                        st.markdown(f"**Per serving:** {recipe['cal_per_serving']} kcal")
                        n, srv = recipe["nutrients"], recipe["servings"]
                        st.markdown(
                            f"**Macros/serving:** "
                            f"P {round(n['protein']/srv)}g · "
                            f"C {round(n['carbs']/srv)}g · "
                            f"F {round(n['fat']/srv)}g"
                        )

                    with rc3:
                        st.markdown("**Ingredients:**")
                        for ing in recipe["ingredients"][:8]:
                            st.markdown(f"- {ing}")
                        if len(recipe["ingredients"]) > 8:
                            st.markdown(f"*…and {len(recipe['ingredients']) - 8} more*")

                    if recipe["url"]:
                        st.link_button("📖 Full Recipe & Steps", recipe["url"])
    elif not selected:
        st.caption("👆 Select at least one ingredient to get started.")

# ══════════════════════════════════════════════════════════════════════════════
# DISH LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.subheader("How much of a dish can I eat?")

    MEAL_FRACTIONS = {
        "🌅 Breakfast  (25% of daily)":      0.25,
        "☀️ Lunch / Dinner  (35% of daily)": 0.35,
        "🍎 Snack  (10% of daily)":          0.10,
    }

    dl1, dl2 = st.columns([2, 1])
    with dl1:
        dish_name = st.text_input(
            "Dish name",
            placeholder="e.g. butter chicken, idli sambar, caesar salad, pasta carbonara",
        )
    with dl2:
        meal_label    = st.selectbox("Meal slot", list(MEAL_FRACTIONS.keys()))
        meal_fraction = MEAL_FRACTIONS[meal_label]
        meal_budget   = round(daily_calories * meal_fraction)
        st.caption(f"Budget for this slot: **{meal_budget} kcal**")

    if st.button("🔍 How much can I eat?", type="primary", disabled=not dish_name, use_container_width=True):
        with st.spinner(f"Looking up '{dish_name}'…"):
            result = analyze_dish(dish_name.strip(), daily_calories, meal_fraction)

        if not result:
            st.error(f"Couldn't find **'{dish_name}'**. Try a simpler or more common name.")
        else:
            st.success(f"Found: **{result['name']}**")
            res_left, res_right = st.columns(2)

            with res_left:
                if result.get("image"):
                    st.image(result["image"], use_container_width=True)

            with res_right:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #1a472a, #2d6a4f);
                        border-radius: 12px;
                        padding: 20px;
                        text-align: center;
                        margin-bottom: 12px;
                    ">
                        <div style="color:#95d5b2; font-size:13px;">You can have</div>
                        <div style="color:#52b788; font-size:32px; font-weight:bold;">{result['serving_display']}</div>
                        <div style="color:#95d5b2; font-size:12px; margin-top:4px;">
                            {meal_label.split('(')[0].strip()} · {result['meal_budget']} kcal budget
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                ca, cb = st.columns(2)
                ca.metric("Calories / serving", f"{result['cal_per_serving']} kcal")
                cb.metric("Your meal budget",   f"{result['meal_budget']} kcal")

                nc = result["nutrients_per_serving"]
                cp, cc, cf = st.columns(3)
                cp.metric("Protein", f"{nc['protein']}g")
                cc.metric("Carbs",   f"{nc['carbs']}g")
                cf.metric("Fat",     f"{nc['fat']}g")

            with st.expander("📋 Ingredients"):
                for ing in result.get("ingredients", []):
                    st.markdown(f"- {ing}")
    elif not dish_name:
        st.caption("👆 Type a dish name above to get started.")
