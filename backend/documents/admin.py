from django.contrib import admin

from .models import Document, LineItem


class LineItemInline(admin.TabularInline):
    model = LineItem
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "customer", "owner", "status", "issue_date"]
    list_filter = ["status"]
    inlines = [LineItemInline]
