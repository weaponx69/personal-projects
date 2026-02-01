from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Prompt(models.Model):
    text = models.TextField()
    quality_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    quality_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class WeaknessCategory(models.Model):
    name = models.CharField(max_length=100) # e.g., Hallucination, Verbosity
    description = models.TextField(blank=True, help_text="Why is this a weakness?")
    examples = models.TextField(blank=True, help_text="Plain text examples for copy-pasting.")
    
    def __str__(self):
        return self.name

class Evaluation(models.Model):
    prompt = models.OneToOneField(Prompt, on_delete=models.CASCADE)
    response_a = models.TextField()
    response_b = models.TextField()
    
    # -5 (Strong A) to 5 (Strong B)
    score = models.IntegerField(default=0, validators=[MinValueValidator(-5), MaxValueValidator(5)])
    
    weaknesses_a = models.ManyToManyField(WeaknessCategory, related_name='a_flaws', blank=True)
    weaknesses_b = models.ManyToManyField(WeaknessCategory, related_name='b_flaws', blank=True)
    
    ai_logic = models.TextField(blank=True) # To store the AI's explanation
    ai_thought = models.TextField(blank=True) # To store the AI's internal reasoning/thinking
    overall_rationale = models.TextField(blank=True) # AI's final rationale breakdown
    
    # Strengths
    strength_a = models.TextField(blank=True)
    strength_b = models.TextField(blank=True)
    
    # Comparison Summaries (Text)
    comparison_accuracy = models.TextField(blank=True)
    comparison_instructions = models.TextField(blank=True)
    comparison_tone = models.TextField(blank=True)
    comparison_overall = models.TextField(blank=True)
    comparison_naming_clarity = models.TextField(blank=True)
    comparison_organization_modularity = models.TextField(blank=True)
    comparison_error_handling = models.TextField(blank=True)
    comparison_documentation = models.TextField(blank=True)
    comparison_review_readiness = models.TextField(blank=True)
    comparison_logic_correctness = models.TextField(blank=True)
    comparison_honesty = models.TextField(blank=True)
    comparison_instruction_following = models.TextField(blank=True)

    # Comparison Scores (-4 to 4)
    score_accuracy = models.IntegerField(default=0)
    score_instructions = models.IntegerField(default=0)
    score_tone = models.IntegerField(default=0)
    score_overall = models.IntegerField(default=0)
    score_naming_clarity = models.IntegerField(default=0)
    score_organization_modularity = models.IntegerField(default=0)
    score_error_handling = models.IntegerField(default=0)
    score_documentation = models.IntegerField(default=0)
    score_review_readiness = models.IntegerField(default=0)
    score_logic_correctness = models.IntegerField(default=0)
    score_honesty = models.IntegerField(default=0)
    score_instruction_following = models.IntegerField(default=0)
