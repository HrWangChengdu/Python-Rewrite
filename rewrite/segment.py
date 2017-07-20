import ast
# Add the wrapper
def segment(node, ndarray_types, is_atomic_func):
    """Segment a node given its information collected in the runtime

    Parameters
    ------
    node:  ast.Ast

    var_types: a list of types for ast.Name, ast.Call return values

    is_atomic_func: a boolean list to denote whether

    # Puzzles:whether we need to record the function type? 
        - it depends on whether @Jit/Atomic decorator is removed in the annotation stage.

    # Potential missing Input: variable liveness, i.e. whether one variable is accessed in the future or not
        - Let's assume all the output variables are accessed, i.e. the worst case
    """
    var_cnt = -1
    func_cnt = -1

    # TODO: how about AugAssign
    seg_list = [IfExp, Delete, For, AsyncFor, While, If, With, AsyncWith, Raise, Try, Assert, Import, ImportFrom, Global, Nonlocal, Expr, Pass, Break, Continue]
    func_checking_list = [Call]
    type_checking_list = [Name, BinOp, UnaryOp, Lambda, Compare, Assign, BoolOp] 


    def fuse_atmoic(node)
    """Fuse the node

    Parameters
    ------
    node:  ast.Ast   


    TODO: Need to infer the inputs and outputs of this node

    The expression could be re-writen to 'run_segment(inputs)'
    The assignment statement should kept its outputs  'outputs = run_segments(inputs)'
    """

    def is_atomic_op(node): 
        nonlocal func_cnt, var_cnt
        if isinstance(node, seg_list):
            return False
        if isinstance(node, func_checking_list):
            func_cnt += 1
            return is_atomic_func[func_cnt]
        if isinstance(node, type_checking_list):
            var_cnt += 1
            return is_ndarray_type[var_cnt]

        return True

    def do_segment(node):
        atom_signs = {}
        all_atom = True
        # Change the use of iter_child_nodes
        for name, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                atom_signs[name] = do_segment(value)
                all_atom &= atom_signs[name]
            elif isinstance(value, list):
                atom_signs[name] = {}
                for i, e in enumerate(value):
                    if (isinstance(e, ast.AST)):
                        atom_signs[name][i] = do_segment(e)
                        all_atom &= atom_signs[name][i] 

        all_atom &= is_atomic(node)

        # If all child nodes are atomic and the operation itself is good, then leave it to its parent
        if all_atom:
            return True

        # TODO: add optimization rules:
        # Rule 1: consecutive atomic statements could be fused

        for name, value in enumerate(ast.iter_fields(node)):
            if isinstance(value, ast.AST) and (atom_signs[name])
                new_value = fuse_atomic(value)
                setattr(node, name, new_value)
            elif isinstance(value, list):
                new_values = []
                for i, e in enumerate(value):
                    if isinstance(e, ast.AST) and atom_signs[name][i]:
                        e = fuse_atomic(e)
                    new_values.append(e)
                value[:] = new_values
        return False

    if (insert_bound(node))
        node = fuse_atomic(node)
