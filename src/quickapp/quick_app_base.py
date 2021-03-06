from abc import abstractmethod
from conf_tools.utils import indent
from contracts import contract, describe_value, ContractsMeta
from decent_params import DecentParams, UserError
from pprint import pformat
from .utils import HasLogger
from quickapp import logger
import logging
import os
import sys
import traceback
from quickapp.exceptions import QuickAppException
from decent_params.exceptions import DecentParamsUserError

__all__ = ['QuickAppBase']


class QuickAppBase(HasLogger):
    """
        class attributes used:
        
            cmd
            usage
            description (deprecated) => use docstring
            
    
    """
    __metaclass__ = ContractsMeta

    def __init__(self, parent=None):
        HasLogger.__init__(self)
        self.parent = parent
        
        logger_name = self.get_prog_name()
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        self.logger = logger
    
    @abstractmethod
    def define_program_options(self, params):
        """ Must be implemented by the subclass. """
        pass

    @abstractmethod
    @contract(returns='None|int')
    def go(self):
        """ 
            Must be implemented. This should return either None to mean success, 
            or an integer error code. 
        """
        pass
    
    @classmethod
    def get_sys_main(cls):
        """ Returns a function to be used as main function for a script. """
        from quickapp import quickapp_main
        return lambda: quickapp_main(cls, args=None, sys_exit=True)
    
    
    
    @classmethod
    def get_program_description(cls):
        """     
            Returns a description for the program. This is by default
            looked in the docstring or in the "description" attribute
            (deprecated).
        """
        if cls.__doc__ is not None:
            # use docstring
            docs = cls.__doc__
        else:
            docs = cls.__dict__.get('description', None)
        
        if docs is None:
            logger.warn('No description at all for %s' % cls) 
        
        return docs
    
    @classmethod
    def get_short_description(cls):
        longdesc = cls.get_program_description()
        if longdesc is None:
            return None
        return longdesc.strip()  # Todo: extract first sentence

    
    @classmethod
    def get_usage(cls):
        """     
            Returns an usage string for the program. The pattern ``%prog``
            will be substituted with the name of the program.
        """
        usage = cls.__dict__.get('usage', None)
        return usage
    
    @classmethod
    def get_epilog(cls):
        """     
            Returns the string used as an epilog in the help text. 
        """
        return None
    
    @classmethod
    def get_prog_name(cls):
        """     
            Returns the string used as the program name. By default
            it is contained in the ``cmd`` attribute. 
        """
        if not 'cmd' in cls.__dict__:
            return os.path.basename(sys.argv[0])
        else:    
            return cls.__dict__['cmd']
    
    
    def get_options(self):
        return self.options

    def set_parent(self, parent):
        self.parent = parent
        
    def get_parent(self):
        if self.parent is not None: 
            assert self.parent != self
        return self.parent
    
    @contract(args='None|list(str)', returns=int)
    def main(self, args=None, parent=None):
        """ Main entry point. Returns an integer as an error code. """ 
        
        if "short" in type(self).__dict__:
            msg = 'Class %s uses deprecated attribute "short".' % type(self)
            msg += ' Use "description" instead.'
            self.error(msg)
            
        # Create the parameters and set them using args
        self.parent = parent
        self.set_options_from_args(args)
        ret = self.go()
        if ret is None:
            ret = 0
        
        if isinstance(ret, int):
            return ret
        else:
            msg = 'Expected None or an integer fomr self.go(), got %s' % describe_value(ret)
            raise ValueError(msg)
        

    @contract(config='dict(str:*)')
    def set_options_from_dict(self, config):
        """
            Reads the configuration from a dictionary.
        
            raises: UserError: Wrong configuration, user's mistake.
                    Exception: all other exceptions
        """
        params = DecentParams()
        self.define_program_options(params)
        
        try:
            self.options = params.get_dpr_from_dict(config)
        except DecentParamsUserError as e:
            raise QuickAppException(str(e))
        except Exception as e:
            msg = 'Could not interpret:\n'
            msg += indent(pformat(config), '| ') 
            msg += 'according to params spec:\n'
            msg += indent(str(params), '| ') + '\n'
            msg += 'Error is:\n'
#             if isinstance(e, DecentParamsUserError):
#                 msg += indent(str(e), '> ')
#             else:
            msg += indent(traceback.format_exc(e), '> ')
            raise QuickAppException(msg)  # XXX class
         
 
    @contract(args='list(str)')
    def set_options_from_args(self, args):
        """
            Reads the configuration from command line arguments. 
            
            raises: UserError: Wrong configuration, user's mistake.
                    Exception: all other exceptions
        """
        cls = type(self)
        prog = cls.get_prog_name()
        params = DecentParams()
        self.define_program_options(params)
        
        try:
            usage = cls.get_usage()
            if usage:
                usage = usage.replace('%prog', prog)

            desc = cls.get_program_description()
            epilog = cls.get_epilog()
            self.options = \
                params.get_dpr_from_args(prog=prog, args=args, usage=usage,
                                         description=desc, epilog=epilog)
        except UserError:
            raise
        except Exception as e:
            msg = 'Could not interpret:\n'
            msg += ' args = %s\n' % args
            msg += 'according to params spec:\n'
            msg += indent(str(params), '| ') + '\n'
            msg += 'Error is:\n'
            msg += indent(traceback.format_exc(e), '> ')
            raise Exception(msg)  # XXX class
        
 
