import json
import re
import openai  # Added this import to fix exception handling
from openai import OpenAI, APIConnectionError, APIStatusError, APITimeoutError
from django.conf import settings
from .models import Evaluation, WeaknessCategory

# Initialize the Ollama client
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama", 
    timeout=600.0  # Increased to 10 minutes for very large local contexts
)

# Ensure Ollama model is available and Ollama is running (this check is not performed here,
# assuming Ollama setup is managed externally, or handled by the frontend checks if any)

def try_parse_json(text):
    """
    Attempts to parse JSON with aggressive LLM failure fixes.
    """
    # 1. Strip whitespace and non-JSON preamble
    text = text.strip()
    
    # 2. Fix trailing commas in objects and arrays
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    # 3. Handle single quote keys/values (common in small models)
    # This is conservative: only replace single quotes if they are likely intended as JSON delimiters
    # Replace {'key': 'value'} style
    # Match ' at start or after { , : and before } , : or end
    # We use a pattern to find single-quoted strings and replace them with double quotes
    # But only if they don't contain escaped double quotes which would break things
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If standard parsing fails, try aggressive fixes
        
        # A) Replace single quotes with double quotes
        # Pattern for keys: 'key': -> "key":
        repaired = re.sub(r"'(\w+)'\s*:", r'"\1":', text)
        # Pattern for string values: : 'value' -> : "value"
        repaired = re.sub(r":\s*'([^']*)'", r': "\1"', repaired)
        # Pattern for array values: ['val1', 'val2'] -> ["val1", "val2"]
        repaired = re.sub(r"\[\s*'([^']*)'", r'["\1"', repaired) # start
        repaired = re.sub(r"'\s*,\s*'([^']*)'", r'", "\1"', repaired) # middle
        repaired = re.sub(r"'([^']*)\s*\]", r'"\1"]', repaired) # end
        
        # B) Fix unescaped newlines inside strings
        # This looks for content between quotes and escapes actual newlines
        def fix_newlines(match):
            return match.group(0).replace('\n', '\\n')
        repaired = re.sub(r'"[^"]*"', fix_newlines, repaired)

        try:
            return json.loads(repaired)
        except:
            # Last ditch effort: try ast.literal_eval if it looks like a python dict
            import ast
            try:
                data = ast.literal_eval(text)
                if isinstance(data, dict):
                    return data
            except:
                pass
            raise # Re-raise original error if fixes failed

def auto_evaluate_stream(evaluation_id, pre_scan_a=None, pre_scan_b=None):
    try:
        eval_obj = Evaluation.objects.get(id=evaluation_id)
        categories = list(WeaknessCategory.objects.values_list('name', flat=True))
        
        system_prompt = (
            "You are an expert AI quality auditor. You must compare two AI responses (A and B). "
            "A preliminary scan has already been performed. Your goal is to provide a final score and comparison."
            " Respond and reason exclusively in English."
        )

        user_prompt = f"""
        Prompt: "{eval_obj.prompt.text}"
        
        Response A: {eval_obj.response_a}
        
        Response B: {eval_obj.response_b}

        --- PRE-IDENTIFIED FINDINGS FOR REFERENCE ---
        These weaknesses and strengths were found in preliminary individual scans. 
        You MUST synthesize these findings into your detailed comparison below:
        Findings A: {pre_scan_a if pre_scan_a else "None provided"}
        Findings B: {pre_scan_b if pre_scan_b else "None provided"}
        
        CRITICAL: Use ONLY these Category Names for identification: {categories}
        
        INSTRUCTIONS:
        1. Compare Response A and Response B.
        2. Integrate the pre-identified findings into your analysis.
        3. Identify strengths and ALL relevant weaknesses using exact tags {categories}.
        4. TIE-BREAKER RULE: A score of 0 is FORBIDDEN. If they seem equal, you MUST pick a winner based on subtle factors like readability, formatting, or tone.
        5. For each category, provide a justification (text) and a score.
           -4 to -1: A wins (4=max, 1=marginal)
            1 to 4: B wins (1=marginal, 4=max)
        
        OUTPUT FORMAT:
        YOU MUST RETURN ONLY THE JSON OBJECT.
        Structure:
        {{
            "overall_final_score": -2,
            "overall_final_reasoning": "...",
            "overall_rationale": "Detailed explanation of your decision-making process...",
            "strength_a": "...",
            "strength_b": "...",
            "weaknesses_a": ["[TAG1]"],
            "weaknesses_b": ["[TAG2]"],
            "categories": [
                {{"id": "accuracy", "text": "...", "score": 1}},
                {{"id": "instructions", "text": "...", "score": -2}},
                {{"id": "tone", "text": "...", "score": 3}},
                {{"id": "overall", "text": "...", "score": -1}},
                {{"id": "naming_clarity", "text": "...", "score": 2}},
                {{"id": "organization_modularity", "text": "...", "score": -4}},
                {{"id": "error_handling", "text": "...", "score": 1}},
                {{"id": "documentation", "text": "...", "score": 2}},
                {{"id": "review_readiness", "text": "...", "score": -1}},
                {{"id": "logic_correctness", "text": "...", "score": 3}},
                {{"id": "honesty", "text": "...", "score": -2}},
                {{"id": "instruction_following", "text": "...", "score": 1}}
            ]
        }}
        
        CRITICAL: NO ZERO SCORES. EVERY category MUST have a non-zero score.
        If you are unsure, you MUST pick the response that is slightly clearer or better formatted.
        Choosing zero is a failure of the audit.
        """

        response = client.chat.completions.create(
            model="deepseek-r1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True
        )

        full_content = ""
        in_thinking = False
        
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                full_content += delta
                
                # If we see think tags, use them
                if "<think>" in delta:
                    in_thinking = True
                    continue
                if "</think>" in delta:
                    in_thinking = False
                    yield "THOUGHT_END\n"
                    continue
                
                if in_thinking:
                    yield f"THOUGHT:{delta}\n"
                else:
                    # If we aren't in a think block, but we haven't seen a JSON '{' yet,
                    # treat it as 'pre-thinking' or explanation
                    if "{" not in full_content:
                        yield f"THOUGHT:{delta}\n"
        
        # Parse final result
        # Aggressive JSON cleaning
        content = re.sub(r'<think>.*?</think>', '', full_content, flags=re.DOTALL)
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```', '', content).strip()
        
        # Look for the outermost JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                data = try_parse_json(json_match.group())
            except Exception as e:
                # If lazy JSON parsing fails, try to fix common issues
                raise ValueError(f"AI returned invalid JSON: {str(e)}\nRaw Content: {content[:500]}...")
        else:
            try:
                data = try_parse_json(content)
            except Exception as e:
                raise ValueError(f"AI failed to return valid JSON: {str(e)}\nRaw Content: {content[:500]}...")
            
        # Save results
        thought_match = re.search(r'<think>(.*?)</think>', full_content, re.DOTALL)
        if thought_match:
            eval_obj.ai_thought = thought_match.group(1).strip()
        else:
            # If tags are missing, use everything before the first '{' as thought
            pre_json = full_content.split('{')[0].strip()
            eval_obj.ai_thought = pre_json if pre_json else "No thought tags found."

        eval_obj.ai_logic = data.get('overall_final_reasoning', '')
        eval_obj.overall_rationale = data.get('overall_rationale', '')
        eval_obj.strength_a = data.get('strength_a', '')
        eval_obj.strength_b = data.get('strength_b', '')
        
        # New List-based saving logic
        category_list = data.get('categories', [])
        for item in category_list:
            cid = item.get('id')
            if cid:
                setattr(eval_obj, f'comparison_{cid}', item.get('text', ''))
                # Force non-zero if the model still slips up
                raw_score = item.get('score', 0)
                if raw_score == 0:
                    raw_score = 1 # Default to slight B if it refuses to choose
                setattr(eval_obj, f'score_{cid}', raw_score)
        
        eval_obj.save()

        # Map weaknesses
        eval_obj.weaknesses_a.clear()
        eval_obj.weaknesses_b.clear()

        def add_weaknesses(tags, m2m):
            for w_name in tags:
                cat = WeaknessCategory.objects.filter(name=w_name).first()
                if not cat:
                    tag_match = re.search(r'\[[A-Z]+\]', w_name)
                    if tag_match:
                        cat = WeaknessCategory.objects.filter(name__startswith=tag_match.group()).first()
                if cat: m2m.add(cat)

        add_weaknesses(data.get('weaknesses_a', []), eval_obj.weaknesses_a)
        add_weaknesses(data.get('weaknesses_b', []), eval_obj.weaknesses_b)

        # Build final return data for frontend
        def format_weaknesses(queryset):
            return [{'name': w.name, 'description': w.description, 'examples': w.examples} for w in queryset.all()]

        final_json = {
            'status': 'success',
            'score': eval_obj.score,
            'ai_logic': eval_obj.ai_logic,
            'overall_rationale': eval_obj.overall_rationale,
            'strength_a': eval_obj.strength_a,
            'strength_b': eval_obj.strength_b,
            'categories': category_list,
            'weaknesses_a': format_weaknesses(eval_obj.weaknesses_a),
            'weaknesses_b': format_weaknesses(eval_obj.weaknesses_b),
        }
        yield f"DATA:{json.dumps(final_json)}\n"

    except Exception as e:
        yield f"ERROR:{str(e)}\n"

def auto_evaluate(evaluation_id):
    # Synchronous wrapper for the streaming version
    gen = auto_evaluate_stream(evaluation_id)
    success = False
    for chunk in gen:
        if chunk.startswith("DATA:"):
            success = True
        elif chunk.startswith("ERROR:"):
            success = False
    return success

def evaluate_prompt_quality(prompt_text):
    try:
        system_prompt = "You are an expert prompt engineer. Evaluate the user's prompt for clarity, constraints, and effectiveness on a scale of 1-5. Respond and reason exclusively in English."
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
            model="deepseek-r1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4096,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        # Remove thinking and common markdown wrappers
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = re.sub(r'```json|```', '', content).strip()

        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(content)
            
        return data  # {'score': x, 'feedback': '...'}
    # FIXED: Changed from OpenAI.APIConnectionError to openai.APIConnectionError
    # except OpenAI.APIConnectionError as e:
    except (APIConnectionError, APIStatusError, APITimeoutError, openai.AuthenticationError) as e:
        # User requested no console output
        # print(f"Connection error during prompt evaluation: {e.__cause__}")
        return {'score': 0, 'feedback': f"Error: A connection error occurred. Details: {str(e)}"}
    except Exception as e:
        return {'score': 0, 'feedback': f"Error: {str(e)}"}

def scan_response_weaknesses_stream(prompt_text, response_text):
    """
    A generator that yields the 'thinking' trail first, then the final JSON data.
    """
    try:
        categories = list(WeaknessCategory.objects.values_list('name', flat=True))
        system_prompt = "You are an AI quality auditor. Scan a single AI response against specific weakness criteria and identify its strengths. Respond and reason exclusively in English."
        user_prompt = f"""
        Original Prompt: "{prompt_text}"
        AI Response: "{response_text}"
        
        CRITICAL: Use ONLY these Category Names for identification: {categories}
        
        INSTRUCTIONS:
        1. Identify ALL relevant weaknesses from the list above that are present in this specific response.
        2. Provide a 1-sentence explanation for each.
        3. Identify main strengths.
        
        Return ONLY JSON:
        {{
            "strength": "desc...",
            "found_weaknesses": [{{"name": "[TAG]", "reason": "reason..."}}]
        }}
        """

        response = client.chat.completions.create(
            model="deepseek-r1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True
        )

        full_content = ""
        in_thinking = False
        
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                full_content += delta
                # Yield thinking parts to the frontend
                if "<think>" in delta:
                    in_thinking = True
                    continue
                if "</think>" in delta:
                    in_thinking = False
                    yield "THOUGHT_END\n"
                    continue
                
                if in_thinking:
                    yield f"THOUGHT:{delta}\n"
                else:
                    if "{" not in full_content:
                        yield f"THOUGHT:{delta}\n"

        # Cleanup and Parse the final JSON
        content = re.sub(r'<think>.*?</think>', '', full_content, flags=re.DOTALL)
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```', '', content).strip()
        
        # Look for the outermost JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                data = try_parse_json(json_match.group())
            except Exception as e:
                raise ValueError(f"AI returned invalid JSON: {str(e)}\nRaw Content: {content[:500]}...")
        else:
            try:
                data = try_parse_json(content)
            except Exception as e:
                raise ValueError(f"AI failed to return valid JSON: {str(e)}\nRaw Content: {content[:500]}...")
            
        yield f"DATA:{json.dumps(data)}\n"

    except Exception as e:
        yield f"ERROR:{str(e)}\n"

def scan_response_weaknesses(prompt_text, response_text):
    # Synchronous version for simple calls
    gen = scan_response_weaknesses_stream(prompt_text, response_text)
    data = {"strength": "Error: Analysis failed", "found_weaknesses": []}
    for chunk in gen:
        if chunk.startswith("DATA:"):
            data = json.loads(chunk[5:])
    return data