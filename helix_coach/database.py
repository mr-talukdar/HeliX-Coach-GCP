import os
import sqlalchemy
from google.cloud.alloydb.connector import Connector, IPTypes # Added IPTypes

# --- CONFIGURATION ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = "us-east4"    
CLUSTER = "helix-database"      
INSTANCE = "helix-database-primary" # Ensure this is correct!
DB_USER = "postgres"
DB_PASS = "Kula8#%47"  # Ensure this is correct!
DB_NAME = "postgres"

connector = None
pool = None

def init_pool_and_db():
    global connector, pool
    if pool is not None:
        return pool
        
    print("Connecting to AlloyDB...")
    connector = Connector()
    
    def getconn():
        return connector.connect(
            f"projects/{PROJECT_ID}/locations/{REGION}/clusters/{CLUSTER}/instances/{INSTANCE}",
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            enable_iam_auth=False,
            ip_type=IPTypes.PUBLIC  # <--- THIS IS THE MAGIC FIX
        )
    
    pool = sqlalchemy.create_engine("postgresql+pg8000://", creator=getconn)
    
    # Create the table if it doesn't exist yet
    print("Executing table creation/check...")
    with pool.connect() as db_conn:
        db_conn.execute(sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS users (name VARCHAR(50) PRIMARY KEY, goal VARCHAR(255))"
        ))
   
        db_conn.execute(sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS workouts (username VARCHAR(50), day VARCHAR(20), workout_text TEXT, PRIMARY KEY (username, day))"
        ))
        db_conn.commit()
    print("Database ready!")
        
    return pool

# --- ADK TOOLS ---
def save_user_context(name: str, goal: str) -> str:
    try:
        db_pool = init_pool_and_db() 
        with db_pool.connect() as db_conn:
            db_conn.execute(
                sqlalchemy.text("INSERT INTO users (name, goal) VALUES (:name, :goal) ON CONFLICT (name) DO UPDATE SET goal = EXCLUDED.goal"),
                {"name": name, "goal": goal}
            )
            db_conn.commit()
        return f"Successfully saved {name}'s goal to AlloyDB."
    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        print(error_msg) # Prints to your terminal so you can see it
        return error_msg

def get_user_context(name: str) -> str:
    try:
        db_pool = init_pool_and_db() 
        with db_pool.connect() as db_conn:
            result = db_conn.execute(
                sqlalchemy.text("SELECT goal FROM users WHERE name = :name"),
                {"name": name}
            ).fetchone()
            if result:
                return f"User {name} has a current goal of: {result[0]}"
            return "User not found in database."
    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        print(error_msg)
        return error_msg

def save_daily_workout(username: str, day: str, workout_text: str) -> str:
    """Saves a generated workout for a specific day of the week to the database."""
    try:
        db_pool = init_pool_and_db() 
        with db_pool.connect() as db_conn:
            db_conn.execute(
                sqlalchemy.text("INSERT INTO workouts (username, day, workout_text) VALUES (:username, :day, :workout_text) ON CONFLICT (username, day) DO UPDATE SET workout_text = EXCLUDED.workout_text"),
                {"username": username.lower(), "day": day.lower(), "workout_text": workout_text}
            )
            db_conn.commit()
        return f"Successfully saved the workout for {day}."
    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        print(error_msg)
        return error_msg

def get_daily_workout(username: str, day: str) -> str:
    """Fetches the scheduled workout for a specific day from the database."""
    try:
        db_pool = init_pool_and_db() 
        with db_pool.connect() as db_conn:
            result = db_conn.execute(
                sqlalchemy.text("SELECT workout_text FROM workouts WHERE username = :username AND day = :day"),
                {"username": username.lower(), "day": day.lower()}
            ).fetchone()
            if result:
                return result[0]
            return f"No workout found for {day}. It might be a rest day, or a routine hasn't been generated yet."
    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        print(error_msg)
        return error_msg