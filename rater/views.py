import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Prompt, Evaluation, WeaknessCategory
from .services import auto_evaluate, evaluate_prompt_quality, scan_response_weaknesses

def index(request):
    categories = WeaknessCategory.objects.all().order_by('name')
    return render(request, 'index.html', {'weakness_categories': categories})

def evaluate(request):
    if request.method == 'POST':
        prompt_text = request.POST.get('prompt')
        response_a = request.POST.get('response_a')
        response_b = request.POST.get('response_b')

        if not all([prompt_text, response_a, response_b]):
            return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

        # 1. Create the objects
        prompt_obj = Prompt.objects.create(text=prompt_text)
        eval_obj = Evaluation.objects.create(
            prompt=prompt_obj,
            response_a=response_a,
            response_b=response_b
        )

        # 2. Trigger the AI audit
        success = auto_evaluate(eval_obj.id)

        if success:
            # Refresh to get updated data
            eval_obj.refresh_from_db()
            
            def format_weaknesses(queryset):
                return [
                    {
                        'name': w.name,
                        'description': w.description,
                        'examples': w.examples
                    } for w in queryset.all()
                ]

            return JsonResponse({
                'status': 'success',
                'score': eval_obj.score,
                'ai_logic': eval_obj.ai_logic,
                'strength_a': eval_obj.strength_a,
                'strength_b': eval_obj.strength_b,
                'comparison': {
                    'accuracy': eval_obj.comparison_accuracy,
                    'instructions': eval_obj.comparison_instructions,
                    'tone': eval_obj.comparison_tone,
                },
                'weaknesses_a': format_weaknesses(eval_obj.weaknesses_a),
                'weaknesses_b': format_weaknesses(eval_obj.weaknesses_b),
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'AI Audit failed'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

def evaluate_prompt(request):
    if request.method == 'POST':
        prompt_text = request.POST.get('prompt')
        if not prompt_text:
            return JsonResponse({'status': 'error', 'message': 'No prompt provided'}, status=400)
            
        result = evaluate_prompt_quality(prompt_text)
        return JsonResponse({
            'status': 'success',
            'score': result.get('score'),
            'feedback': result.get('feedback')
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

def scan_weaknesses(request):
    if request.method == 'POST':
        prompt_text = request.POST.get('prompt')
        response_text = request.POST.get('response_text')
        
        if not prompt_text or not response_text:
            return JsonResponse({'status': 'error', 'message': 'Missing text'}, status=400)
            
        found = scan_response_weaknesses(prompt_text, response_text)
        return JsonResponse({
            'status': 'success',
            'found_weaknesses': found
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
