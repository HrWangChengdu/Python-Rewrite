from __future__ import print_function
import ast
import inspect

def segment(f, module_namespace, visualize_mode=False):
    def always_true(x):
        return True
    node = ast.parse(inspect.getsource(f))
    node = do_segment(node, always_true, always_true, visualize_mode)
    node.body[0].name += '_rewritten'
    func_name = node.body[0].name
    global_namespace = module_namespace.copy()
    exec(
        compile(node, filename='<ast>', mode='exec'), global_namespace)

    def wrapper(*args, **kwargs):
        return global_namespace[func_name](*args, **kwargs)
    return wrapper


def do_segment(node, is_ndarray_type, is_atomic_func, visualize_mode):
    """Segment a node given its information collected in the runtime

    Parameters
    ------
    node:  ast.Ast

    is_ndarray_type: the func for checking the types for ast.Name, ast.Call return values

    is_atomic_func: the func to check the existence of @atom

    # Puzzles:whether we need to record the function type? 
        - it depends on whether @Jit/Atomic decorator is removed in the annotation stage.

    # Potential missing Input: variable liveness, i.e. whether one variable is accessed in the future or not
        - Let's assume all the output variables are accessed, i.e. the worst case
    """

    class UnexpectedNodeType(Exception):
        """UnexpectedNodeType"""
        pass

    class AstTypeHelper:
        """
        """
        seg_list = (
            # Module, Function, Class Related
            ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.arguments, ast.ClassDef,
            # Control Flow
            ast.IfExp, ast.Return, ast.Delete, ast.For, ast.AsyncFor, ast.While, ast.If,
            # Special Ops
            ast.With, ast.AsyncWith, ast.Raise, ast.Try, ast.Assert, ast.Import, ast.ImportFrom,
            # More Special Ops
            ast.Global, ast.Nonlocal, ast.Expr, ast.Pass, ast.Break, ast.Continue, ast.Str
            )
    
        func_checking_list = (ast.Call)
    
        # Check its or the computed result's type
        type_checking_list = (ast.Name, ast.BinOp, ast.UnaryOp,  ast.Compare, ast.BoolOp, ast.Attribute, ast.Subscript)
    
        # Types that are not doing any checking:
        non_check_list = (
            # Assignment
            ast.Assign, ast.AugAssign,
            # Basic Data Structure
            ast.List, ast.Tuple,  ast.Dict, ast.Set, ast.Num,
            # Context Related Function
            ast.Load, ast.Store,
            # Operators that are covered by BinOp and UnaryOp
            ast.operator, ast.boolop, ast.unaryop, ast.cmpop,
            # arg
            ast.arg
            )
    
        skip_fuse_list = (ast.arg, ast.Name)
    
        @staticmethod
        def fuse_check(node): 
            # TODO: rewrite this one
            if isinstance(node, AstTypeHelper.seg_list):
                return False
    
            if isinstance(node, AstTypeHelper.func_checking_list):
                return is_atomic_func(node)
    
            if isinstance(node, AstTypeHelper.type_checking_list):
                return is_ndarray_type(node)
    
            if isinstance(node, AstTypeHelper.non_check_list):
                return True
    
            raise UnexpectedNodeType(type(node))

    def fuse(node):
        """Fuse the node or the list of nodes

        Parameters
        ------
        node:  ast.Ast  | the list of ast.Ast

        TODO: Need to infer the inputs and outputs of this node

        The expression could be re-writen to 'run_segment(inputs)'
        The assignment statement should kept its outputs  'outputs = run_segments(inputs)'
        """

        # Do nothing on unit op
        if (isinstance(node, AstTypeHelper.skip_fuse_list)):
            return node

        if (visualize_mode):
            print('----segment start-----')
            if isinstance(node, list):
                for e in node:
                    print(e)
            else:
                print(node)
            print('----segment end-----')

        # TODO: Add aggregation code here
        return node

    def get_consec_assign(values, signs):
        pos, leng = (0, 0)
        while pos < len(values):
            if (isinstance(values[pos], ast.Assign)):
                leng += 1
            else:
                if leng > 0:
                    yield (pos - leng, leng)
                    leng = 0
            pos += 1

        if leng > 0:
            yield (pos - leng, leng)

    def iterate_and_fuse(node):
        """
        Iterate over the AST by DFS and fuse the expr/stmt

        Parameters
        ------
        node
            The ast node

        Returns
        ------
        bool
            True, if all the children nodes can be fused. And fusion is done by some of its ancestor nodes
            False, otherwise
        """
        atom_signs = {}
        all_atom = True
        for name, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                atom_signs[name] = iterate_and_fuse(value)
                all_atom &= atom_signs[name]
            elif isinstance(value, list):
                atom_signs[name] = []
                for i, e in enumerate(value):
                    if (isinstance(e, ast.AST)):
                        atom_signs[name].append(iterate_and_fuse(e))
                        all_atom &= atom_signs[name][i] 

        all_atom &= AstTypeHelper.fuse_check(node)

        # If all child nodes are atomic and the operation itself is good, then leave it to its parent
        if all_atom:
            return True

        # Rule 1: fuse consecutive atomic asssign statements in the body
        if hasattr(node, 'body'): 
            values = node.body
            signs = atom_signs['body']
            removed_num = 0
            for (st, leng) in get_consec_assign(values, signs):
                if not visualize_mode:
                    st -= removed_num
                    values[st] = fuse(values[st:st+leng])
                    # Already being fused
                    signs[st] = False
                    removed_num += leng - 1
                    del values[st+1:st+leng-1]
                    del signs[st+1:st+leng-1]    
                else:
                    fuse(values[st:st+leng])
                    for i in range(st, st+leng):
                        signs[i] = False

        for name, value in ast.iter_fields(node):
            if isinstance(value, ast.AST) and (atom_signs[name]):
                new_value = fuse(value)
                setattr(node, name, new_value)
            elif isinstance(value, list):
                new_values = []
                for i, e in enumerate(value):
                    if isinstance(e, ast.AST) and atom_signs[name][i]:
                        e = fuse(e)
                    new_values.append(e)
                value[:] = new_values
        return False

    if (iterate_and_fuse(node)):
        node = fuse(node)
    return node
