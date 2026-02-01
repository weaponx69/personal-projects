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

        # 2. Capture pre-scanned data from frontend
        scan_a_raw = request.POST.get('scan_data_a')
        scan_b_raw = request.POST.get('scan_data_b')
        
        # Pre-populate Evaluation object if pre-scanned data exists
        def populate_from_scan(eval_obj, raw_data, suffix):
            if not raw_data: return
            try:
                data = json.loads(raw_data)
                setattr(eval_obj, f'strength_{suffix}', data.get('strength', ''))
                m2m = getattr(eval_obj, f'weaknesses_{suffix}')
                for w in data.get('found_weaknesses', []):
                    cat = WeaknessCategory.objects.filter(name=w['name']).first()
                    if cat: m2m.add(cat)
            except: pass

        populate_from_scan(eval_obj, scan_a_raw, 'a')
        populate_from_scan(eval_obj, scan_b_raw, 'b')
        eval_obj.save()

        from .services import auto_evaluate_stream
        return StreamingHttpResponse(
            auto_evaluate_stream(eval_obj.id, pre_scan_a=scan_a_raw, pre_scan_b=scan_b_raw),
            content_type='text/event-stream'
        )

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

from django.http import StreamingHttpResponse
from .services import scan_response_weaknesses_stream

def scan_weaknesses(request):
    if request.method == 'POST':
        prompt_text = request.POST.get('prompt')
        response_text = request.POST.get('response_text')
        
        if not prompt_text or not response_text:
            return JsonResponse({'status': 'error', 'message': 'Missing text'}, status=400)
            
        return StreamingHttpResponse(
            scan_response_weaknesses_stream(prompt_text, response_text),
            content_type='text/event-stream'
        )
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
