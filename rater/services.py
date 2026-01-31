import json
import re
from openai import OpenAI
from django.conf import settings
from .models import Evaluation, WeaknessCategory

# Initialize the Perplexity client using your settings
client = OpenAI(
    api_key=settings.PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

def auto_evaluate(evaluation_id):
    try:
        # 1. Fetch the evaluation record from your database
        eval_obj = Evaluation.objects.get(id=evaluation_id)
        
        # 2. Get the list of possible weaknesses from your DB to guide the AI
        categories = list(WeaknessCategory.objects.values_list('name', flat=True))
        
        system_prompt = (
            "You are an expert AI quality auditor. You must compare two AI responses (A and B) "
            "based on the provided prompt. Analyze them for weaknesses and provide a score."
        )
        
        user_prompt = f"""
        Prompt: "{eval_obj.prompt.text}"
        
        Response A: {eval_obj.response_a}
        Response B: {eval_obj.response_b}
        
        CRITICAL: Use ONLY these Category Names for identification: {categories}
        
        INSTRUCTIONS:
        1. Compare Response A and Response B.
        2. Identify strengths for each response in one concise paragraph.
        3. Identify weaknesses for A and B using the exact bracketed tags like [LAZY] or [HALLUC].
        4. Provide a direct comparison for Accuracy, Instruction Following, and Tone/Format, explaining which model performed better in each.
        5. Rate the comparison on a scale of -5 to 5.
           -5: Response A is perfect, B is terrible.
            0: They are exactly equal.
            5: Response B is perfect, A is terrible.
        
        OUTPUT FORMAT:
        You must return ONLY a JSON object. No other text.
        Format:
        {{
            "score": 0,
            "strength_a": "Concise paragraph...",
            "strength_b": "Concise paragraph...",
            "weaknesses_a": ["[TAG1]", "[TAG2]"],
            "weaknesses_b": ["[TAG3]"],
            "comparison": {{
                "accuracy": "Compare A and B behavior...",
                "instructions": "Compare A and B behavior...",
                "tone": "Compare A and B behavior..."
            }},
            "reasoning": "Overall final logic here..."
        }}
        """

        # 3. Call Perplexity
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        content = response.choices[0].message.content

        # 4. Extract and Clean JSON (in case Perplexity adds markdown or text)
        # This regex finds the first '{' and last '}' to extract the JSON block
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(content)
        
        # 5. Save the data to your Django Model
        eval_obj.score = data.get('score', 0)
        eval_obj.ai_logic = data.get('reasoning', '')
        
        # New sections
        eval_obj.strength_a = data.get('strength_a', '')
        eval_obj.strength_b = data.get('strength_b', '')
        
        comp = data.get('comparison', {})
        eval_obj.comparison_accuracy = comp.get('accuracy', '')
        eval_obj.comparison_instructions = comp.get('instructions', '')
        eval_obj.comparison_tone = comp.get('tone', '')
        
        # Save before adding many-to-many relationships
        eval_obj.save()

        # Clear old weaknesses before adding new ones
        eval_obj.weaknesses_a.clear()
        eval_obj.weaknesses_b.clear()

        # Map strings back to database objects
        for w_name in data.get('weaknesses_a', []):
            # Try exact match first
            cat = WeaknessCategory.objects.filter(name=w_name).first()
            if not cat:
                # Try matching just the bracketed part, e.g., "[LAZY]"
                tag_match = re.search(r'\[[A-Z]+\]', w_name)
                if tag_match:
                    cat = WeaknessCategory.objects.filter(name__startswith=tag_match.group()).first()
            
            if cat:
                eval_obj.weaknesses_a.add(cat)
            
        for w_name in data.get('weaknesses_b', []):
            # Try exact match first
            cat = WeaknessCategory.objects.filter(name=w_name).first()
            if not cat:
                # Try matching just the bracketed part, e.g., "[LAZY]"
                tag_match = re.search(r'\[[A-Z]+\]', w_name)
                if tag_match:
                    cat = WeaknessCategory.objects.filter(name__startswith=tag_match.group()).first()
            
            if cat:
                eval_obj.weaknesses_b.add(cat)

        return True

    except Evaluation.DoesNotExist:
        print(f"Evaluation with ID {evaluation_id} not found.")
        return False
    except Exception as e:
        print(f"Error in auto_evaluate: {e}")
        # If we have the eval_obj, we can save the error message
        try:
            eval_obj = Evaluation.objects.get(id=evaluation_id)
            eval_obj.ai_logic = f"Error: {str(e)}"
            if 'content' in locals():
                eval_obj.ai_logic += f" | Raw Content: {content}"
            eval_obj.save()
        except:
            pass
        return False