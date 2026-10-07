import ast
import math
import operator


class SafeCalculator:
    """
    Safe mathematical expression evaluator.

    Only arithmetic operations and selected math functions
    are allowed. Python code execution is not permitted.
    """

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.FloorDiv: operator.floordiv,
    }

    FUNCTIONS = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "ceil": math.ceil,
        "floor": math.floor,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
    }

    CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
    }

    def evaluate(self, expression: str):
        expression = expression.strip()

        if not expression:
            raise ValueError(
                "Expression cannot be empty."
            )

        if len(expression) > 500:
            raise ValueError(
                "Expression is too long."
            )

        tree = ast.parse(
            expression,
            mode="eval"
        )

        return self._evaluate_node(
            tree.body
        )

    def _evaluate_node(self, node):

        if isinstance(
            node,
            ast.Constant
        ):
            if isinstance(
                node.value,
                (int, float)
            ):
                return node.value

            raise ValueError(
                "Only numeric values are allowed."
            )

        if isinstance(
            node,
            ast.BinOp
        ):
            left = self._evaluate_node(
                node.left
            )

            right = self._evaluate_node(
                node.right
            )

            operation = self.OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError(
                    "Unsupported operator."
                )

            return operation(
                left,
                right
            )

        if isinstance(
            node,
            ast.UnaryOp
        ):
            operand = self._evaluate_node(
                node.operand
            )

            operation = self.OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError(
                    "Unsupported unary operator."
                )

            return operation(
                operand
            )

        if isinstance(
            node,
            ast.Name
        ):
            if node.id in self.CONSTANTS:
                return self.CONSTANTS[
                    node.id
                ]

            raise ValueError(
                f"Unknown constant: {node.id}"
            )

        if isinstance(
            node,
            ast.Call
        ):
            if not isinstance(
                node.func,
                ast.Name
            ):
                raise ValueError(
                    "Unsupported function."
                )

            function_name = node.func.id

            function = self.FUNCTIONS.get(
                function_name
            )

            if function is None:
                raise ValueError(
                    f"Unsupported function: {function_name}"
                )

            arguments = [
                self._evaluate_node(argument)
                for argument in node.args
            ]

            return function(*arguments)

        raise ValueError(
            "Unsupported expression."
        )


calculator = SafeCalculator()


def calculate(expression: str) -> dict:
    """
    Calculate a mathematical expression safely.

    Args:
        expression: Mathematical expression such as
                    "25 * 4 + 10" or "sqrt(144)".

    Returns:
        Calculation result.
    """

    try:
        result = calculator.evaluate(
            expression
        )

        return {
            "expression": expression,
            "result": result,
        }

    except Exception as exc:
        return {
            "expression": expression,
            "error": str(exc),
        }