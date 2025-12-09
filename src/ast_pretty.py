# src/ast_pretty.py

from parser import (
    ProgramNode, DataDeclarationNode, AssignmentNode,
    SelectQueryNode, FilterQueryNode, AggregationNode, PrintNode
)

def pretty(node):
    """Return a pretty ASCII tree of the AST."""
    lines = []

    def render(n, prefix="", is_last=True):
        branch = "└── " if is_last else "├── "
        new_prefix = prefix + ("    " if is_last else "│   ")

        if isinstance(n, ProgramNode):
            lines.append("Program")
            for i, stmt in enumerate(n.statements):
                render(stmt, "", i == len(n.statements) - 1)
            return

        # Label formation
        if isinstance(n, DataDeclarationNode):
            label = f"DataDeclaration({n.name} {n.values})"

        elif isinstance(n, AssignmentNode):
            label = "Assignment"
        elif isinstance(n, SelectQueryNode):
            label = "SelectQuery"
        elif isinstance(n, FilterQueryNode):
            label = "FilterQuery"
        elif isinstance(n, AggregationNode):
            label = f"Aggregation({n.func})"
        elif isinstance(n, PrintNode):
            label = f"Print({n.target})"
            lines.append(prefix + branch + label)
            return
        else:
            label = str(n)

        lines.append(prefix + branch + label)

        # Children
        if isinstance(n, AssignmentNode):
            # target
            render(("TARGET", n.target), new_prefix, False)
            # expr
            render(n.expr, new_prefix, True)

        elif isinstance(n, SelectQueryNode):
            render(("condition", n.condition), new_prefix, False)
            render(("source", n.source), new_prefix, True)

        elif isinstance(n, FilterQueryNode):
            render(("mode", n.mode), new_prefix, False)
            render(("source", n.source), new_prefix, True)

        elif isinstance(n, AggregationNode):
            render(("source", n.source), new_prefix, True)

        elif isinstance(n, DataDeclarationNode):
            # Show name + values are in main label, no children
            pass

        elif isinstance(n, tuple):
            # (label, value)
            label, value = n
            lines.append(new_prefix + f"└── {label}: {value}")

    # Start
    render(node)
    return "\n".join(lines)
