import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_rater_project.settings')
django.setup()

from rater.services import scan_response_weaknesses

prompt = "Write a python script to sort a list."
response = "Here is the script: \n```python\ndef sort_list(l):\n    return sorted(l)\n```"

try:
    result = scan_response_weaknesses(prompt, response)
    print("RESULT:", result)
except Exception as e:
    print("EXCEPTION:", type(e).__name__, "-", e)
