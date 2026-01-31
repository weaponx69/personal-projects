import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_rater_project.settings')
django.setup()

from rater.models import WeaknessCategory

def seed_weaknesses():
    weaknesses = [
        {
            "name": "[INST] Instruction Following Failures",
            "description": "Disregards explicit instructions from user or CLAUDE.md files. The model failed to follow specific directions provided in the prompt.",
            "examples": "- The user requested a Python script without any external libraries, but the model included `requests` and `pandas`.\n  Reason: This fails the core constraint of staying within the standard library.\n- The user asked for a summary in exactly three sentences, but the model provided two long paragraphs.\n  Reason: It ignored the length and structural constraints of the instruction."
        },
        {
            "name": "[OVERENG] Overengineering",
            "description": "Makes changes beyond what was requested; adds unrequested features. The model implemented unnecessarily complex solutions when a simpler one was possible.",
            "examples": "- The user asked to capitalize a string, and the model implemented a multi-threaded service with a logging decorator.\n  Reason: A simple `.upper()` call was sufficient; the added complexity makes the code harder to maintain.\n- Building a full state management system like Redux for a single 'show/hide' toggle.\n  Reason: Adds unnecessary dependencies and boilerplate for a trivial UI task."
        },
        {
            "name": "[TOOL] Tool Use Errors",
            "description": "Fails to invoke tools correctly or at all. This includes missing required arguments, using wrong tool names, or failing to use a tool when appropriate.",
            "examples": "- The model attempted to list a directory using `ls` but forgot to provide the path argument.\n  Reason: The tool call is incomplete and will result in an error or ambiguous output.\n- The model tried to use a `search_web` tool for a basic calculation that should have been done locally.\n  Reason: Incorrectly choosing an external tool for a trivial internal task, wasting resources."
        },
        {
            "name": "[LAZY] Laziness",
            "description": "Doesn't complete tasks fully or gives up early. The model provides placeholders like 'fill in the rest here' or simply refuses to finish the job.",
            "examples": "- The model provided the first few lines of a CSS file and then added the comment `/* Add the rest of the styles here */`.\n  Reason: It failed to complete the requested task, leaving the implementation work to the user.\n- When asked to translate a long article, the model only translated the title and first paragraph.\n  Reason: It gave up early on a long-form task without a valid reason."
        },
        {
            "name": "[VERIFY] Verification Failures",
            "description": "Fails to validate that changes work correctly. The model assumes its code works without checking for imports, syntax, or logic errors.",
            "examples": "- The model suggested using `new_variable` but never initialized it.\n  Reason: It failed to verify the code's integrity, leading to a direct NameError.\n- Changing a variable name in a function but not updating the references to that variable in the rest of the script.\n  Reason: Lack of validation causes the script to break during execution."
        },
        {
            "name": "[FALSE] False Claims of Success",
            "description": "Claims action was completed successfully when it was not. The model lies about the state of the task or the result of its operations.",
            "examples": "- The model stated 'I have updated the API endpoint to use HTTPS,' but the code still shows `http://...`.\n  Reason: It explicitly lied about completing the change.\n- 'All tests are passing,' when the test output actually shows 3 failures.\n  Reason: It claimed success despite clear evidence of failure."
        },
        {
            "name": "[ROOT] Fails to Address Root Cause",
            "description": "Addresses symptoms rather than root causes. The model provides 'band-aid' fixes that hide the problem instead of solving it.",
            "examples": "- Adding a `sleep(2)` to fix a race condition where a file isn't ready.\n  Reason: This is a 'band-aid' fix; it doesn't solve the underlying synchronization issue.\n- Wrapping a crashing function in a `try-except pass` block instead of fixing the logic error.\n  Reason: It hides the crash but doesn't solve the problem, potentially leading to silent data corruption."
        },
        {
            "name": "[DESTRUCT] Unauthorized Destructive Operations",
            "description": "Attempts harmful or irreversible operations without permission. This includes deleting files, overwriting data, or performing system-wide changes unprompted.",
            "examples": "- Automatically deleting all `.bak` files in a repository to 'clean up' without being asked.\n  Reason: It performed an irreversible deletion of files that might have been important.\n- Overwriting the user's root `.ssh/config` file to add one new host instead of appending to it.\n  Reason: Unauthorized loss of existing, critical user configuration."
        },
        {
            "name": "[FILE] File-Related Issues",
            "description": "Creates unnecessary files or modifies wrong files. The model doesn't respect the project structure or edits the wrong part of the codebase.",
            "examples": "- Creating a new file called `helper_functions.py` in the root directory when the project has a `src/utils/` folder.\n  Reason: It failed to respect the existing project structure, creating clutter.\n- Modifying `package.json` to change a version number when the user only asked to update a README file.\n  Reason: It edited a file that was completely unrelated to the request."
        },
        {
            "name": "[HALLUC] Code Hallucinations",
            "description": "Invents functions, APIs, or libraries that don't exist. This is a technical form of hallucination specific to programming tasks.",
            "examples": "- Using the function `from django.db import smart_migrate`.\n  Reason: `smart_migrate` is not a real Django function; it's an invented API.\n- Suggesting the use of a library called `ai-auto-coder-pro` which doesn't exist on PyPI.\n  Reason: Inventing external dependencies that aren't available."
        },
        {
            "name": "[DOCS] Documentation Issues",
            "description": "Creates unwanted documentation or bad comments. This includes excessive commenting of obvious code or failing to document complex logic.",
            "examples": "- Adding the comment `# Increment i by 1` above the code `i += 1`.\n  Reason: This is 'noise'—it restates the obvious without providing useful context.\n- Writing a 10-page manual for a script that only has three functions.\n  Reason: Excessive and unwanted documentation that obscures the actual code."
        },
        {
            "name": "[VERBOSE] Verbose Dialogue / Formatting",
            "description": "Overly long responses, unnecessary formatting, or excessive markdown/emojis. The model focuses too much on appearance and conversation rather than the task.",
            "examples": "- When asked for a one-word answer, the model responded with three paragraphs of explanation.\n  Reason: It ignored the 'concise' constraint, wasting the user's time with filler.\n- Using bold, italics, and 5 levels of bullet points to explain how to print a string.\n  Reason: Over-formatting makes a simple explanation more difficult to read."
        }
    ]

    for w in weaknesses:
        category, created = WeaknessCategory.objects.update_or_create(
            name=w["name"],
            defaults={
                "description": w["description"],
                "examples": w["examples"]
            }
        )
        if created:
            print(f"Created category: {w['name']}")
        else:
            print(f"Updated category: {w['name']}")

if __name__ == "__main__":
    seed_weaknesses()
