import math
from google.adk.agents import Agent
from .calendar_tools import check_todays_schedule, book_workout_session
from .database import (
    save_user_context, get_user_context,
    save_daily_workout, get_daily_workout,
    log_completed_workout, get_exercise_history, get_personal_records,
    save_readiness_log, get_readiness_trend,
)



def analyze_progress(current_weight: float, reps: int, target_goal: float) -> str:
    """Calculates the estimated one-repetition maximum (1RM) using the Epley formula
    and assesses progress against a specified target goal.

    Args:
        current_weight: The weight lifted in kilograms.
        reps: The number of repetitions completed.
        target_goal: The target 1RM goal in kilograms.
    """
    one_rm = current_weight * (1 + reps / 30)
    percent_to_goal = (one_rm / target_goal) * 100
    return (f"Estimated 1RM: {one_rm:.2f}kg. "
            f"You are {percent_to_goal:.1f}% of the way to your {target_goal}kg goal!")


def calculate_macros(
    current_weight: float,
    target_weight: float,
    activity_level: str,
    age: int = 25,
    height_cm: float = 175.0,
    sex: str = "male"
) -> str:
    """Calculates daily macronutrient and caloric intake recommendations based on
    user profile data using the Mifflin-St Jeor equation.

    Args:
        current_weight: Current body weight in kilograms.
        target_weight: Target body weight in kilograms.
        activity_level: One of 'sedentary', 'light', 'moderate', 'active', 'very_active'.
        age: User's age in years. Defaults to 25.
        height_cm: User's height in centimeters. Defaults to 175.
        sex: 'male' or 'female'. Defaults to 'male'.
    """
    if sex.lower() == "male":
        bmr = (10 * current_weight) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * current_weight) + (6.25 * height_cm) - (5 * age) - 161

    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    multiplier = multipliers.get(activity_level.lower(), 1.55)
    tdee = bmr * multiplier

    protein = target_weight * 2.2

    if target_weight < current_weight:
        calories = int(tdee * 0.80)
        fat = current_weight * 0.8  # 0.8g per kg
        carbs = (calories - (protein * 4) - (fat * 9)) / 4
        phase = "Cut"
        return (
            f"🔥 **{phase} Plan** (20% deficit)\n"
            f"Target Calories: {calories} kcal/day\n"
            f"Protein: {protein:.0f}g | Fat: {fat:.0f}g | Carbs: {max(carbs, 50):.0f}g\n"
            f"Based on TDEE: {tdee:.0f} kcal (BMR: {bmr:.0f}, Activity: {activity_level})"
        )
    elif target_weight > current_weight:
        calories = int(tdee * 1.10)
        fat = current_weight * 1.0
        carbs = (calories - (protein * 4) - (fat * 9)) / 4
        phase = "Lean Bulk"
        return (
            f"💪 **{phase} Plan** (10% surplus)\n"
            f"Target Calories: {calories} kcal/day\n"
            f"Protein: {protein:.0f}g | Fat: {fat:.0f}g | Carbs: {max(carbs, 100):.0f}g\n"
            f"Based on TDEE: {tdee:.0f} kcal (BMR: {bmr:.0f}, Activity: {activity_level})"
        )
    else:
        calories = int(tdee)
        fat = current_weight * 0.9
        carbs = (calories - (protein * 4) - (fat * 9)) / 4
        return (
            f"⚖️ **Maintenance / Recomp Plan**\n"
            f"Target Calories: {calories} kcal/day\n"
            f"Protein: {protein:.0f}g | Fat: {fat:.0f}g | Carbs: {max(carbs, 100):.0f}g\n"
            f"Based on TDEE: {tdee:.0f} kcal (BMR: {bmr:.0f}, Activity: {activity_level})"
        )


def adapt_workout_for_fatigue(baseline_workout: str, readiness_score: int) -> str:
    """Adjusts the prescribed workout volume and intensity based on the user's daily readiness score.

    Args:
        baseline_workout: The originally prescribed workout text.
        readiness_score: The calculated readiness score (0-100).
    """
    if readiness_score >= 80:
        return (f"🟢 GREEN LIGHT (Score {readiness_score}): Push hard today! "
                f"You are cleared for a PR attempt.\nBaseline: {baseline_workout}")
    elif readiness_score >= 50:
        return (f"🟡 YELLOW LIGHT (Score {readiness_score}): Standard training day. "
                f"Stick to the prescribed reps and leave 1-2 reps in the tank.\n"
                f"Baseline: {baseline_workout}")
    else:
        return (f"🔴 RED LIGHT (Score {readiness_score}): High fatigue detected. "
                f"DELOAD PROTOCOL ENGAGED.\n"
                f"Modified Plan: Drop all working weights by 20% and remove 1 working set "
                f"from all exercises.\nOriginal was: {baseline_workout}")


def assess_readiness(user_id: str, sleep_hours: float, soreness_1_to_10: int) -> str:
    """Calculates a daily readiness score to inform appropriate training intensity and volume.
    Automatically persists the result for trend tracking.

    Args:
        user_id: The authenticated user's unique ID.
        sleep_hours: Number of hours of sleep the user got last night.
        soreness_1_to_10: Perceived muscle soreness on a scale of 1 (none) to 10 (extreme).
    """
    score = 100
    if sleep_hours < 7:
        score -= int((7 - sleep_hours) * 10)
    if sleep_hours < 5:
        score -= 10  # Extra penalty for severe sleep deprivation
    score -= (soreness_1_to_10 * 5)
    score = max(0, min(100, score))  # Clamp 0-100

    save_readiness_log(user_id, sleep_hours, soreness_1_to_10, score)

    if score > 80:
        return f"Readiness Score: {score}/100. 🟢 You are primed for a heavy PR attempt today!"
    elif score > 50:
        return f"Readiness Score: {score}/100. 🟡 Moderate fatigue. Stick to your planned working sets, no 1RM testing."
    else:
        return f"Readiness Score: {score}/100. 🔴 High fatigue detected. Recommend an active recovery day or mobility work."



lift_specialist = Agent(
    name="lift_specialist",
    model="gemini-2.5-flash",
    instruction="""You are an expert strength coach specializing in performance analysis.
    Your primary function is to analyze strength training performance data and calculate 
    estimated one-repetition maximums (1RM) using the Epley formula.
    When a user provides their lift data, use the analyze_progress tool to give them 
    actionable feedback on their progress toward their goal.""",
    tools=[analyze_progress]
)

schedule_specialist = Agent(
    name="schedule_specialist",
    model="gemini-2.5-flash",
    instruction="""You are the HeliX Logistics and Scheduling Expert.
    
    When a user asks about scheduling a workout:
    1. Use the `check_todays_schedule` tool to see when they are busy today.
       Pass the user_id from the session context.
    2. Suggest a 90-minute block that DOES NOT overlap with their existing events.
    3. If the user agrees to a time, use the `book_workout_session` tool to lock it 
       into their Google Calendar. Format times as ISO strings and pass the user's timezone.
    
    IMPORTANT: Always pass the user_id parameter when calling calendar tools.""",
    tools=[check_todays_schedule, book_workout_session]
)

nutrition_specialist = Agent(
    name="nutrition_specialist",
    model="gemini-2.5-flash",
    instruction="""You are HeliX's sports nutritionist. Your job is to calculate accurate 
    macronutrient targets using the Mifflin-St Jeor equation.
    
    To provide accurate recommendations, you need:
    - Current weight and target weight
    - Activity level (sedentary, light, moderate, active, very_active)
    - Age, height (cm), and sex (male/female)
    
    If the user hasn't provided these, ask for them. Use the calculate_macros tool 
    with all available parameters for the most accurate results.
    Also provide practical meal suggestions and high-protein food recommendations when asked.""",
    tools=[calculate_macros]
)

readiness_specialist = Agent(
    name="readiness_specialist",
    model="gemini-2.5-flash",
    instruction="""You are HeliX's Recovery & Readiness Analyst.
    
    Your responsibilities:
    1. Assess daily CNS and muscular fatigue by asking about sleep (hours) and soreness (1-10).
    2. Use the `assess_readiness` tool to calculate the score. This automatically saves the data.
    3. You can use `get_readiness_trend` to show the user their recovery patterns over time.
    4. If readiness has been low for 3+ consecutive days, recommend a deload week.
    
    Always pass the user_id parameter when calling tools.""",
    tools=[assess_readiness, get_readiness_trend]
)

routine_generator = Agent(
    name="routine_generator",
    model="gemini-2.5-flash",
    instruction="""You are a Master Strength Programmer. 
    Your job is to generate long-term training blocks based on the user's goal.
    
    CRITICAL DATABASE RULE:
    When you generate a new weekly routine, you MUST use the `save_daily_workout` tool 
    to individually save the workout plan for EACH day of the week to the database. 
    Always pass the user_id parameter.
    Once all days are successfully saved, give the user a brief summary of the routine and STOP. 
    Do not generate the text twice.""",
    tools=[save_daily_workout]
)

routine_editor = Agent(
    name="routine_editor",
    model="gemini-2.5-flash",
    instruction="""You are the Auto-Regulation Specialist.
    When the user asks "What am I doing today?":
    1. Determine what day of the week it is.
    2. Use the `get_daily_workout` tool to pull their prescribed workout from the database.
       Pass the user_id from context.
    3. Ask them about their sleep and soreness to assess readiness.
    4. If their readiness score is below 50, use the `adapt_workout_for_fatigue` tool 
       to modify the workout you pulled from the database.
    5. Present the final, adapted workout to the user.""",
    tools=[get_daily_workout, adapt_workout_for_fatigue, assess_readiness]
)

workout_logger = Agent(
    name="workout_logger",
    model="gemini-2.5-flash",
    instruction="""You are HeliX's Workout Logger and PR Tracker.
    
    Your responsibilities:
    1. Help users log their completed exercises using `log_completed_workout`.
       For each exercise, collect: name, sets, reps, weight (kg), and optionally RPE (1-10).
    2. Show exercise history with `get_exercise_history` when users ask about past performance.
    3. Display personal records using `get_personal_records` when users want to see their PRs.
    
    After logging, congratulate them and show the estimated 1RM from the tool output.
    Always pass the user_id parameter.""",
    tools=[log_completed_workout, get_exercise_history, get_personal_records]
)



root_agent = Agent(
    name="helix_coach",
    model="gemini-2.5-flash",
    instruction="""You are the HeliX Head Coach, orchestrating a team of fitness specialists.
    
    CRITICAL ONBOARDING RULE (APPLY ONLY ONCE): 
    1. INITIALIZATION: On the VERY FIRST message of the conversation, use `get_user_context` 
       with the user_id from the session to check the database for the user.
    2. GREETING: Welcome them back if found, or ask for their name/goal if not found 
       (and use `save_user_context`).
    3. ANTI-LOOP: Do NOT repeat this greeting on every message. Once the user is greeted, 
       stop checking the context tool unless specifically asked.
    
    DELEGATION: Route user queries to the right sub-agent:
       - Creating a multi-week training plan → 'routine_generator'
       - "What is my workout today?" → 'routine_editor'
       - Lift progress / 1RM tracking → 'lift_specialist'
       - Scheduling / Calendar → 'schedule_specialist'
       - Diet / Macros / Nutrition → 'nutrition_specialist'
       - Fatigue / Recovery assessment → 'readiness_specialist'
       - "Log my workout" / "What are my PRs?" → 'workout_logger'
       
    When a specialist finishes a task and returns control to you, simply present 
    their final output to the user. Do not restart the greeting protocol.""",
       
    tools=[save_user_context, get_user_context], 
    
    sub_agents=[
        lift_specialist, 
        schedule_specialist, 
        nutrition_specialist, 
        readiness_specialist, 
        routine_generator, 
        routine_editor,
        workout_logger,
    ]
)