import os, json
from openai import OpenAI  # We still use the OpenAI library because it's compatible!

# Point it to Perplexity's URL
client = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"), 
    base_url="https://api.perplexity.ai"
)

def auto_evaluate(evaluation_id):
    # ... (rest of your logic remains the same)
    
    response = client.chat.completions.create(
        model="sonar-pro", # Use Perplexity's powerful search/reasoning model
        messages=[{"role": "user", "content": prompt_text}],
        # Note: Perplexity might not support 'json_object' format on all models, 
        # so we'll just ask for a clean string if it fails.
    )
    # ...