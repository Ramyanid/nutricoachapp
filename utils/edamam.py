import requests

RECIPE_APP_ID  = "12c61805"
RECIPE_APP_KEY = "04d173f71065bb5e617d71cabad8c6ee"

RECIPE_HEADERS = {"Edamam-Account-User": RECIPE_APP_ID}

NUTRITION_APP_ID  = "e7e92f95"
NUTRITION_APP_KEY = "c205efd25584f54ed0dd4a7501de0c07"

HEALTH_CONDITION_MAP = {
    "Diabetes":           ["sugar-conscious", "low-sugar"],
    "High Blood Pressure":["low-sodium"],
    "High Cholesterol":   ["low-fat"],
    "PCOS":               ["sugar-conscious"],
    "Thyroid condition":  [],
    "Gluten intolerance": ["gluten-free"],
}

PIECE_KEYWORDS = [
    "idli", "roti", "chapati", "dosa", "paratha", "puri", "naan",
    "egg", "pancake", "waffle", "crepe", "bread slice",
    "cookie", "muffin", "cupcake", "donut", "bagel", "croissant",
    "burger", "sandwich", "wrap", "roll", "taco",
    "dumpling", "samosa", "spring roll",
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


def analyze_dish(dish_name, daily_calories, meal_fraction=0.35):
    params = {
        "type":    "public",
        "q":       dish_name,
        "app_id":  RECIPE_APP_ID,
        "app_key": RECIPE_APP_KEY,
    }
    try:
        resp = requests.get(
            "https://api.edamam.com/api/recipes/v2",
            params=params, headers=RECIPE_HEADERS, timeout=10
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None

    hits = resp.json().get("hits", [])
    if not hits:
        return None

    r = hits[0]["recipe"]
    parsed = _parse_recipe(r)

    servings         = parsed["servings"]
    cal_per_serving  = parsed["cal_per_serving"] or 1
    total_weight     = parsed["total_weight"]
    weight_per_srv   = total_weight / servings if total_weight else 0

    meal_budget       = round(daily_calories * meal_fraction)
    servings_allowed  = meal_budget / cal_per_serving

    dish_lower = dish_name.lower()
    is_piece   = any(kw in dish_lower for kw in PIECE_KEYWORDS)

    if is_piece:
        # servings_allowed is already in portion units — do NOT multiply by yield
        if servings_allowed < 0.75:
            weight_note = f" (~{round(weight_per_srv * servings_allowed)}g)" if weight_per_srv else ""
            serving_display = f"½ piece{weight_note}"
        else:
            n = max(round(servings_allowed), 1)
            weight_note = f" (~{round(weight_per_srv * n)}g)" if weight_per_srv else ""
            serving_display = f"{n} piece{'s' if n != 1 else ''}{weight_note}"
    elif weight_per_srv > 0:
        grams = weight_per_srv * servings_allowed
        cups  = round(grams / 240, 1)
        if cups < 0.5:
            serving_display = f"{round(grams)}g (~{round(cups * 16)} tbsp)"
        else:
            serving_display = f"{cups} cup{'s' if cups != 1.0 else ''} (~{round(grams)}g)"
    else:
        n = round(servings_allowed, 1)
        serving_display = f"{n} serving{'s' if n != 1 else ''}"

    nutrients = r.get("totalNutrients", {})
    return {
        "name":            parsed["name"],
        "cal_per_serving": cal_per_serving,
        "servings_allowed":round(servings_allowed, 1),
        "serving_display": serving_display,
        "meal_budget":     meal_budget,
        "image":           parsed["image"],
        "ingredients":     parsed["ingredients"],
        "nutrients_per_serving": {
            "protein": round(nutrients.get("PROCNT", {}).get("quantity", 0) / servings),
            "carbs":   round(nutrients.get("CHOCDF", {}).get("quantity", 0) / servings),
            "fat":     round(nutrients.get("FAT",    {}).get("quantity", 0) / servings),
        },
    }
