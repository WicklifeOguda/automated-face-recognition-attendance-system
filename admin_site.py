from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin, ModelView

from admin_auth import AdminAuthProvider
from database import engine
from models import Student, Unit

admin = Admin(
    engine,
    title="WikieAutoAttendance",
    auth_provider=AdminAuthProvider(),
    middlewares=[Middleware(SessionMiddleware, secret_key="SECRET")],
)

admin.add_view(ModelView(Student))
admin.add_view(ModelView(Unit))
