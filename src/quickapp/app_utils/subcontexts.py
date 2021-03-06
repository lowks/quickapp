from contracts import contract
import os

__all__ = ['iterate_context_names', 'iterate_context_names_pair', 'iterate_context_names_triplet',
           'iterate_context_names_quartet']


def iterate_context_names(context, it1):
    """ Creates child contexts with minimal names. """
    # make strings
    if len(it1) == 0:
        raise ValueError('Empty iterator: %s' % it1)
    names = map(str, it1)
    # get nonambiguous and minimal at _,- boundaries
    _, names, _ = minimal_names_at_boundaries(names)
    # remove '-' and '_'
    names = map(good_context_name, names)
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

def iterate_context_names_triplet(context, it1, it2, it3):
    """
        Yields tuples of (context, s1, s2, s3).
    """
    for c1, x1 in iterate_context_names(context, it1):
        for c2, x2 in iterate_context_names(c1, it2):
            for c3, x3 in iterate_context_names(c2, it3):
                yield c3, x1, x2, x3

def iterate_context_names_quartet(context, it1, it2, it3, it4):
    """
        Yields tuples of (context, s1, s2, s3, s4).
    """
    for c1, x1 in iterate_context_names(context, it1):
        for c2, x2 in iterate_context_names(c1, it2):
            for c3, x3 in iterate_context_names(c2, it3):
                for c4, x4 in iterate_context_names(c3, it4):
                    yield c4, x1, x2, x3, x4

def iterate_context_names_quintuplet(context, it1, it2, it3, it4, it5):
    """
        Yields tuples of (context, s1, s2, s3, s4).
    """
    for c1, x1 in iterate_context_names(context, it1):
        for c2, x2 in iterate_context_names(c1, it2):
            for c3, x3 in iterate_context_names(c2, it3):
                for c4, x4 in iterate_context_names(c3, it4):
                    for c5, x5 in iterate_context_names(c4, it5):
                        yield c5, x1, x2, x3, x4, x5
                        
                        
@contract(id_object='str', returns='str')
def good_context_name(id_object):
    """ 
        Removes strange characters from a string to make it a good 
        context name. 
    """
    id_object = id_object.replace('-', '')
    id_object = id_object.replace('_', '')
    return id_object


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
    assert objects == objects2, (prefix, minimal, postfix)
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
        return x
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
    
    assert objects == objects2, (objects, objects2, (prefix, minimal, postfix))
    return prefix, minimal, postfix
    
    
    
    
    
    
