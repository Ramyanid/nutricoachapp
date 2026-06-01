import requests
import streamlit as st

RECIPE_APP_ID  = st.secrets["RECIPE_APP_ID"]
RECIPE_APP_KEY = st.secrets["RECIPE_APP_KEY"]

RECIPE_HEADERS = {"Edamam-Account-User": RECIPE_APP_ID}

NUTRITION_APP_ID  = st.secrets["NUTRITION_APP_ID"]
NUTRITION_APP_KEY = st.secrets["NUTRITION_APP_KEY"]

HEALTH_CONDITION_MAP = {
    "Diabetes":           ["sugar-conscious", "low-sugar"],
    "High Blood Pressure":["low-sodium"],
    "High Cholesterol":   ["low-fat"],
    "PCOS":               ["sugar-conscious"],
    "Thyroid condition":  [],
    "Gluten intolerance": ["gluten-free"],
}

PIECE_KEYWORDS = [
    # Indian breads & snacks
    "idli", "roti", "chapati", "dosa", "paratha", "puri", "naan",
    "uttapam", "appam", "vada", "bhatura", "kulcha", "thepla",
    "samosa", "kachori", "poha", "upma",
    # Indian sweets (piece-based)
    "ladoo", "barfi", "gulab jamun", "rasgulla", "jalebi",
    # Eggs & breakfast items
    "egg", "omelette", "pancake", "waffle", "crepe", "toast",
    "french toast", "poached egg", "boiled egg",
    # Baked goods
    "cookie", "muffin", "cupcake", "donut", "bagel", "croissant",
    "brownie", "slice of cake", "bread slice", "biscuit",
    # Mains & street food
    "burger", "sandwich", "wrap", "roll", "taco", "pizza",
    "dumpling", "spring roll", "kebab", "skewer",
    "pita", "gyoza", "empanada",
]


def _build_health_labels(health_conditions, diet_pref):
    labels = []
    for condition in health_conditions:
        if condition != "None":
            labels.extend(HEALTH_CONDITION_MAP.get(condition, []))
    if diet_pref == "Vegetarian":
        labels.append("vegetarian")
    elif diet_pref == "Vegan":
        labels.append("vegan")
    return list(set(labels))


def _parse_recipe(r):
    servings = r.get("yield", 1) or 1
    total_cals = r.get("calories", 0)
    nutrients = r.get("totalNutrients", {})
    return {
        "name":           r["label"],
        "calories":       round(total_cals),
        "servings":       servings,
        "cal_per_serving":round(total_cals / servings),
        "image":          r.get("image", ""),
        "url":            r.get("url", ""),
        "ingredients":    r.get("ingredientLines", []),
        "nutrients": {
            "protein": round(nutrients.get("PROCNT", {}).get("quantity", 0)),
            "carbs":   round(nutrients.get("CHOCDF", {}).get("quantity", 0)),
            "fat":     round(nutrients.get("FAT",    {}).get("quantity", 0)),
        },
        "cuisine":       r.get("cuisineType", [""])[0].title() if r.get("cuisineType") else "",
        "total_weight":  r.get("totalWeight", 0),
    }


def search_recipes(ingredients, meal_budget, diet_pref, health_conditions, cuisine, num_results=5):
    params = {
        "type":    "public",
        "q":       " ".join(ingredients[:10]),
        "app_id":  RECIPE_APP_ID,
        "app_key": RECIPE_APP_KEY,
        "random":  "true",
    }
    if cuisine and cuisine != "Any":
        params["cuisineType"] = cuisine.lower()

    health_labels = _build_health_labels(health_conditions, diet_pref)
    if health_labels:
        params["health"] = health_labels

    try:
        resp = requests.get(
            "https://api.edamam.com/api/recipes/v2",
            params=params, headers=RECIPE_HEADERS, timeout=10
        )
        if not resp.ok:
            return [], f"API error {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as e:
        return [], f"Network error: {e}"

    # Fetch more results so we have enough after filtering by cal_per_serving
    hits = resp.json().get("hits", [])[:20]
    recipes = [_parse_recipe(h["recipe"]) for h in hits]

    # Filter to recipes whose per-serving calories fit within ±40% of the meal budget
    cal_min = meal_budget * 0.5
    cal_max = meal_budget * 1.4
    filtered = [r for r in recipes if cal_min <= r["cal_per_serving"] <= cal_max]

    # If nothing passes the filter, relax and return closest matches
    if not filtered:
        filtered = sorted(recipes, key=lambda r: abs(r["cal_per_serving"] - meal_budget))

    return filtered[:num_results], None


def _nutrition_api_lookup(query):
    """Call Nutrition Analysis API for a single ingredient query like '1 idli' or '1 cup rice'."""
    try:
        resp = requests.post(
            "https://api.edamam.com/api/nutrition-details",
            params={"app_id": NUTRITION_APP_ID, "app_key": NUTRITION_APP_KEY},
            json={"ingr": [query], "title": query},
            timeout=10,
        )
        if not resp.ok:
            return None
        data     = resp.json()
        parsed   = data.get("ingredients", [{}])[0].get("parsed", [{}])[0]
        if parsed.get("status") != "OK":
            return None
        nutrients = parsed.get("nutrients", {})
        kcal      = nutrients.get("ENERC_KCAL", {}).get("quantity", 0)
        if not kcal:
            return None
        return {
            "food":    parsed.get("food", query).title(),
            "kcal":    round(kcal),
            "weight":  round(parsed.get("weight", 0)),
            "protein": round(nutrients.get("PROCNT", {}).get("quantity", 0)),
            "carbs":   round(nutrients.get("CHOCDF", {}).get("quantity", 0)),
            "fat":     round(nutrients.get("FAT",    {}).get("quantity", 0)),
        }
    except requests.RequestException:
        return None


def analyze_dish(dish_name, daily_calories, meal_fraction=0.35):
    meal_budget = round(daily_calories * meal_fraction)
    dish_lower  = dish_name.lower()
    is_piece    = any(kw in dish_lower for kw in PIECE_KEYWORDS)

    # Try Nutrition Analysis API first — accurate per-unit data
    unit_query = f"1 {dish_name}" if is_piece else f"1 cup {dish_name}"
    unit_data  = _nutrition_api_lookup(unit_query)

    # Fallback: try recipe search API if nutrition API can't parse the dish
    if not unit_data:
        unit_data = _recipe_fallback(dish_name)

    if not unit_data:
        return None

    cal_per_unit     = unit_data["kcal"] or 1
    units_allowed    = meal_budget / cal_per_unit

    if is_piece:
        if units_allowed < 0.75:
            serving_display = f"½ {dish_name} (~{cal_per_unit} kcal each)"
        elif units_allowed < 1.5:
            serving_display = f"1 {dish_name} (~{cal_per_unit} kcal each)"
        else:
            n = round(units_allowed)
            serving_display = f"{n} {dish_name}s (~{cal_per_unit} kcal each)"
    else:
        cups = round(units_allowed, 1)
        if cups < 0.5:
            tbsp = round(cups * 16)
            serving_display = f"{tbsp} tablespoons (~{cal_per_unit} kcal per cup)"
        elif cups == 1.0:
            serving_display = f"1 cup (~{cal_per_unit} kcal per cup)"
        else:
            serving_display = f"{cups} cups (~{cal_per_unit} kcal per cup)"

    # Fetch image + ingredients from recipe search (nutrition API has none)
    recipe_extra = _recipe_fallback(dish_name)

    return {
        "name":            unit_data["food"],
        "cal_per_serving": cal_per_unit,
        "servings_allowed":round(units_allowed, 1),
        "serving_display": serving_display,
        "meal_budget":     meal_budget,
        "image":           recipe_extra.get("image", "") if recipe_extra else "",
        "ingredients":     recipe_extra.get("ingredients", []) if recipe_extra else [],
        "nutrients_per_serving": {
            "protein": unit_data["protein"],
            "carbs":   unit_data["carbs"],
            "fat":     unit_data["fat"],
        },
    }


def _recipe_fallback(dish_name):
    """Fallback to recipe search when nutrition API can't identify the dish."""
    try:
        resp = requests.get(
            "https://api.edamam.com/api/recipes/v2",
            params={"type": "public", "q": dish_name,
                    "app_id": RECIPE_APP_ID, "app_key": RECIPE_APP_KEY},
            headers=RECIPE_HEADERS, timeout=10,
        )
        if not resp.ok:
            return None
        hits = resp.json().get("hits", [])
        if not hits:
            return None
        r        = hits[0]["recipe"]
        parsed   = _parse_recipe(r)
        servings = parsed["servings"]
        nutrients = r.get("totalNutrients", {})
        return {
            "food":        parsed["name"],
            "kcal":        parsed["cal_per_serving"],
            "weight":      round(parsed["total_weight"] / servings) if parsed["total_weight"] else 0,
            "protein":     round(nutrients.get("PROCNT", {}).get("quantity", 0) / servings),
            "carbs":       round(nutrients.get("CHOCDF", {}).get("quantity", 0) / servings),
            "fat":         round(nutrients.get("FAT",    {}).get("quantity", 0) / servings),
            "image":       parsed["image"],
            "ingredients": parsed["ingredients"],
        }
    except requests.RequestException:
        return None
