from django.contrib import admin

from .models import (
    ParentChildRelation,
    Person,
    SiblingRelation,
    SpouseRelation,
    WelcomeScreen,
)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'middle_name',
        'birth_date',
        'birth_year_only',
        'death_date',
        'death_year_only',
        'graph_x',
        'graph_y',
    )
    list_display_links = ('last_name',)
    list_editable = (
        'first_name',
        'middle_name',
        'birth_date',
        'birth_year_only',
        'death_date',
        'death_year_only',
        'graph_x',
        'graph_y',
    )
    search_fields = ('first_name', 'last_name', 'middle_name')
    list_filter = ('birth_year_only', 'death_year_only', 'birth_date')
    list_per_page = 50
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'last_name',
                'first_name',
                'middle_name',
                'photo',
            ),
        }),
        ('Даты', {
            'fields': (
                'birth_date',
                'birth_year_only',
                'death_date',
                'death_year_only',
            ),
            'description': (
                'Можно указать только рождение, только смерть или обе даты. '
                'Если известен только год — поставьте 01.01.YYYY и отметьте «только год». '
                'Неизвестную дату просто оставьте пустой.'
            ),
        }),
        ('Биография', {
            'fields': ('short_bio', 'full_bio'),
        }),
        ('Позиция на графе', {
            'fields': ('graph_x', 'graph_y'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ParentChildRelation)
class ParentChildRelationAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child')
    autocomplete_fields = ('parent', 'child')


@admin.register(SiblingRelation)
class SiblingRelationAdmin(admin.ModelAdmin):
    list_display = ('person_a', 'person_b', 'relation_type')
    list_filter = ('relation_type',)
    autocomplete_fields = ('person_a', 'person_b')


@admin.register(SpouseRelation)
class SpouseRelationAdmin(admin.ModelAdmin):
    list_display = ('person_a', 'person_b')
    autocomplete_fields = ('person_a', 'person_b')


@admin.register(WelcomeScreen)
class WelcomeScreenAdmin(admin.ModelAdmin):
    list_display = ('title',)

    def has_add_permission(self, request):
        if WelcomeScreen.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False
