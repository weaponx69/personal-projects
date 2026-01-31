from django.contrib import admin
from .models import Prompt, WeaknessCategory, Evaluation

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'created_at')
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

@admin.register(WeaknessCategory)
class WeaknessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('prompt_preview', 'score')
    filter_horizontal = ('weaknesses_a', 'weaknesses_b')
    
    def prompt_preview(self, obj):
        return obj.prompt.text[:50] + "..." if len(obj.prompt.text) > 50 else obj.prompt.text
