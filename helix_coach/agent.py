from google.adk.agents import Agent
from .calender_tools import check_todays_schedule, book_workout_session
from .database import save_user_context, get_user_context, save_daily_workout, get_daily_workout
# ==========================================
# 1. DEFINE TOOLS FOR EACH DOMAIN
# ==========================================

# --- Lift Performance Analysis Tools ---
def analyze_progress(current_weight: float, reps: int, target_goal: float) -> str:
    """Calculates the estimated one-repetition maximum (1RM) and assesses progress against a specified target goal.
    """
    one_rm = current_weight * (1 + reps / 30)
    percent_to_goal = (one_rm / target_goal) * 100
    return (f"Estimated 1RM: {one_rm:.2f}kg. "
            f"You are {percent_to_goal:.1f}% of the way to your {target_goal}kg goal!")

# --- Nutrition Planning Tools ---
def calculate_macros(current_weight: float, target_weight: float, activity_level: str) -> str:
    """Calculates daily macronutrient and caloric intake recommendations based on current and target body weight.
    """
    # This implementation uses a simplified calculation model for demonstration purposes.
    protein = target_weight * 2.2 # 2.2g per kg of target weight
    
    if target_weight < current_weight:
        calories = target_weight * 25 # Deficit multiplier
        return f"To cut down to {target_weight}kg, aim for {calories} kcal/day with at least {protein:.0f}g of protein."
    else:
        calories = target_weight * 30 # Maintenance/Surplus
        return f"To build up to {target_weight}kg, aim for {calories} kcal/day with {protein:.0f}g of protein."


def adapt_workout_for_fatigue(baseline_workout: str, readiness_score: int) -> str:
    """Adjusts the prescribed workout volume and intensity based on the user's daily readiness score.
    """
    if readiness_score >= 80:
        return f"🟢 GREEN LIGHT (Score {readiness_score}): Push hard today! You are cleared for a PR attempt. \nBaseline: {baseline_workout}"
    elif readiness_score >= 50:
        return f"🟡 YELLOW LIGHT (Score {readiness_score}): Standard training day. Stick to the prescribed reps and leave 1-2 reps in the tank. \nBaseline: {baseline_workout}"
    else:
        return f"🔴 RED LIGHT (Score {readiness_score}): High fatigue detected. DELOAD PROTOCOL ENGAGED. \nModified Plan: Drop all working weights by 20% and remove 1 working set from all exercises. \nOriginal was: {baseline_workout}"


# --- Readiness Assessment Tools ---
def assess_readiness(sleep_hours: float, soreness_1_to_10: int) -> str:
    """Calculates a daily readiness score to inform appropriate training intensity and volume.
    """
    score = 100
    if sleep_hours < 7:
        score -= (7 - sleep_hours) * 10
    score -= (soreness_1_to_10 * 5)
    
    if score > 80:
        return f"Readiness Score: {score}/100. You are primed for a heavy PR attempt today!"
    elif score > 50:
        return f"Readiness Score: {score}/100. Moderate fatigue. Stick to your planned working sets, no 1RM testing."
    else:
        return f"Readiness Score: {score}/100. High fatigue detected. Recommend an active recovery day or mobility work."


# ==========================================
# 2. DEFINE THE SPECIALIZED SUB-AGENTS
# ==========================================

lift_specialist = Agent(
    name="lift_specialist",
    model="gemini-2.5-flash", # Updated model name for consistency/latest
    instruction="""You are an expert strength coach. 
    Your primary function is to analyze strength training performance data and calculate estimated one-repetition maximums (1RM) using the available tools.""",
    tools=[analyze_progress]
)

schedule_specialist = Agent(
    name="schedule_specialist",
    model="gemini-2.5-flash",
    instruction="""You are the LeanX Logistics and Scheduling Expert.
    
    When a user asks about scheduling a workout:
    1. Use the `check_todays_schedule` tool to see when they are busy today.
    2. Suggest a 90-minute block that DOES NOT overlap with their existing events.
    3. If the user agrees to a time, use the `book_workout_session` tool to lock it into their Google Calendar. (Remember to format the times as ISO strings for the tool).
    """,
    tools=[check_todays_schedule, book_workout_session]
)

nutrition_specialist = Agent(
    name="nutrition_specialist",
    model="gemini-2.5-flash", # Updated model name for consistency/latest
    instruction="""You function as a sports nutritionist. Your responsibilities include calculating macronutrient targets based on user weight goals and providing dietary recommendations, such as high-protein food options, upon request.""",
    tools=[calculate_macros]
)

readiness_specialist = Agent(
    name="readiness_specialist",
    model="gemini-2.5-flash", # Updated model name for consistency/latest
    instruction="""You are tasked with assessing central nervous system and muscular fatigue levels.
    Prior to providing any recommendations, you must inquire about the user's sleep duration (in hours) and their perceived soreness level (on a scale of 1 to 10).""",
    tools=[assess_readiness]
)

routine_generator = Agent(
    name="routine_generator",
    model="gemini-2.5-flash",
    instruction="""You are a Master Strength Programmer. 
    Your job is to generate long-term training blocks based on the user's goal.
    
    CCRITICAL DATABASE RULE:
    When you generate a new weekly routine, you MUST use the `save_daily_workout` tool to individually save the workout plan for EACH day of the week to the database. 
    Once all days are successfully saved, give the user a brief summary of the routine and STOP. Do not generate the text twice.""",
    tools=[save_daily_workout]
)

routine_editor = Agent(
    name="routine_editor",
    model="gemini-2.5-flash",
    instruction="""You are the Auto-Regulation Specialist.
    When the user asks "What am I doing today?":
    1. Check what day of the week it is, and ensure you know the user's name.
    2. Use the `get_daily_workout` tool to pull their exact prescribed workout from the database.
    3. Check their fatigue/readiness score (coordinate with the readiness_specialist).
    4. If their readiness score is below 50, use the `adapt_workout_for_fatigue` tool to modify the workout you pulled from the database.
    5. Present the final, adapted workout to the user.""",
    tools=[get_daily_workout, adapt_workout_for_fatigue] 
)


# ==========================================
# 3. DEFINE THE ROOT ORCHESTRATOR
# ==========================================

root_agent = Agent(
    name="leanx_coach",
    model="gemini-2.5-flash",
    instruction="""You are the LeanX Head Coach orchestrating a team of specialists. 
    
    CRITICAL ONBOARDING RULE (APPLY ONLY ONCE): 
    1. INITIALIZATION: On the VERY FIRST message of the conversation, use the `get_user_context` tool to check your AlloyDB memory for the user. 
    2. GREETING: Welcome them back if found, or ask for their name/goal if not found (and use `save_user_context`).
    3. ANTI-LOOP: Do NOT repeat this greeting on every message. Once the user is greeted, stop checking the context tool unless specifically asked.
    
    DELEGATION: Route user queries to the right sub-agent:
       - Creating a multi-week plan -> 'routine_generator'
       - "What is my workout today?" -> 'routine_editor'
       - Lift progress / 1RM tracking -> 'lift_specialist'
       - Scheduling -> 'schedule_specialist'
       - Diet / Macros -> 'nutrition_specialist'
       - Fatigue assessment -> 'readiness_specialist'
       
    When a specialist finishes a task and returns control to you, simply present their final output to the user. Do not restart the greeting protocol.""",
       
    tools=[save_user_context, get_user_context], 
    
    sub_agents=[
        lift_specialist, 
        schedule_specialist, 
        nutrition_specialist, 
        readiness_specialist, 
        routine_generator, 
        routine_editor
    ]
)