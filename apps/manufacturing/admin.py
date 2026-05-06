from django.contrib import admin
from apps.manufacturing.models import Job, CutRequirement, CutPlan, CutBar, BOM, BOMLine

admin.site.register(Job)
admin.site.register(CutRequirement)
admin.site.register(CutPlan)
admin.site.register(CutBar)
admin.site.register(BOM)
admin.site.register(BOMLine)
