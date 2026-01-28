import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, text
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.types import JSON
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
PROJECT_ROOT = Path(__file__).parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_FILE = DATA_DIR / "diabetesai.db"

# Support both SQLite (default) and PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATABASE_FILE}",
)

# Detect database type
IS_POSTGRESQL = DATABASE_URL.startswith("postgresql")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

Base = declarative_base()


class PlanRecord(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False)
    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=False)


class AuthUserRecord(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False)
    auth_user_id = Column(Integer, nullable=False, unique=True)
    profile_payload = Column(JSON, nullable=False)


class ConsumedMealRecord(Base):
    __tablename__ = "consumed_meals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    plan_id = Column(Integer, nullable=True)  # ID do plano relacionado
    meal_type = Column(Text, nullable=False)  # "Café da manhã", "Almoço", etc.
    meal_name = Column(Text, nullable=False)  # Nome da refeição
    consumed_at = Column(DateTime, nullable=False, index=True)
    notes = Column(Text, nullable=True)  # Notas opcionais do usuário

class GlucoseSessionRecord(Base):
    __tablename__ = "glucose_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    patient_id = Column(Text, nullable=False, index=True)
    source_session_id = Column(Text, nullable=False, index=True)
    anchor_time_iso = Column(Text, nullable=False)
    dashboard_payload = Column(JSON, nullable=False)

def _engine():
    """Create and return a SQLAlchemy engine with proper configuration."""
    try:
        connect_args = {}
        engine_kwargs = {
            "future": True,
            "pool_pre_ping": True,  # Test connections before using them
            "echo": False,  # Set to True for SQL logging during development
        }

        if IS_SQLITE:
            # SQLite specific configurations
            connect_args = {
                "check_same_thread": False,  # Allow multi-threading for SQLite
                "timeout": 30.0,  # Connection timeout
            }
            logger.info("🔧 Using SQLite database configuration")
        elif IS_POSTGRESQL:
            # PostgreSQL specific configurations
            engine_kwargs.update({
                "pool_size": 10,  # Connection pool size
                "max_overflow": 20,  # Max overflow connections
                "pool_timeout": 30,  # Connection timeout
                "pool_recycle": 3600,  # Recycle connections after 1 hour
            })
            logger.info("🔧 Using PostgreSQL database configuration")
        else:
            logger.warning(f"⚠️ Unknown database type in URL: {DATABASE_URL}")

        engine_kwargs["connect_args"] = connect_args

        engine = create_engine(DATABASE_URL, **engine_kwargs)
        logger.info(f"✅ Database engine created successfully: {'PostgreSQL' if IS_POSTGRESQL else 'SQLite'}")
        return engine
    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}")
        raise


def init_db() -> None:
    """Initialize database tables."""
    try:
        logger.info("Initializing database...")
        engine = _engine()

        # Create all tables (works for both SQLite and PostgreSQL)
        Base.metadata.create_all(engine)

        # ✅ Only verify file existence for SQLite
        if IS_SQLITE:
            if DATABASE_FILE.exists():
                logger.info(f"✅ SQLite database initialized successfully at: {DATABASE_FILE}")
                logger.info(f"Database file size: {DATABASE_FILE.stat().st_size} bytes")
            else:
                logger.error(f"❌ SQLite database file was not created at: {DATABASE_FILE}")
                raise FileNotFoundError(f"SQLite database file not found: {DATABASE_FILE}")
        elif IS_POSTGRESQL:
            # ✅ For PostgreSQL, validate connectivity instead of checking a file
            with Session(engine) as session:
                session.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL database initialized successfully (connectivity OK).")
        else:
            logger.warning(f"⚠️ Database initialized, but type is unknown for URL: {DATABASE_URL}")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise



def save_plan(request_payload: Dict[str, Any], response_payload: Dict[str, Any]) -> int:
    """Save a meal plan to the database."""
    try:
        logger.debug("Saving plan to database...")
        engine = _engine()

        with Session(engine) as session:
            record = PlanRecord(
                created_at=datetime.utcnow(),
                request_payload=request_payload,
                response_payload=response_payload,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            plan_id = int(record.id)
            logger.info(f"Plan saved successfully with ID: {plan_id}")
            return plan_id

    except SQLAlchemyError as e:
        logger.error(f"Database error while saving plan: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while saving plan: {e}")
        raise


def check_database_health() -> Dict[str, Any]:
    """Check database health and connectivity."""
    try:
        logger.debug("Checking database health...")
        engine = _engine()

        with Session(engine) as session:
            # Test basic connectivity
            if IS_POSTGRESQL:
                session.execute(text("SELECT 1"))
            else:
                session.execute(text("SELECT 1"))

            # Get table counts
            plans_count = session.query(PlanRecord).count()
            users_count = session.query(UserRecord).count()
            auth_users_count = session.query(AuthUserRecord).count()
            consumed_meals_count = session.query(ConsumedMealRecord).count()

            # Check database file info
            db_size = DATABASE_FILE.stat().st_size if DATABASE_FILE.exists() else 0

            health_info = {
                "status": "healthy",
                "database_path": str(DATABASE_FILE),
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "tables": {
                    "plans": plans_count,
                    "users": users_count,
                    "auth_users": auth_users_count,
                    "consumed_meals": consumed_meals_count,
                },
                "last_check": datetime.utcnow().isoformat(),
            }

            logger.info(f"Database health check passed. Tables: plans={plans_count}, users={users_count}")
            return health_info

    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database_path": str(DATABASE_FILE),
            "database_size_bytes": DATABASE_FILE.stat().st_size if DATABASE_FILE.exists() else 0,
            "database_size_mb": 0,
            "error": str(e),
            "error_type": "database_error",
            "tables": {},
            "last_check": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}")
        return {
            "status": "unhealthy",
            "database_path": str(DATABASE_FILE),
            "database_size_bytes": DATABASE_FILE.stat().st_size if DATABASE_FILE.exists() else 0,
            "database_size_mb": 0,
            "error": str(e),
            "error_type": "unexpected_error",
            "tables": {},
            "last_check": datetime.utcnow().isoformat(),
        }


def list_plans(limit: int = 20) -> List[Dict[str, Any]]:
    """List meal plans from the database."""
    try:
        logger.debug(f"Listing plans (limit: {limit})...")
        engine = _engine()

        with Session(engine) as session:
            rows = session.query(PlanRecord).order_by(PlanRecord.id.desc()).limit(limit).all()

            result = []
            for row in rows:
                # Manually deserialize JSON fields if they are strings
                request_payload = row.request_payload
                response_payload = row.response_payload

                if isinstance(request_payload, str):
                    try:
                        request_payload = json.loads(request_payload)
                    except Exception as e:
                        logger.warning(f"Failed to parse request_payload for plan {row.id}: {e}")
                        request_payload = {}

                if isinstance(response_payload, str):
                    try:
                        response_payload = json.loads(response_payload)
                    except Exception as e:
                        logger.warning(f"Failed to parse response_payload for plan {row.id}: {e}")
                        response_payload = {}

                plan_data = {
                    "id": row.id,
                    "created_at": row.created_at.isoformat(),
                    "request_payload": request_payload,
                    "response_payload": response_payload,
                    "plan_json": (response_payload or {}).get("plan_json"),
                }
                result.append(plan_data)

            logger.debug(f"Retrieved {len(result)} plans")
            return result

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing plans: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while listing plans: {e}")
        raise


def get_plan(plan_id: int) -> Optional[Dict[str, Any]]:
    engine = _engine()
    with Session(engine) as session:
        row = session.get(PlanRecord, plan_id)
        if not row:
            return None
        return {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "request_payload": row.request_payload,
            "response_payload": row.response_payload,
        }


def create_auth_user(email: str, password_hash: str) -> int:
    engine = _engine()
    with Session(engine) as session:
        record = AuthUserRecord(
            created_at=datetime.utcnow(),
            email=email,
            password_hash=password_hash,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return int(record.id)


def get_auth_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    engine = _engine()
    with Session(engine) as session:
        row = session.query(AuthUserRecord).filter(AuthUserRecord.email == email).first()
        if not row:
            return None
        return {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "email": row.email,
            "password_hash": row.password_hash,
        }


def create_empty_profile() -> Dict[str, Any]:
    """Create an empty profile structure with all fields as None or empty"""
    return {
        "full_name": None,
        "age": None,
        "health_metrics": {
            "diabetes_type": None,
            "glucose_levels": None,
            "weight": None,
            "height": None,
            "bmi": None,
            "blood_pressure": None,
            "other_conditions": []
        },
        "preferences": {
            "cuisine": None,
            "region": None,
            "likes": [],
            "dislikes": [],
            "dietary_style": None
        },
        "goals": [],
        "restrictions": [],
        "region": None,
        "inventory": [],
        "glucose_readings": [],
        "meal_history": []
    }


def create_user(profile_payload: Dict[str, Any], auth_user_id: int) -> int:
    engine = _engine()
    with Session(engine) as session:
        record = UserRecord(
            created_at=datetime.utcnow(),
            auth_user_id=auth_user_id,
            profile_payload=profile_payload,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return int(record.id)


def create_user_with_empty_profile(auth_user_id: int) -> int:
    """Create a user with an empty profile after registration"""
    empty_profile = create_empty_profile()
    return create_user(empty_profile, auth_user_id)


def list_users(limit: int = 50) -> List[Dict[str, Any]]:
    engine = _engine()
    with Session(engine) as session:
        rows = session.query(UserRecord).order_by(UserRecord.id.desc()).limit(limit).all()
        return [
            {
                "id": row.id,
                "created_at": row.created_at.isoformat(),
                "auth_user_id": row.auth_user_id,
                "profile": row.profile_payload,
            }
            for row in rows
        ]


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get a user by ID."""
    try:
        logger.debug(f"Getting user with ID: {user_id}")
        engine = _engine()

        with Session(engine) as session:
            row = session.get(UserRecord, user_id)
            if not row:
                logger.debug(f"User not found: {user_id}")
                return None

            result = {
                "id": row.id,
                "created_at": row.created_at.isoformat(),
                "auth_user_id": row.auth_user_id,
                "profile": row.profile_payload,
            }
            logger.debug(f"User retrieved successfully: {user_id}")
            return result

    except SQLAlchemyError as e:
        logger.error(f"Database error while getting user {user_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while getting user {user_id}: {e}")
        raise


def get_user_by_auth_id(auth_user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile by auth_user_id"""
    engine = _engine()
    with Session(engine) as session:
        row = session.query(UserRecord).filter(UserRecord.auth_user_id == auth_user_id).first()
        if not row:
            return None
        return {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "auth_user_id": row.auth_user_id,
            "profile": row.profile_payload,
        }


def update_user(user_id: int, profile_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    engine = _engine()
    with Session(engine) as session:
        row = session.get(UserRecord, user_id)
        if not row:
            return None
        row.profile_payload = profile_payload
        session.commit()
        session.refresh(row)
        return {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "auth_user_id": row.auth_user_id,
            "profile": row.profile_payload,
        }


def save_consumed_meal(
    user_id: int,
    meal_type: str,
    meal_name: str,
    plan_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> int:
    """Save a consumed meal record"""
    engine = _engine()
    with Session(engine) as session:
        record = ConsumedMealRecord(
            user_id=user_id,
            plan_id=plan_id,
            meal_type=meal_type,
            meal_name=meal_name,
            consumed_at=datetime.utcnow(),
            notes=notes,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return int(record.id)


def get_consumed_meals(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get consumed meals for a user"""
    engine = _engine()
    with Session(engine) as session:
        query = session.query(ConsumedMealRecord).filter(
            ConsumedMealRecord.user_id == user_id
        )
        
        if start_date:
            query = query.filter(ConsumedMealRecord.consumed_at >= start_date)
        if end_date:
            query = query.filter(ConsumedMealRecord.consumed_at <= end_date)
        
        rows = query.order_by(ConsumedMealRecord.consumed_at.desc()).limit(limit).all()
        
        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "plan_id": row.plan_id,
                "meal_type": row.meal_type,
                "meal_name": row.meal_name,
                "consumed_at": row.consumed_at.isoformat(),
                "notes": row.notes,
            }
            for row in rows
        ]


def calculate_adherence(
    user_id: int,
    plan_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calculate adherence metrics for a user's meal plan"""
    # Get the plan
    if plan_id:
        plan_data = get_plan(plan_id)
        if not plan_data:
            return {"error": "Plan not found"}
        
        plan_json = plan_data.get("response_payload", {}).get("plan_json", {})
        planned_meals = plan_json.get("meals", [])
    else:
        # Get most recent plan for user
        all_plans = list_plans(limit=50)
        user_plans = [
            p for p in all_plans
            if p.get("request_payload", {}).get("user_id") == user_id
        ]
        if not user_plans:
            return {"error": "No plans found for user"}
        
        plan_data = get_plan(user_plans[0]["id"])
        plan_json = plan_data.get("response_payload", {}).get("plan_json", {})
        planned_meals = plan_json.get("meals", [])
    
    if not planned_meals:
        return {"error": "No meals in plan"}
    
    # Get consumed meals
    consumed_meals = get_consumed_meals(user_id, start_date, end_date)
    
    # Calculate metrics
    total_planned = len(planned_meals)

    # Match consumed meals to planned meals (by meal_type and name similarity)
    matched_meals = []
    for consumed in consumed_meals:
        for planned in planned_meals:
            planned_type = planned.get("meal_type") or planned.get("type", "")
            planned_name = planned.get("name") or planned.get("title", "")

            # More precise matching
            if (consumed["meal_type"].lower() == planned_type.lower() and
                (consumed["meal_name"].lower() in planned_name.lower() or
                 planned_name.lower() in consumed["meal_name"].lower() or
                 planned_name.lower() == consumed["meal_name"].lower())):
                matched_meals.append(consumed)
                break

    # Calculate adherence based only on matched meals vs planned meals
    adherence_percentage = (len(matched_meals) / total_planned * 100) if total_planned > 0 else 0

    # Count only consumed meals that match the current plan
    total_consumed_in_plan = len(matched_meals)
    
    # Group by meal type
    by_type = {}
    for meal in planned_meals:
        meal_type = meal.get("meal_type") or meal.get("type", "Outro")
        if meal_type not in by_type:
            by_type[meal_type] = {"planned": 0, "consumed": 0}
        by_type[meal_type]["planned"] += 1
    
    for consumed in consumed_meals:
        meal_type = consumed["meal_type"]
        if meal_type not in by_type:
            by_type[meal_type] = {"planned": 0, "consumed": 0}
        by_type[meal_type]["consumed"] += 1
    
    return {
        "total_planned": total_planned,
        "total_consumed": total_consumed_in_plan,  # Only meals consumed from current plan
        "matched_meals": len(matched_meals),
        "adherence_percentage": round(min(adherence_percentage, 100.0), 2),  # Cap at 100%
        "by_meal_type": by_type,
        "consumed_meals": consumed_meals[:20],  # Last 20 consumed meals
        "all_consumed_count": len(consumed_meals),  # Total consumed meals across all plans
    }


def delete_consumed_meal(consumed_meal_id: int, user_id: int) -> bool:
    """Delete a consumed meal record (unmark as consumed)."""
    try:
        engine = _engine()

        with Session(engine) as session:
            # Find the consumed meal
            from sqlalchemy import select
            stmt = select(ConsumedMealRecord).where(
                ConsumedMealRecord.id == consumed_meal_id,
                ConsumedMealRecord.user_id == user_id
            )
            result = session.execute(stmt)
            consumed_meal = result.scalar_one_or_none()

            if not consumed_meal:
                return False

            # Delete the record
            session.delete(consumed_meal)
            session.commit()

            logger.info(f"Consumed meal {consumed_meal_id} deleted for user {user_id}")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting consumed meal: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while deleting consumed meal: {e}")
        raise

def delete_user(user_id: int) -> bool:
    engine = _engine()
    with Session(engine) as session:
        row = session.get(UserRecord, user_id)
        if not row:
            return False
        session.delete(row)
        session.commit()
        return True
        
def create_glucose_session(
    user_id: int,
    patient_id: str,
    source_session_id: str,
    anchor_time_iso: str,
    dashboard_payload: Dict[str, Any],
) -> int:
    engine = _engine()
    with Session(engine) as session:
        record = GlucoseSessionRecord(
            created_at=datetime.utcnow(),
            user_id=user_id,
            patient_id=patient_id,
            source_session_id=source_session_id,
            anchor_time_iso=anchor_time_iso,
            dashboard_payload=dashboard_payload,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return int(record.id)


def list_glucose_sessions(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    engine = _engine()
    with Session(engine) as session:
        rows = (
            session.query(GlucoseSessionRecord)
            .filter(GlucoseSessionRecord.user_id == user_id)
            .order_by(GlucoseSessionRecord.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "created_at": row.created_at.isoformat(),
                "patient_id": row.patient_id,
                "source_session_id": row.source_session_id,
                "anchor_time_iso": row.anchor_time_iso,
            }
            for row in rows
        ]


def get_glucose_session(db_session_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    engine = _engine()
    with Session(engine) as session:
        row = (
            session.query(GlucoseSessionRecord)
            .filter(
                GlucoseSessionRecord.id == db_session_id,
                GlucoseSessionRecord.user_id == user_id,
            )
            .first()
        )
        if not row:
            return None
        return {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "user_id": row.user_id,
            "patient_id": row.patient_id,
            "source_session_id": row.source_session_id,
            "anchor_time_iso": row.anchor_time_iso,
            "dashboard_payload": row.dashboard_payload,
        }