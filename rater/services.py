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
                "tone": "Compare A and B behavior...",
                "overall": "Which response is better overall, and why?",
                "naming_clarity": "Which code has better naming and clarity?",
                "organization_modularity": "Which code has better organization and modularity?",
                "error_handling": "Which code has better error handling and robustness?",
                "documentation": "Which code has better comments and documentation?",
                "review_readiness": "Which code is more ready for review/merge?",
                "logic_correctness": "Which code has better logic and correctness?",
                "honesty": "Which response is more honest about what it actually did?",
                "instruction_following": "Which response follows the instructions better?"
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
        eval_obj.comparison_overall = comp.get('overall', '')
        eval_obj.comparison_naming_clarity = comp.get('naming_clarity', '')
        eval_obj.comparison_organization_modularity = comp.get('organization_modularity', '')
        eval_obj.comparison_error_handling = comp.get('error_handling', '')
        eval_obj.comparison_documentation = comp.get('documentation', '')
        eval_obj.comparison_review_readiness = comp.get('review_readiness', '')
        eval_obj.comparison_logic_correctness = comp.get('logic_correctness', '')
        eval_obj.comparison_honesty = comp.get('honesty', '')
        eval_obj.comparison_instruction_following = comp.get('instruction_following', '')
        
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
def evaluate_prompt_quality(prompt_text):
    try:
        system_prompt = "You are an expert prompt engineer. Evaluate the user's prompt for clarity, constraints, and effectiveness on a scale of 1-5."
        user_prompt = f"""
        Evaluate this prompt: "{prompt_text}"
        
        Provide a score (1-5) and a concise paragraph of feedback.
        1: Very poor, ambiguous, no constraints.
        5: Excellent, clear, specific constraints, well-structured.
        
        Return ONLY JSON:
        {{
            "score": 4,
            "feedback": "Your feedback here..."
        }}
        """
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(content)
            
        return data  # {'score': x, 'feedback': '...'}
    except Exception as e:
        print(f"Error evaluating prompt: {e}")
        return {'score': 0, 'feedback': f"Error: {str(e)}"}

def scan_response_weaknesses(prompt_text, response_text):
    try:
        categories = list(WeaknessCategory.objects.values_list('name', flat=True))
        system_prompt = "You are an AI quality auditor. Scan a single AI response against specific weakness criteria."
        user_prompt = f"""
        Original Prompt: "{prompt_text}"
        AI Response: "{response_text}"
        
        Criteria to check: {categories}
        
        INSTRUCTIONS:
        1. Identify which weaknesses from the list above are present in this specific response.
        2. For each identified weakness, provide a 1-sentence explanation of where it occurred.
        
        Return ONLY JSON:
        {{
            "found_weaknesses": [
                {{"name": "[TAG]", "reason": "Specific reason..."}}
            ]
        }}
        """
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(content)
            
        return data.get('found_weaknesses', [])
    except Exception as e:
        print(f"Error scanning response: {e}")
        return []
