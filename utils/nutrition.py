def calculate_bmr(weight_kg, height_cm, age, sex):
    if sex == "Male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161


ACTIVITY_MULTIPLIERS = {
    "Sedentary (little/no exercise)": 1.2,
    "Lightly active (1-3 days/week)": 1.375,
    "Moderately active (3-5 days/week)": 1.55,
    "Very active (6-7 days/week)": 1.725,
    "Extremely active (athlete/physical job)": 1.9,
}

GOAL_ADJUSTMENTS = {
    "Overall weight loss": -500,
    "Muscle building": 250,
    "Body toning / inch loss": -200,
    "Maintenance": 0,
}

FOCUS_ADJUSTMENTS = {
    "Muscle tightening": 150,
    "Core + fat loss": -250,
    "Overall weight loss": -350,
    "Body toning": -150,
    "Rest day": -100,
}

FOCUS_MACROS = {
    "Muscle tightening":  (0.35, 0.40, 0.25),
    "Core + fat loss":    (0.40, 0.30, 0.30),
    "Overall weight loss":(0.30, 0.40, 0.30),
    "Body toning":        (0.30, 0.40, 0.30),
    "Rest day":           (0.25, 0.45, 0.30),
}

WORKOUT_BURN_RATES = {
    "Cardio": 9,
    "Strength training": 6,
    "HIIT": 11,
    "Yoga": 3,
    "Walking": 4,
    "Cycling": 8,
    "Swimming": 8,
}


def calculate_tdee(bmr, activity_level):
    return bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)


def adjust_calories_for_goal(tdee, goal):
    return tdee + GOAL_ADJUSTMENTS.get(goal, 0)


def adjust_for_daily_focus(base_calories, focus):
    return base_calories + FOCUS_ADJUSTMENTS.get(focus, 0)


def calculate_workout_burn(workout_type, duration_mins):
    return WORKOUT_BURN_RATES.get(workout_type, 6) * duration_mins


def get_macros(calories, focus):
    p_pct, c_pct, f_pct = FOCUS_MACROS.get(focus, (0.30, 0.40, 0.30))
    return {
        "protein_g": round((calories * p_pct) / 4),
        "carbs_g":   round((calories * c_pct) / 4),
        "fat_g":     round((calories * f_pct) / 9),
    }


def apply_calorie_floor(calories, sex):
    floor = 1500 if sex == "Male" else 1200
    return max(calories, floor)
