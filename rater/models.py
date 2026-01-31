from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Prompt(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class WeaknessCategory(models.Model):
    name = models.CharField(max_length=100) # e.g., Hallucination, Verbosity

class Evaluation(models.Model):
    prompt = models.OneToOneField(Prompt, on_delete=models.CASCADE)
    response_a = models.TextField()
    response_b = models.TextField()
    
    # -5 (Strong A) to 5 (Strong B)
    score = models.IntegerField(default=0, validators=[MinValueValidator(-5), MaxValueValidator(5)])
    
    weaknesses_a = models.ManyToManyField(WeaknessCategory, related_name='a_flaws', blank=True)
    weaknesses_b = models.ManyToManyField(WeaknessCategory, related_name='b_flaws', blank=True)
    
    ai_logic = models.TextField(blank=True) # To store the AI's explanation
