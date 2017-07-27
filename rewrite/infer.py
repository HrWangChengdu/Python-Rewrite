from __future__ import print_function
import ast
from collections import OrderedDict
from .common import UnexpectedNodeType
from functools import reduce


def infer_inputs_and_outputs_given_nodes(nodes):
    """Given a/a list of ast-node, output the input ids (names)
    """
    # TODO: A set to inst
    if isinstance(nodes, list):
        ins = []
        outs = []
        for node in nodes:
            sub_ins, sub_outs = infer_inputs_and_outputs_given_node(node)
            ins += [x for x in sub_ins if x not in outs]
            outs += sub_outs
        return list(
            OrderedDict.fromkeys(ins)), list(
            OrderedDict.fromkeys(outs))
    else:
        return infer_inputs_and_outputs_given_node(nodes)


def infer_inputs_and_outputs_given_node(node):
    """
        The node could only be assign-statement or expressions
    """
    if isinstance(node, ast.Assign):
        # get inputs from its value expression
        ins, _ = infer_inputs_and_outputs_given_node(node.value)
        # treat all the targets as outputs
        outs = [name.id for name in node.targets]
        return ins, outs
    elif isinstance(node, ast.expr):
        return infer_inputs_given_exprs(node), []
    else:
        raise UnexpectedNodeType(type(node))


def infer_inputs_given_exprs(expr):
    """
    TODO:
      - handle the slice object
      - need to know the actual type of the left operand of attribute
        - if it's module or class, then return []
    """
    if isinstance(expr, list):
        return list(OrderedDict.fromkeys(reduce(lambda x, y: x + y,
                                                [infer_inputs_given_exprs(e) for e in expr])))
    elif isinstance(expr, ast.Call):
        return infer_inputs_given_exprs(expr.args)
    elif isinstance(expr, ast.BinOp):
        return infer_inputs_given_exprs([expr.left, expr.right])
    elif isinstance(expr, ast.UnaryOp):
        return infer_inputs_given_exprs(expr.operand)
    elif isinstance(expr, ast.Tuple):
        return infer_inputs_given_exprs(expr.elts)
    elif isinstance(expr, ast.Attribute):
        # Assumption: left operand is a Name
        assert(isinstance(expr.expr, ast.Name))
        return [expr.expr.id + "." + expr.attr]
    elif isinstance(expr, ast.Subscript):
        # Assumption: left operand is a Name
        assert(isinstance(expr.expr, ast.Name))
        return [expr.expr.id + "_subscript_"]
    elif isinstance(expr, ast.Name):
        return [expr.id]
    elif isinstance(expr, (ast.Num, ast.Str, ast.Bytes)):
        return []

    raise UnexpectedNodeType(type(expr))
