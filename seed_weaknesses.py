import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_rater_project.settings')
django.setup()

from rater.models import WeaknessCategory

def seed_weaknesses():
    weaknesses = [
        {
            "name": "Hallucination",
            "description": "The model generates information that is factually incorrect, non-existent, or contradicted by the provided context. This undermines the reliability of the output.",
            "examples": "Example: The model claims that a person was born in 1995 when their actual birth year is 1982. \nExample: The model quotes a law or statistic that does not exist."
        },
        {
            "name": "Verbosity",
            "description": "The response contains excessive wordiness, repetitive phrasing, or 'fluff' that does not add value. It forces the reader to sift through filler to find the actual answer.",
            "examples": "Example: 'In order to explore the multifaceted nature of this complex question, it is first necessary to establish a foundational understanding...' \nExample: Repeating the same point three times using slightly different synonyms."
        },
        {
            "name": "Instructions Ignored",
            "description": "The model failed to adhere to specific constraints provided in the prompt, such as formatting requirements, word counts, or 'negative' constraints (e.g., 'Do not use the word X').",
            "examples": "Example: The user asked for a bulleted list, but the model provided a large block of text. \nExample: The user asked to avoid code, but the model included a Python snippet."
        },
        {
            "name": "Tone Mismatch",
            "description": "The language used is inappropriate for the intended audience or persona. It may be too formal, too casual, or sound overly robotic and 'AI-like'.",
            "examples": "Example: A corporate announcement written like a text message to a friend. \nExample: A creative writing piece that uses overly sterile, clinical language."
        },
        {
            "name": "Logic Error",
            "description": "The model makes a reasoning mistake, mathematical error, or provides a nonsensical conclusion that doesn't follow from the premises.",
            "examples": "Example: Claiming that 10 - 5 = 6. \nExample: Stating that 'John is taller than Mark' and 'Mark is taller than John' in the same paragraph."
        }
    ]

    for w in weaknesses:
        category, created = WeaknessCategory.objects.get_or_create(name=w["name"])
        category.description = w["description"]
        category.examples = w["examples"]
        category.save()
        if created:
            print(f"Created category: {w['name']}")
        else:
            print(f"Updated category: {w['name']}")

if __name__ == "__main__":
    seed_weaknesses()
