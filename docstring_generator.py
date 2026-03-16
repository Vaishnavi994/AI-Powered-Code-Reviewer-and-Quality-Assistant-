

# import ast
# import os
# from groq import Groq
# from dotenv import load_dotenv

# # 1. Load environment variables
# load_dotenv()

# # 2. Initialize the client
# api_key = os.getenv("GROQ_API_KEY")
# client = Groq(api_key=api_key)

# def remove_existing_docstring(code):
#     """
#     Removes an existing docstring from a Python function code block.
#     This ensures we don't end up with double docstrings.
#     """
#     try:
#         tree = ast.parse(code)
#         for node in ast.walk(tree):
#             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
#                 if (node.body and isinstance(node.body[0], ast.Expr) and 
#                     isinstance(node.body[0].value, ast.Constant) and 
#                     isinstance(node.body[0].value.value, str)):
#                     node.body.pop(0)
#         return ast.unparse(tree)
#     except Exception:
#         return code


# # def generate_docstring(function_code, style):
# #     """Generates a docstring with strict style rules."""
# #     style_guidance = ""
    
# #     if style == "Google":
# #         style_guidance = """
# #         STRICT RULES FOR Google Style:
# #         - Use 'Args:' section for parameters.
# #         - Use 'Returns:' section for return values.
# #         - Do NOT use :param: or :rtype: (that is reST).
# #         - Format: 
# #             Args:
# #                 name (type): description
# #             Returns:
# #                 type: description
# #         """
# #     elif style == "reST":
# #         style_guidance = """
# #         STRICT RULES FOR reStructuredText:
# #         - Use :param name: description
# #         - Use :type name: type
# #         - Use :return: description
# #         - Use :rtype: type
# #         - Do NOT use 'Args:' or 'Returns:' headers.
# #         """
# #     elif style == "NumPy":
# #         style_guidance = """
# #         STRICT RULES FOR NumPy Style:
# #         - Use 'Parameters' and 'Returns' sections.
# #         - Underline headers with hyphens (---).
# #         - Format:
# #             Parameters
# #             ----------
# #             name : type
# #                 Description.
# #         """

# #     prompt = f"""
# #     Generate a {style} docstring for the provided Python code.
    
# #     {style_guidance}
    
# #     General Rules:
# #     - Return ONLY the docstring starting and ending with \"\"\"
# #     - Do not include any explanations, markdown code blocks, or preamble.
# #     - Infer types for parameters and return values accurately.
# #     - If the function has no arguments or returns nothing, omit those sections.

# #     Code:
# #     {function_code}
# #     """

# #     response = client.chat.completions.create(
# #         model="llama-3.3-70b-versatile",
# #         messages=[
# #             {"role": "system", "content": f"You are a technical writer specialized in {style} documentation."},
# #             {"role": "user", "content": prompt}
# #         ],
# #         temperature=0.1 # Keep this low to ensure consistency
# #     )

# #     doc = response.choices[0].message.content.strip()
    
# #     # Robust cleaning of potential LLM "chatter"
# #     doc = doc.replace("```python", "").replace("```", "").strip()
    
# #     # Ensure it's wrapped in triple quotes once
# #     if not doc.startswith('"""'): doc = '"""\n' + doc
# #     if not doc.endswith('"""'): doc = doc + '\n"""'
    
# #     return doc


# def generate_docstring(function_input, style):
#     """
#     Generates a docstring.
#     Works with:
#     1) dictionary input (used by tests)
#     2) real function code (used by the AI generator)
#     """

#     # ---------- TEST MODE (dictionary input) ----------
#     if isinstance(function_input, dict):

#         name = function_input.get("name", "")
#         args = function_input.get("args", [])
#         returns = function_input.get("returns", None)

#         doc = '"""\n'
#         doc += f"{name} function.\n\n"

#         if style.lower() == "google":

#             if args:
#                 doc += "Args:\n"
#                 for arg in args:
#                     doc += f"    {arg['name']}: description\n"

#             if returns:
#                 doc += "\nReturns:\n"
#                 doc += f"    {returns}: description\n"

#         elif style.lower() == "numpy":

#             if args:
#                 doc += "Parameters\n"
#                 doc += "----------\n"
#                 for arg in args:
#                     doc += f"{arg['name']} : type\n"
#                     doc += "    description\n"

#             if returns:
#                 doc += "\nReturns\n"
#                 doc += "-------\n"
#                 doc += f"{returns}\n"
#                 doc += "    description\n"

#         elif style.lower() == "rest":

#             for arg in args:
#                 doc += f":param {arg['name']}: description\n"
#                 doc += f":type {arg['name']}: type\n"

#             if returns:
#                 doc += f":return: description\n"
#                 doc += f":rtype: {returns}\n"

#         else:
#             raise ValueError("Invalid docstring style")

#         doc += '"""'
#         return doc

#     # ---------- AI MODE (existing implementation) ----------
#     function_code = function_input

#     style_guidance = ""

#     if style == "Google":
#         style_guidance = """
#         Use 'Args:' and 'Returns:' sections.
#         """

#     elif style == "reST":
#         style_guidance = """
#         Use :param name: description
#         Use :type name: type
#         Use :return: description
#         Use :rtype: type
#         """

#     elif style == "NumPy":
#         style_guidance = """
#         Use 'Parameters' and 'Returns' sections.
#         """

#     prompt = f"""
# Generate a {style} docstring.

# {style_guidance}

# Code:
# {function_code}
# """

#     response = client.chat.completions.create(
#         model="llama-3.3-70b-versatile",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.1
#     )

#     doc = response.choices[0].message.content.strip()

#     doc = doc.replace("```python", "").replace("```", "").strip()

#     if not doc.startswith('"""'):
#         doc = '"""\n' + doc
#     if not doc.endswith('"""'):
#         doc = doc + '\n"""'

#     return doc
# def insert_docstring(function_code, docstring):
#     """Inserts the generated docstring with correct indentation."""
#     lines = function_code.split("\n")
#     for i, line in enumerate(lines):
#         if line.strip().startswith("def "):
#             base_indent = len(line) - len(line.lstrip())
#             indent = " " * (base_indent + 4)
#             doc_lines = docstring.split("\n")
#             doc_lines = [indent + l if l.strip() != "" else "" for l in doc_lines]
#             lines.insert(i + 1, "\n".join(doc_lines))
#             break
#     return "\n".join(lines)

# def update_function_in_file(file_path, function_name, new_function_code):
#     """Handles nested class methods and preserves indentation."""
#     with open(file_path, "r", encoding="utf-8") as f:
#         lines = f.readlines()

#     source = "".join(lines)
#     tree = ast.parse(source)
    
#     target_node = None
#     for node in ast.walk(tree):
#         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
#             target_node = node
#             break

#     if target_node:
#         start_line = target_node.lineno - 1
#         end_line = target_node.end_lineno
#         original_line = lines[start_line]
#         indentation = original_line[:len(original_line) - len(original_line.lstrip())]
        
#         indented_new_code = "\n".join([indentation + l if l.strip() else "" 
#                                       for l in new_function_code.splitlines()])
        
#         lines[start_line:end_line] = [indented_new_code + "\n"]
        
#         with open(file_path, "w", encoding="utf-8") as f:
#             f.writelines(lines)
#     else:
#         print(f"Error: Could not find {function_name}")




import ast
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


# ---------------------------------------------------
# Remove existing docstring
# ---------------------------------------------------

def remove_existing_docstring(code):
    """Remove an existing docstring from a function."""

    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    node.body.pop(0)

        return ast.unparse(tree)

    except Exception:
        return code


# ---------------------------------------------------
# Generate docstring
# ---------------------------------------------------

def generate_docstring(function_input, style):
    style = style.lower()
    """
    Generates a docstring.

    Supports:
    1. Dictionary input (for tests)
    2. Function code input (AI generation)
    """

    # ---------------------------------------------------
    # TEST MODE (dictionary input)
    # ---------------------------------------------------

    if isinstance(function_input, dict):

        name = function_input.get("name", "")
        args = function_input.get("args", [])
        returns = function_input.get("returns", None)

        style = style.lower()

        doc = '"""\n'
        doc += f"{name} function.\n\n"

        if style == "google":

            if args:
                doc += "Args:\n"
                for arg in args:
                    doc += f"    {arg['name']}: description\n"

            if returns:
                doc += "\nReturns:\n"
                doc += f"    {returns}: description\n"

        elif style == "numpy":

            if args:
                doc += "Parameters\n"
                doc += "----------\n"

                for arg in args:
                    doc += f"{arg['name']} : type\n"
                    doc += "    description\n"

            if returns:
                doc += "\nReturns\n"
                doc += "-------\n"
                doc += f"{returns}\n"
                doc += "    description\n"

        elif style == "rest":

            for arg in args:
                doc += f":param {arg['name']}: description\n"
                doc += f":type {arg['name']}: type\n"

            if returns:
                doc += ":return: description\n"
                doc += f":rtype: {returns}\n"

        else:
            raise ValueError("Invalid docstring style")

        doc += '"""'

        return doc


    # ---------------------------------------------------
    # AI MODE (actual function code)
    # ---------------------------------------------------

    function_code = function_input

    style_guidance = ""

    if style.lower() == "google":

        style_guidance = """
Use Google docstring style.

Args:
    name (type): description

Returns:
    type: description
"""

    elif style.lower() == "numpy":

        style_guidance = """
Use NumPy docstring style.

Parameters
----------
name : type
    description

Returns
-------
type
    description
"""

    elif style.lower() == "rest":

        style_guidance = """
Use reStructuredText docstring style.

:param name: description
:type name: type
:return: description
:rtype: type
"""

    prompt = f"""
Generate a {style} style Python docstring.

Rules:
- Return ONLY the docstring
- Start and end with triple quotes
- Do NOT include markdown
- Do NOT explain the code
- Infer parameter and return types

Code:
{function_code}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert Python documentation writer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    doc = response.choices[0].message.content.strip()

    # ---------------------------------------------------
    # CLEAN LLM OUTPUT
    # ---------------------------------------------------

    doc = doc.replace("```python", "").replace("```", "").strip()

    # Remove indentation from AI output
    cleaned_lines = [line.strip() for line in doc.splitlines()]
    doc = "\n".join(cleaned_lines)

    if not doc.startswith('"""'):
        doc = '"""\n' + doc

    if not doc.endswith('"""'):
        doc = doc + '\n"""'

    return doc


# ---------------------------------------------------
# Insert docstring into function
# ---------------------------------------------------

def insert_docstring(function_code, docstring):
    """Insert docstring under function definition safely."""

    lines = function_code.split("\n")

    for i, line in enumerate(lines):

        if line.strip().startswith("def ") or line.strip().startswith("async def"):

            base_indent = len(line) - len(line.lstrip())
            indent = " " * (base_indent + 4)

            doc_lines = docstring.strip().split("\n")

            formatted_doc = []

            for l in doc_lines:

                if l.strip():
                    formatted_doc.append(indent + l.strip())
                else:
                    formatted_doc.append("")

            lines.insert(i + 1, "\n".join(formatted_doc))
            break

    return "\n".join(lines)


# ---------------------------------------------------
# Update function inside file safely
# ---------------------------------------------------

def update_function_in_file(file_path, function_name, new_function_code):
    """Replace function in file safely after validating syntax."""

    # Validate syntax before writing
    try:
        ast.parse(new_function_code)
    except SyntaxError:
        print("Generated code invalid. Skipping update.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    source = "".join(lines)

    tree = ast.parse(source)

    target_node = None

    for node in ast.walk(tree):

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            target_node = node
            break

    if not target_node:
        print(f"Function {function_name} not found")
        return

    start_line = target_node.lineno - 1
    end_line = target_node.end_lineno

    original_line = lines[start_line]

    indentation = original_line[: len(original_line) - len(original_line.lstrip())]

    indented_new_code = "\n".join(
        [indentation + l if l.strip() else "" for l in new_function_code.splitlines()]
    )

    lines[start_line:end_line] = [indented_new_code + "\n"]

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)