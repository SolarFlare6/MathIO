import numpy as np
import pytesseract as pt
import requests as rq
import json
import antlr4
import sympy
import sympy.parsing.latex
import sympy.parsing.latex._parse_latex_antlr
from sympy.parsing.latex import parse_latex
from sympy import solve, simplify, Eq

import cv2 as cv
import pkg_resources

print("Version of antrl4 is:", pkg_resources.get_distribution("antlr4-python3-runtime").version)


# ---------- UTIL FUNCTIONS ----------
def clean_json(text):
    text = text.strip()

    # remove ```json and ```
    text = text.replace("```json", "")
    text = text.replace("```", "")

    return text.strip()


# ---------- OLLAMA FUNCTIONS & VARIABLES ----------
check_url = "http://localhost:11434"
request_url = "http://localhost:11434/api/generate"


# FIRST CALL THIS FUNC IN A IF STATEMENT.
# WHEN IT RETURNS TRUE, CALL THE explain_solution_with_ollama FUNCTION TO GET EXPLANATION.
# IF NO CONNECTION HAS BEEN ESTABLISHED. SHOW EXCPETION RESULT.
def verifyConnection():
    try:
        response = rq.get(check_url)
        if response.status_code == 200:
            return True
    except Exception as e:
        raise Exception("No connection established. Please Check Ollama Model")


"""
This function sends a math expression + final answer to an Ollama model
and returns either a normal text explanation OR a structured JSON result.

------------------------------------------------------------
MODES
------------------------------------------------------------

1. DEFAULT MODE (solution_type = "Text")
------------------------------------------------------------
- The model returns a natural language explanation.
- Output is a single formatted string.
- Best for simple display / debugging / reading.

Example return:
"Step 1: Add 5 and 3...
 Final Answer: 8"

How to use:
result = explain_solution_with_ollama("5+3", 8)
print(result)

------------------------------------------------------------
2. JSON MODE (solution_type = "JSON")
------------------------------------------------------------

Expected format:
{
  "expression": "...",
  "steps": [
    {"explanation": "..."},
    {"explanation": "..."},
    {"explanation": "..."}
  ],
  "answer": "..."
}

How to use:
result = explain_solution_with_ollama("5+3", 8, solution_type="JSON")

Then access:
- result["expression"] → original equation
- result["answer"] → final answer

Loop through steps:
for step in result["steps"]:
    print(step["explanation"])

"""


def explain_solution_with_ollama(expression, answer, solution_type="Text", model="gemma3:4b"):
    if solution_type == "Text":
        prompt = f"""
    You are a precise math tutor.

    You are given:
    1. A mathematical expression:
    {expression}

    2. The correct final answer:
    {answer}

    Your task:
    - Convert the expression into clean math notation
    - Explain short step-by-step reasoning
    - Keep it simple and structured
    - Do NOT change the final answer

    Format:
    EQUATION:
    ...

    STEPS:
    Step 1:
    Step 2:
    Step 3:

    FINAL ANSWER:
    {answer}
    """
    else:
        prompt = f"""
        You are a precise math tutor.

        Return ONLY valid JSON.

        Format:
        {{
          "expression": "{expression}",
          "steps": [
            {{
              "explanation": "what is happening in this step",
              "situation": "current state of the equation after this step"
            }},
            {{
              "explanation": "next step explanation",
              "situation": "updated equation state"
            }},
            {{
              "explanation": "final transformation",
              "situation": "final simplified equation or result"
            }}
          ],
          "answer": "{answer}"
        }}

        Rules:
        - Do NOT include any text outside JSON
        - Do NOT explain outside JSON
        - Each step MUST show a transformation of the equation
        - Keep explanations short and clear
        - Keep situation as a valid math expression
        - Do NOT change the final answer

        Expression:
        {expression}

        Answer:
        {answer}
        """

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.1
    }

    try:
        response = rq.post(request_url, json=payload)

        if response.status_code == 200:
            if solution_type == "Text":
                return response.json()["response"]

            raw_answer = response.json()["response"]
            clean_answer = clean_json(raw_answer)
            parsed_answer = json.loads(clean_answer)
            if isinstance(parsed_answer, dict):
                return parsed_answer
            else:
                raise Exception("Ollama Model Error. Did not send proper JSON. TRY AGAIN!!!")
        else:
            return f"Error: {response.text}"

    except Exception as e:
        return str(e)


print(type(explain_solution_with_ollama("x*2 = 10", 5, solution_type="JSON")))


# ---------- LATEX & SymPy FUNCTIONS ----------

def clean_latex(latex):
    latex = latex.replace("{", "").replace("}", "")
    latex = latex.replace("X", "x")
    return latex


# REQUIRES LATEX FORM OF EQUATION
# RETURNS A TUPLE (expression, answer)
def latex_to_expr_and_answer(latex_input, proceed=True):
    """
    Converts LaTeX → SymPy expression → computes answer.

    Returns:
        (expression, answer)
    """

    if not latex_input:
        print("DEBUG: empty latex input")
        return None, "No input received"

    expr = parse_latex(latex_input)

    if expr is None:
        print("DEBUG: parse_latex failed")
        return None, "Parse error"

    # If it's an equation
    if "=" in latex_input and proceed:
        answer = solve(expr)
    else:
        answer = simplify(expr)

    return expr, answer


# ---------- IMAGE TESSARACT OCR FUNCTIONS ----------

def verify_tesseract_connection():
    try:
        version = pt.get_tesseract_version()
        print(f"Tesseract connected successfully: {version}")
        return True
    except Exception as e:
        print(f"Failed to connect to Tesseract: {e}")
        return False


def image_to_string(greyscale_image, lang="eng"):  # lang = eng || mkd
    """
        Converts a grayscale numpy image into text using Tesseract OCR.
        """

    if isinstance(greyscale_image, np.ndarray):
        extracted_text = pt.image_to_string(greyscale_image, lang=lang)
        return extracted_text
    else:
        raise TypeError("Expected Numpy Array!")

# print(latex_to_expr_and_answer(r"{\frac{11+x}{x^{3}}}+2x(5-x)"))