import os
import logging
import sqlalchemy
from google.cloud.alloydb.connector import Connector, IPTypes

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = os.getenv("ALLOYDB_REGION", "us-east4")
CLUSTER = os.getenv("ALLOYDB_CLUSTER", "helix-database")
INSTANCE = os.getenv("ALLOYDB_INSTANCE", "helix-database-primary")
DB_USER = os.getenv("DB_USER", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")


def _get_db_password() -> str:
    """Fetch DB password from environment or Google Secret Manager."""
    env_pass = os.environ.get("DB_PASS")
    if env_pass:
        return env_pass

    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{PROJECT_ID}/secrets/alloydb-password/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to fetch DB password from Secret Manager: {e}")
        raise RuntimeError(
            "DB_PASS not set in environment and Secret Manager lookup failed. "
            "Set DB_PASS env var or configure Secret Manager."
        ) from e


connector = None
pool = None


def init_pool_and_db():
    """Initialize the AlloyDB connection pool and create tables if needed."""
    global connector, pool
    if pool is not None:
        return pool

    logger.info("Connecting to AlloyDB...")
    db_pass = _get_db_password()
    connector = Connector()

    def getconn():
        return connector.connect(
            f"projects/{PROJECT_ID}/locations/{REGION}/clusters/{CLUSTER}/instances/{INSTANCE}",
            "pg8000",
            user=DB_USER,
            password=db_pass,
            db=DB_NAME,
            enable_iam_auth=False,
            ip_type=IPTypes.PUBLIC,
        )

    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )

    logger.info("Executing table creation/check...")
    with pool.connect() as db_conn:
        db_conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(128) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                display_name VARCHAR(100),
                goal VARCHAR(500),
                timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
                weight_kg DECIMAL(5,2),
                target_weight_kg DECIMAL(5,2),
                activity_level VARCHAR(20) DEFAULT 'moderate',
                age INT,
                height_cm DECIMAL(5,1),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        db_conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id VARCHAR(128) PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                encrypted_refresh_token TEXT NOT NULL,
                token_expiry TIMESTAMPTZ,
                scopes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        db_conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS workout_routines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(128) REFERENCES users(user_id) ON DELETE CASCADE,
                day VARCHAR(20) NOT NULL,
                workout_text TEXT NOT NULL,
                version INT DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, day, version)
            )
        """))

        db_conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS workout_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(128) REFERENCES users(user_id) ON DELETE CASCADE,
                date DATE NOT NULL DEFAULT CURRENT_DATE,
                exercise VARCHAR(100),
                sets INT,
                reps INT,
                weight_kg DECIMAL(5,2),
                rpe DECIMAL(3,1),
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        db_conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS readiness_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(128) REFERENCES users(user_id) ON DELETE CASCADE,
                date DATE NOT NULL DEFAULT CURRENT_DATE,
                sleep_hours DECIMAL(3,1),
                soreness_score INT CHECK (soreness_score BETWEEN 1 AND 10),
                readiness_score INT,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, date)
            )
        """))

        db_conn.commit()
    logger.info("Database ready!")

    return pool



def save_user_context(user_id: str, email: str, display_name: str, goal: str) -> str:
    """Saves or updates a user's profile and fitness goal in the database.

    Args:
        user_id: The authenticated user's unique ID (Firebase UID).
        email: The user's email address.
        display_name: The user's display name.
        goal: The user's current fitness goal description.
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            db_conn.execute(
                sqlalchemy.text("""
                    INSERT INTO users (user_id, email, display_name, goal, updated_at)
                    VALUES (:user_id, :email, :display_name, :goal, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        goal = EXCLUDED.goal,
                        updated_at = NOW()
                """),
                {"user_id": user_id, "email": email, "display_name": display_name, "goal": goal}
            )
            db_conn.commit()
        return f"Successfully saved {display_name}'s goal to the database."
    except Exception as e:
        error_msg = f"Database error saving user context: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_user_context(user_id: str) -> str:
    """Retrieves a user's profile and fitness goal from the database.

    Args:
        user_id: The authenticated user's unique ID (Firebase UID).
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            result = db_conn.execute(
                sqlalchemy.text("SELECT display_name, goal, weight_kg, target_weight_kg, activity_level FROM users WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            if result:
                name, goal, weight, target, activity = result
                return (
                    f"User: {name}\n"
                    f"Goal: {goal}\n"
                    f"Current Weight: {weight}kg\n"
                    f"Target Weight: {target}kg\n"
                    f"Activity Level: {activity}"
                )
            return "User not found in database. This is a new user."
    except Exception as e:
        error_msg = f"Database error fetching user context: {str(e)}"
        logger.error(error_msg)
        return error_msg



def save_daily_workout(user_id: str, day: str, workout_text: str) -> str:
    """Saves a generated workout routine for a specific day of the week to the database.

    Args:
        user_id: The authenticated user's unique ID.
        day: The day of the week (e.g., 'monday', 'tuesday').
        workout_text: The full workout plan text for that day.
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            db_conn.execute(
                sqlalchemy.text("""
                    UPDATE workout_routines SET is_active = FALSE
                    WHERE user_id = :user_id AND day = :day AND is_active = TRUE
                """),
                {"user_id": user_id, "day": day.lower()}
            )
            version_result = db_conn.execute(
                sqlalchemy.text("""
                    SELECT COALESCE(MAX(version), 0) + 1 FROM workout_routines
                    WHERE user_id = :user_id AND day = :day
                """),
                {"user_id": user_id, "day": day.lower()}
            ).fetchone()
            next_version = version_result[0] if version_result else 1

            db_conn.execute(
                sqlalchemy.text("""
                    INSERT INTO workout_routines (user_id, day, workout_text, version, is_active)
                    VALUES (:user_id, :day, :workout_text, :version, TRUE)
                """),
                {"user_id": user_id, "day": day.lower(), "workout_text": workout_text, "version": next_version}
            )
            db_conn.commit()
        return f"Successfully saved workout for {day} (version {next_version})."
    except Exception as e:
        error_msg = f"Database error saving workout: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_daily_workout(user_id: str, day: str) -> str:
    """Fetches the active scheduled workout routine for a specific day from the database.

    Args:
        user_id: The authenticated user's unique ID.
        day: The day of the week (e.g., 'monday', 'tuesday').
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            result = db_conn.execute(
                sqlalchemy.text("""
                    SELECT workout_text, version, created_at FROM workout_routines
                    WHERE user_id = :user_id AND day = :day AND is_active = TRUE
                    ORDER BY version DESC LIMIT 1
                """),
                {"user_id": user_id, "day": day.lower()}
            ).fetchone()
            if result:
                return f"[Routine v{result[1]}, created {result[2]}]\n{result[0]}"
            return f"No workout found for {day}. It might be a rest day, or a routine hasn't been generated yet."
    except Exception as e:
        error_msg = f"Database error fetching workout: {str(e)}"
        logger.error(error_msg)
        return error_msg



def log_completed_workout(user_id: str, exercise: str, sets: int, reps: int, weight_kg: float, rpe: float = None, notes: str = None) -> str:
    """Logs a completed exercise set to the workout history for progress tracking and PR detection.

    Args:
        user_id: The authenticated user's unique ID.
        exercise: The name of the exercise (e.g., 'Bench Press', 'Squat').
        sets: Number of sets completed.
        reps: Number of reps per set.
        weight_kg: Weight used in kilograms.
        rpe: Optional. Rate of Perceived Exertion (1-10 scale).
        notes: Optional. Any additional notes about the exercise.
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            db_conn.execute(
                sqlalchemy.text("""
                    INSERT INTO workout_logs (user_id, exercise, sets, reps, weight_kg, rpe, notes)
                    VALUES (:user_id, :exercise, :sets, :reps, :weight_kg, :rpe, :notes)
                """),
                {
                    "user_id": user_id, "exercise": exercise.lower(),
                    "sets": sets, "reps": reps, "weight_kg": weight_kg,
                    "rpe": rpe, "notes": notes
                }
            )
            db_conn.commit()

        est_1rm = weight_kg * (1 + reps / 30)
        return f"✅ Logged: {exercise} — {sets}x{reps} @ {weight_kg}kg (Est. 1RM: {est_1rm:.1f}kg)"
    except Exception as e:
        error_msg = f"Database error logging workout: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_exercise_history(user_id: str, exercise: str, limit: int = 10) -> str:
    """Retrieves the recent history for a specific exercise to show progress over time.

    Args:
        user_id: The authenticated user's unique ID.
        exercise: The name of the exercise to look up.
        limit: Number of recent entries to retrieve. Defaults to 10.
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            results = db_conn.execute(
                sqlalchemy.text("""
                    SELECT date, sets, reps, weight_kg, rpe FROM workout_logs
                    WHERE user_id = :user_id AND exercise = :exercise
                    ORDER BY date DESC, created_at DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "exercise": exercise.lower(), "limit": limit}
            ).fetchall()

            if not results:
                return f"No history found for '{exercise}'. Start logging to track progress!"

            history = f"📊 Recent History for {exercise}:\n"
            for row in results:
                date, sets, reps, weight, rpe = row
                rpe_str = f" RPE {rpe}" if rpe else ""
                history += f"  {date}: {sets}x{reps} @ {weight}kg{rpe_str}\n"
            return history
    except Exception as e:
        error_msg = f"Database error fetching exercise history: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_personal_records(user_id: str) -> str:
    """Fetches the best estimated 1RM for each exercise the user has ever logged.

    Args:
        user_id: The authenticated user's unique ID.
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            results = db_conn.execute(
                sqlalchemy.text("""
                    SELECT exercise, MAX(weight_kg * (1 + reps::decimal / 30)) as est_1rm,
                           MAX(weight_kg) as max_weight
                    FROM workout_logs
                    WHERE user_id = :user_id
                    GROUP BY exercise
                    ORDER BY est_1rm DESC
                """),
                {"user_id": user_id}
            ).fetchall()

            if not results:
                return "No personal records yet. Start logging your workouts to track PRs!"

            prs = "🏆 Personal Records (Estimated 1RM):\n"
            for row in results:
                exercise, est_1rm, max_weight = row
                prs += f"  {exercise.title()}: {est_1rm:.1f}kg (heaviest: {max_weight}kg)\n"
            return prs
    except Exception as e:
        error_msg = f"Database error fetching PRs: {str(e)}"
        logger.error(error_msg)
        return error_msg



def save_readiness_log(user_id: str, sleep_hours: float, soreness_score: int, readiness_score: int, notes: str = None) -> str:
    """Persists a daily readiness assessment for trend tracking and auto-regulation.

    Args:
        user_id: The authenticated user's unique ID.
        sleep_hours: Hours of sleep the user got.
        soreness_score: Muscle soreness level from 1 (none) to 10 (extreme).
        readiness_score: The calculated readiness score (0-100).
        notes: Optional. Additional notes about recovery state.
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            db_conn.execute(
                sqlalchemy.text("""
                    INSERT INTO readiness_logs (user_id, sleep_hours, soreness_score, readiness_score, notes)
                    VALUES (:user_id, :sleep_hours, :soreness_score, :readiness_score, :notes)
                    ON CONFLICT (user_id, date) DO UPDATE SET
                        sleep_hours = EXCLUDED.sleep_hours,
                        soreness_score = EXCLUDED.soreness_score,
                        readiness_score = EXCLUDED.readiness_score,
                        notes = EXCLUDED.notes
                """),
                {
                    "user_id": user_id, "sleep_hours": sleep_hours,
                    "soreness_score": soreness_score, "readiness_score": readiness_score,
                    "notes": notes
                }
            )
            db_conn.commit()
        return f"Readiness logged: Score {readiness_score}/100 (Sleep: {sleep_hours}h, Soreness: {soreness_score}/10)"
    except Exception as e:
        error_msg = f"Database error saving readiness: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_readiness_trend(user_id: str, days: int = 7) -> str:
    """Shows the readiness scores over the last N days to identify fatigue trends.

    Args:
        user_id: The authenticated user's unique ID.
        days: Number of days to look back. Defaults to 7.
    """
    try:
        db_pool = init_pool_and_db()
        with db_pool.connect() as db_conn:
            results = db_conn.execute(
                sqlalchemy.text("""
                    SELECT date, sleep_hours, soreness_score, readiness_score FROM readiness_logs
                    WHERE user_id = :user_id AND date >= CURRENT_DATE - :days
                    ORDER BY date DESC
                """),
                {"user_id": user_id, "days": days}
            ).fetchall()

            if not results:
                return f"No readiness data in the last {days} days. Start checking in daily to track recovery trends!"

            trend = f"📈 Readiness Trend (Last {days} Days):\n"
            scores = []
            for row in results:
                date, sleep, soreness, score = row
                indicator = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
                trend += f"  {indicator} {date}: Score {score}/100 (Sleep: {sleep}h, Soreness: {soreness}/10)\n"
                scores.append(score)

            avg_score = sum(scores) / len(scores)
            trend += f"\n  Average: {avg_score:.0f}/100"

            if len(scores) >= 3 and all(s < 50 for s in scores[:3]):
                trend += "\n  ⚠️ WARNING: Your readiness has been critically low for 3+ days. Consider a deload week."
            elif avg_score < 60:
                trend += "\n  ⚠️ Your average readiness is below 60. Sleep quality may need attention."

            return trend
    except Exception as e:
        error_msg = f"Database error fetching readiness trend: {str(e)}"
        logger.error(error_msg)
        return error_msg