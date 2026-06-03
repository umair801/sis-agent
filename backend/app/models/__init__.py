"""
Model registry — import ALL SQLAlchemy models here so that
Base.metadata knows about every table.

Import order matters: tables with no foreign keys first,
then tables that depend on them.

Every service, route, and test should import models from here,
NOT from app.models.sped, app.models.student, etc. directly.
This prevents circular imports because database.py no longer
imports models, and models only import Base from database.py.
"""

from app.models.tenant import Tenant                        # noqa: F401
from app.models.user import Role, User                      # noqa: F401
from app.models.student import (                            # noqa: F401
    Student, Guardian, School, AcademicYear,
    GradeLevel, Enrollment,
)
from app.models.attendance import (                         # noqa: F401
    Period, AttendanceDaily, AttendancePeriod,
)
from app.models.scheduling import (                         # noqa: F401
    Course, Room, Section, StudentSection,
)
from app.models.gradebook import (                          # noqa: F401
    GradingScale, AssignmentCategory, Assignment,
    Grade, SectionFinalGrade,
)
from app.models.sped import (                               # noqa: F401
    IEP, IEPService, IEPGoal, IEPGoalProgress,
    IEPAccommodation, IEPTeamMember, IEPMeeting,
)
