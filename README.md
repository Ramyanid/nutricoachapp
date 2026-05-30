# NutriCoach 🥗

A personalised nutrition and fitness Streamlit app that calculates your daily calorie budget, suggests healthy recipes from your kitchen ingredients, and tells you exactly how much of any dish you can eat.

---

## Features

- **One-time Profile Setup** — enter your height, weight, age, sex, activity level, health conditions, fitness goal, diet preference, and cuisine preferences. Your profile is saved locally and persists across sessions.
- **Daily Dashboard** — choose your daily focus (muscle tightening, core + fat loss, weight loss, body toning, or rest day), log your workout, and get a net calorie budget with macro targets and a per-meal breakdown.
- **Kitchen Mode** — select ingredients you have at home, pick a meal slot and cuisine, and get recipe suggestions filtered to your calorie budget, diet, and health conditions via the Edamam API.
- **Dish Lookup** — type any dish name and get an accurate portion size (in pieces or cups) based on your remaining meal budget for that slot.

---

## Tech Stack

| Layer | Tool |
|---|---|
| UI & server | [Streamlit](https://streamlit.io) |
| Recipe & nutrition data | [Edamam Recipe Search API](https://developer.edamam.com) |
| Calorie calculation | Mifflin-St Jeor BMR formula |
| Profile persistence | Local JSON file |
| Language | Python 3.10+ |

---

## Project Structure

```
nutricoachapp/
├── app.py                  # Home page
├── requirements.txt
├── pages/
│   ├── 1_Setup.py          # Profile onboarding
│   ├── 2_Dashboard.py      # Daily calorie & macro planner
│   ├── 3_Kitchen_Mode.py   # Recipe search + dish lookup
│   └── 4_Dish_Lookup.py    # (standalone dish lookup page)
└── utils/
    ├── nutrition.py        # BMR, TDEE, macro calculations
    ├── edamam.py           # Edamam API wrapper
    └── storage.py          # Profile save/load (JSON)
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Ramyanid/nutricoachapp.git
cd nutricoachapp
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Edamam API keys

Create a file at `.streamlit/secrets.toml`:

```toml
RECIPE_APP_ID  = "your_recipe_app_id"
RECIPE_APP_KEY = "your_recipe_app_key"

NUTRITION_APP_ID  = "your_nutrition_app_id"
NUTRITION_APP_KEY = "your_nutrition_app_key"
```

Get free API keys at [developer.edamam.com](https://developer.edamam.com) — you need the **Recipe Search API** and the **Nutrition Analysis API**.

### 4. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## How It Works

### Calorie Calculation

| Step | Formula |
|---|---|
| BMR | Mifflin-St Jeor (sex-adjusted) |
| TDEE | BMR × activity multiplier |
| Goal adjustment | −500 kcal (weight loss) to +250 kcal (muscle building) |
| Focus adjustment | Additional ±150–350 kcal based on daily focus |
| Workout | Estimated burn added back so deficit stays consistent |
| Floor | 1200 kcal (female) / 1500 kcal (male) minimum |

### Daily Focus Options

| Focus | Effect |
|---|---|
| Muscle tightening | +150 kcal · high protein macros |
| Core + fat loss | −250 kcal · low carb |
| Overall weight loss | −350 kcal · balanced |
| Body toning | −150 kcal · balanced |
| Rest day | −100 kcal · higher carbs |

---

## Deploying to Streamlit Community Cloud

1. Push your code to GitHub (secrets.toml is gitignored — never committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. In **App Settings → Secrets**, paste the contents of your `secrets.toml`.
4. Deploy.

---

## Health Condition Filters

The app maps health conditions to Edamam API health labels to filter recipes:

| Condition | Filter applied |
|---|---|
| Diabetes | sugar-conscious, low-sugar |
| High Blood Pressure | low-sodium |
| High Cholesterol | low-fat |
| PCOS | sugar-conscious |
| Gluten intolerance | gluten-free |
