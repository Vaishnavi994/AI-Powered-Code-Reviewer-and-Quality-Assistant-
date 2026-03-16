# import ast
# import os
# import re


# def to_snake_case(name):
#     s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
#     return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# class CodeTransformer(ast.NodeTransformer):
#     def __init__(self, file_name, source_lines):
#         self.file_name = file_name
#         self.errors = []
#         self.source_lines = source_lines

#     def visit_FunctionDef(self, node):
#         self.generic_visit(node)

#         func_line_index = node.lineno - 1  # zero-based index

#         # 🔥 RULE 1: Blank line immediately after def
#         if func_line_index + 1 < len(self.source_lines):
#             if self.source_lines[func_line_index + 1].strip() == "":
#                 self.errors.append(
#                     f"{self.file_name}: Blank line immediately after function definition at line {node.lineno}"
#                 )

#         # 🔥 RULE 2: Docstring must be first statement
#         has_proper_docstring = (
#             len(node.body) > 0
#             and isinstance(node.body[0], ast.Expr)
#             and isinstance(node.body[0].value, ast.Constant)
#             and isinstance(node.body[0].value.value, str)
#         )

#         if not has_proper_docstring:
#             self.errors.append(
#                 f"{self.file_name}: Missing docstring in '{node.name}'"
#             )

#             # Auto insert docstring
#             docstring_text = f"{node.name.replace('_', ' ').capitalize()} function."
#             doc_node = ast.Expr(value=ast.Constant(value=docstring_text))
#             node.body.insert(0, doc_node)

#         else:
#             docstring = node.body[0].value.value

#             # 🔥 RULE 3: Docstring must end with period
#             if not docstring.strip().endswith("."):
#                 self.errors.append(
#                     f"{self.file_name}: Docstring in '{node.name}' must end with a period."
#                 )
#                 node.body[0].value = ast.Constant(value=docstring.strip() + ".")

#         # 🔥 Variable naming rule
#         for child in ast.walk(node):
#             if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
#                 if not re.match(r'^[a-z_][a-z0-9_]*$', child.id):
#                     old = child.id
#                     child.id = to_snake_case(child.id)
#                     self.errors.append(
#                         f"{self.file_name}: Improper variable '{old}'"
#                     )

#         return node


# def detect_consecutive_blank_lines(source, file_name):
#     lines = source.split("\n")
#     errors = []
#     blank_count = 0

#     for i, line in enumerate(lines):
#         if line.strip() == "":
#             blank_count += 1
#             if blank_count == 3:
#                 errors.append(
#                     f"{file_name}: Too many consecutive blank lines near line {i+1}"
#                 )
#         else:
#             blank_count = 0

#     return errors


# def analyze_and_fix(file_path):
#     file_name = os.path.basename(file_path)

#     try:
#         with open(file_path, "r", encoding="utf-8") as f:
#             source = f.read()

#         source_lines = source.split("\n")
#         blank_errors = detect_consecutive_blank_lines(source, file_name)

#         tree = ast.parse(source)

#     except SyntaxError as e:
#         print(f"\n❌ Syntax Error in file: {file_name}")
#         print(e)
#         return

#     transformer = CodeTransformer(file_name, source_lines)
#     new_tree = transformer.visit(tree)
#     ast.fix_missing_locations(new_tree)

#     all_errors = transformer.errors + blank_errors

#     if not all_errors:
#         print("✅ No errors found!")
#         return

#     print("\n🔎 Errors Found:\n")
#     for err in sorted(set(all_errors)):
#         print("❌", err)

#     choice = input("\nDo you want to fix them? (yes/no): ").strip().lower()
#     if choice != "yes":
#         print("\n⚠ No changes made.")
#         return

#     new_code = ast.unparse(new_tree)

#     with open(file_path, "w", encoding="utf-8") as f:
#         f.write(new_code)

#     print("\n✅ All errors fixed safely using AST rewrite!")


# if __name__ == "__main__":
#     path = input("Enter Python file path: ").strip()
#     analyze_and_fix(path)




# import ast
# import os
# import re


# def to_snake_case(name):
#     s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
#     return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# class CodeTransformer(ast.NodeTransformer):
#     def __init__(self, file_name, source_lines):
#         self.file_name = file_name
#         self.errors = []
#         self.source_lines = source_lines

#     # 🔥 Google-style docstring generator
#     def generate_docstring(self, node):
#         func_name = node.name.replace("_", " ").capitalize()

#         # Parameters
#         params = []
#         for arg in node.args.args:
#             params.append(f"        {arg.arg}: Description.")

#         args_section = ""
#         if params:
#             args_section = "\n\n    Args:\n" + "\n".join(params)

#         # Returns detection
#         has_return = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node))
#         returns_section = ""
#         if has_return:
#             returns_section = "\n\n    Returns:\n        Description."

#         # Raises detection (actual exception type)
#         raise_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Raise)]
#         raises_section = ""
#         if raise_nodes:
#             exception_names = []
#             for r in raise_nodes:
#                 if isinstance(r.exc, ast.Call) and isinstance(r.exc.func, ast.Name):
#                     exception_names.append(r.exc.func.id)
#                 elif isinstance(r.exc, ast.Name):
#                     exception_names.append(r.exc.id)

#             exception_names = list(set(exception_names))
#             raise_lines = "\n".join([f"        {exc}: Description." for exc in exception_names])
#             raises_section = f"\n\n    Raises:\n{raise_lines}"

#         docstring = f"""{func_name} function.{args_section}{returns_section}{raises_section}
#     """

#         return docstring

#     def visit_FunctionDef(self, node):
#         self.generic_visit(node)

#         func_line_index = node.lineno - 1

#         # ❌ Blank line immediately after def
#         if func_line_index + 1 < len(self.source_lines):
#             if self.source_lines[func_line_index + 1].strip() == "":
#                 self.errors.append(
#                     f"{self.file_name}: Blank line immediately after function definition at line {node.lineno}"
#                 )

#         # ✅ Check if proper docstring exists as first statement
#         has_proper_docstring = (
#             len(node.body) > 0
#             and isinstance(node.body[0], ast.Expr)
#             and isinstance(node.body[0].value, ast.Constant)
#             and isinstance(node.body[0].value.value, str)
#         )

#         if not has_proper_docstring:
#             self.errors.append(
#                 f"{self.file_name}: Missing docstring in '{node.name}'"
#             )

#             docstring_text = self.generate_docstring(node)
#             doc_node = ast.Expr(value=ast.Constant(value=docstring_text))
#             node.body.insert(0, doc_node)

#         else:
#             docstring = node.body[0].value.value

#             if not docstring.strip().endswith("."):
#                 self.errors.append(
#                     f"{self.file_name}: Docstring in '{node.name}' must end with a period."
#                 )
#                 node.body[0].value = ast.Constant(value=docstring.strip() + ".")

#         # 🔥 Fix variable naming
#         for child in ast.walk(node):
#             if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
#                 if not re.match(r'^[a-z_][a-z0-9_]*$', child.id):
#                     old = child.id
#                     child.id = to_snake_case(child.id)
#                     self.errors.append(
#                         f"{self.file_name}: Improper variable '{old}'"
#                     )

#         return node


# def detect_consecutive_blank_lines(source, file_name):
#     lines = source.split("\n")
#     errors = []
#     blank_count = 0

#     for i, line in enumerate(lines):
#         if line.strip() == "":
#             blank_count += 1
#             if blank_count == 3:
#                 errors.append(
#                     f"{file_name}: Too many consecutive blank lines near line {i+1}"
#                 )
#         else:
#             blank_count = 0

#     return errors


# def analyze_and_fix(file_path):
#     file_name = os.path.basename(file_path)

#     try:
#         with open(file_path, "r", encoding="utf-8") as f:
#             source = f.read()

#         source_lines = source.split("\n")
#         blank_errors = detect_consecutive_blank_lines(source, file_name)

#         tree = ast.parse(source)

#     except SyntaxError as e:
#         print(f"\n❌ Syntax Error in file: {file_name}")
#         print(e)
#         return

#     transformer = CodeTransformer(file_name, source_lines)
#     new_tree = transformer.visit(tree)
#     ast.fix_missing_locations(new_tree)

#     all_errors = transformer.errors + blank_errors

#     if not all_errors:
#         print("✅ No errors found!")
#         return

#     print("\n🔎 Errors Found:\n")
#     for err in sorted(set(all_errors)):
#         print("❌", err)

#     choice = input("\nDo you want to fix them? (yes/no): ").strip().lower()
#     if choice != "yes":
#         print("\n⚠ No changes made.")
#         return

#     new_code = ast.unparse(new_tree)

#     with open(file_path, "w", encoding="utf-8") as f:
#         f.write(new_code)

#     print("\n✅ All errors fixed safely using AST rewrite!")


# if __name__ == "__main__":
#     path = input("Enter Python file path: ").strip()
#     analyze_and_fix(path)

import ast
import os
import re


def to_snake_case(name):
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class CodeTransformer(ast.NodeTransformer):
    def __init__(self, file_name, source_lines):
        self.file_name = file_name
        self.errors = []
        self.source_lines = source_lines

    def generate_docstring(self, node):
        func_name = node.name.replace("_", " ").capitalize()

        params = []
        for arg in node.args.args:
            params.append(f"        {arg.arg}: Description.")

        args_section = ""
        if params:
            args_section = "\n\n    Args:\n" + "\n".join(params)

        has_return = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node))
        returns_section = ""
        if has_return:
            returns_section = "\n\n    Returns:\n        Description."

        raise_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Raise)]
        raises_section = ""
        if raise_nodes:
            exception_names = []
            for r in raise_nodes:
                if isinstance(r.exc, ast.Call) and isinstance(r.exc.func, ast.Name):
                    exception_names.append(r.exc.func.id)
                elif isinstance(r.exc, ast.Name):
                    exception_names.append(r.exc.id)

            exception_names = list(set(exception_names))
            raise_lines = "\n".join([f"        {exc}: Description." for exc in exception_names])
            raises_section = f"\n\n    Raises:\n{raise_lines}"

        docstring = f"""{func_name} function.{args_section}{returns_section}{raises_section}
    """
        return docstring

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        func_line_index = node.lineno - 1

        if func_line_index + 1 < len(self.source_lines):
            if self.source_lines[func_line_index + 1].strip() == "":
                self.errors.append(
                    f"{self.file_name}: Blank line immediately after function definition at line {node.lineno}"
                )

        has_proper_docstring = (
            len(node.body) > 0
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        )

        if not has_proper_docstring:
            self.errors.append(f"{self.file_name}: Missing docstring in '{node.name}'")
            doc_node = ast.Expr(value=ast.Constant(value=self.generate_docstring(node)))
            node.body.insert(0, doc_node)
        else:
            docstring = node.body[0].value.value
            if not docstring.strip().endswith("."):
                self.errors.append(f"{self.file_name}: Docstring in '{node.name}' must end with a period.")
                node.body[0].value = ast.Constant(value=docstring.strip() + ".")

        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                if not re.match(r'^[a-z_][a-z0-9_]*$', child.id):
                    old = child.id
                    child.id = to_snake_case(child.id)
                    self.errors.append(f"{self.file_name}: Improper variable '{old}'")

        return node


def detect_consecutive_blank_lines(source, file_name):
    lines = source.split("\n")
    errors = []
    blank_count = 0

    for i, line in enumerate(lines):
        if line.strip() == "":
            blank_count += 1
            if blank_count == 3:
                errors.append(f"{file_name}: Too many consecutive blank lines near line {i+1}")
        else:
            blank_count = 0

    return errors


# 🔥 NEW: FIX SOURCE STRING AND RETURN UPDATED CODE (for Streamlit)
def fix_source_code(source: str, file_name: str):
    source_lines = source.split("\n")

    tree = ast.parse(source)
    transformer = CodeTransformer(file_name, source_lines)
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    updated_code = ast.unparse(new_tree)

    # normalize blank lines (max 1)
    lines = updated_code.split("\n")
    cleaned = []
    blanks = 0
    for l in lines:
        if not l.strip():
            blanks += 1
            if blanks <= 1:
                cleaned.append(l)
        else:
            blanks = 0
            cleaned.append(l)

    updated_code = "\n".join(cleaned)

    errors = transformer.errors + detect_consecutive_blank_lines(source, file_name)
    return errors, updated_code