import ast
import textwrap

def insert_or_update_docstring(file_path, function_name, new_docstring):

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    source = "".join(lines)
    tree = ast.parse(source)

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef) and node.name == function_name:

            start_line = node.lineno - 1

            indent = len(lines[start_line]) - len(lines[start_line].lstrip())
            indent_spaces = " " * (indent + 4)

            clean_doc = textwrap.dedent(new_docstring).strip().strip('"""').strip()

            formatted_doc = indent_spaces + '"""\n'

            for line in clean_doc.split("\n"):
                formatted_doc += indent_spaces + line.rstrip() + "\n"

            formatted_doc += indent_spaces + '"""\n'

            if ast.get_docstring(node):

                doc_node = node.body[0]
                doc_start = doc_node.lineno - 1
                doc_end = doc_node.end_lineno

                lines[doc_start:doc_end] = [formatted_doc]

            else:

                insert_position = start_line + 1
                lines.insert(insert_position, formatted_doc)

            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)