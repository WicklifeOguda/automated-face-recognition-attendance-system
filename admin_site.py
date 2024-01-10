from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.admin.settings import Settings
from fastapi_amis_admin.admin.site import AdminSite
from fastapi_amis_admin.amis.components import PageSchema

from models import Student

# AdminSite instance
site = AdminSite(
    settings=Settings(
        database_url_async="sqlite+aiosqlite:///attendance.db",
        site_title="WikieAutoAttendance Admin",
    )
)


# Registration management classes
@site.register_admin
class StudentAdmin(admin.ModelAdmin):
    page_schema = "Student"
    model = Student
