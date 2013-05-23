from contracts import contract
import os

__all__ = ['iterate_context_names', 'iterate_context_names_pair']


def iterate_context_names(context, it1):
    """ Creates child contexts with minimal names. """
    _, names, _ = minimal_names_at_boundaries(map(good_context_name, it1))
    for x, name in zip(it1, names):
        e_c = context.child(name)
        yield e_c, x

    
def iterate_context_names_pair(context, it1, it2):
    """
    
        Yields tuples of (context, s1, s2).
    """
    for cc, x1 in iterate_context_names(context, it1):
        for c, x2 in iterate_context_names(cc, it2):
            yield c, x1, x2


@contract(id_object='str', returns='str')
def good_context_name(id_object):
    """ 
        Removes strange characters from a string to make it a good 
        context name. 
    """
    return id_object.replace('-', '')


@contract(objects='seq[N](str)', returns='tuple(str, list[N](str), str)')
def minimal_names(objects):
    """
        Converts a list of object IDs to a minimal non-ambiguous list of names.
        
        For example, the names: ::
        
            test_learn_fast_10
            test_learn_slow_10
            test_learn_faster_10
            
        is converted to: ::
        
            fast
            slow
            faster
            
        Returns prefix, minimal, postfix
    """
    if len(objects) == 1:
        return '', objects, ''
    
    # find the common prefix
    prefix = os.path.commonprefix(objects)
    # invert strings
    objects_i = [o[::-1] for o in objects]
    # find postfix
    postfix = os.path.commonprefix(objects_i)[::-1]
    
    # print('prefix: %r post: %r' % (prefix, postfix))
    n1 = len(prefix)
    n2 = len(postfix)
    # remove it 
    minimal = [o[n1:-n2] for o in objects]
    
    # recreate them to check everything is ok
    objects2 = [prefix + m + postfix for m in minimal]
    
    # print objects, objects2
    assert objects == objects2
    return prefix, minimal, postfix
    
    

@contract(objects='seq[N](str)', returns='tuple(str, list[N](str), str)')
def minimal_names_at_boundaries(objects, separators=['_', '-']):
    """
        Converts a list of object IDs to a minimal non-ambiguous list of names.
       
        In this version, we only care about splitting at boundaries
        defined by separators.
        
        For example, the names: ::
        
            test_learn1_fast_10
            test_learn1_slow_10
            test_learn2_faster_10
            
        is converted to: ::
        
            learn1_fast
            learn2_slow
            learn2_faster
            
        Returns prefix, minimal, postfix
    """
    
    if len(objects) == 1:
        return '', objects, ''
    
    s0 = separators[0]
    
    # convert and split to uniform separators
    @contract(x='str', returns='str')
    def convert(x):
        for s in separators[1:]:
            x = x.replace(s, s0)
        return x
    
    objectsu = map(convert, objects)
    astokens = [x.split(s0) for x in objectsu]
    
    
    def is_valid_prefix(p):
        return all(x.startswith(p) for x in objectsu)
    
    def is_valid_postfix(p):
        return all(x.endswith(p) for x in objectsu)
    
    # max number of tokens
    ntokens = max(map(len, astokens))
    prefix = None
    for i in range(ntokens):
        toks = astokens[0][:i]
        p = "".join(t + s0 for t in toks) 
        if is_valid_prefix(p):
            prefix = p
        else:
            break
    assert prefix is not None
    
    postfix = None
    for i in range(ntokens):
        t0 = astokens[0]
        toks = t0[len(t0) - i:]
        x = "".join(s0 + t for t in toks)
        if is_valid_postfix(x):
            postfix = x
        else:
            break
    
    assert postfix is not None
        
    n1 = len(prefix)
    n2 = len(postfix)
    # remove it 
    minimal = [o[n1:len(o) - n2] for o in objectsu]
    
    # recreate them to check everything is ok
    objects2 = [prefix + m + postfix for m in minimal]
    
    assert objects == objects2
    return prefix, minimal, postfix
    
    
    
    
    
    