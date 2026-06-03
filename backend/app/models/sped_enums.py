"""
SpEd/IEP enumerations — kept in a separate file to avoid circular imports.
Both models/sped.py and schemas/sped.py import from here.
"""

from enum import Enum as PyEnum


class IEPStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DisabilityCategory(str, PyEnum):
    AUTISM = "autism"
    DEAF_BLINDNESS = "deaf_blindness"
    DEAFNESS = "deafness"
    DEVELOPMENTAL_DELAY = "developmental_delay"
    EMOTIONAL_DISTURBANCE = "emotional_disturbance"
    HEARING_IMPAIRMENT = "hearing_impairment"
    INTELLECTUAL_DISABILITY = "intellectual_disability"
    MULTIPLE_DISABILITIES = "multiple_disabilities"
    ORTHOPEDIC_IMPAIRMENT = "orthopedic_impairment"
    OTHER_HEALTH_IMPAIRMENT = "other_health_impairment"
    SPECIFIC_LEARNING_DISABILITY = "specific_learning_disability"
    SPEECH_LANGUAGE_IMPAIRMENT = "speech_language_impairment"
    TRAUMATIC_BRAIN_INJURY = "traumatic_brain_injury"
    VISUAL_IMPAIRMENT = "visual_impairment"


class ServiceType(str, PyEnum):
    SPECIAL_EDUCATION = "special_education"
    SPEECH_LANGUAGE = "speech_language"
    OCCUPATIONAL_THERAPY = "occupational_therapy"
    PHYSICAL_THERAPY = "physical_therapy"
    COUNSELING = "counseling"
    TRANSPORTATION = "transportation"
    ASSISTIVE_TECHNOLOGY = "assistive_technology"
    OTHER = "other"


class ServiceFrequency(str, PyEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    AS_NEEDED = "as_needed"


class GoalStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    NOT_ACHIEVED = "not_achieved"
    DISCONTINUED = "discontinued"


class GoalDomain(str, PyEnum):
    ACADEMIC = "academic"
    COMMUNICATION = "communication"
    SOCIAL_EMOTIONAL = "social_emotional"
    BEHAVIORAL = "behavioral"
    ADAPTIVE = "adaptive"
    MOTOR = "motor"
    TRANSITION = "transition"
    OTHER = "other"


class AccommodationType(str, PyEnum):
    PRESENTATION = "presentation"
    RESPONSE = "response"
    SETTING = "setting"
    TIMING_SCHEDULING = "timing_scheduling"
    OTHER = "other"


class TeamMemberRole(str, PyEnum):
    SPED_COORDINATOR = "sped_coordinator"
    GENERAL_ED_TEACHER = "general_ed_teacher"
    SPECIAL_ED_TEACHER = "special_ed_teacher"
    PARENT_GUARDIAN = "parent_guardian"
    STUDENT = "student"
    ADMINISTRATOR = "administrator"
    PSYCHOLOGIST = "psychologist"
    SPEECH_THERAPIST = "speech_therapist"
    OT = "ot"
    PT = "pt"
    COUNSELOR = "counselor"
    OTHER = "other"


class MeetingType(str, PyEnum):
    INITIAL = "initial"
    ANNUAL = "annual"
    TRIENNIAL = "triennial"
    AMENDMENT = "amendment"
    TRANSITION = "transition"
    OTHER = "other"
