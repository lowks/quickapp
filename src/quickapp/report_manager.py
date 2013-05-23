from compmake import comp_store
from contracts import contract, describe_type, describe_value
from quickapp import logger
from reprep import Report
from reprep.report_utils import StoreResults
from reprep.utils import frozendict2, natsorted
import os
import time
from pprint import pformat

__all__ = ['ReportManager']


class ReportManager(object):
    
    def __init__(self, outdir, index_filename=None):
        self.outdir = outdir
        if index_filename is None:
            index_filename = os.path.join(self.outdir, 'report_index.html')
        self.index_filename = index_filename
        self.allreports = StoreResults()
        self.allreports_filename = StoreResults()

    @contract(report_type='str')
    def add(self, report, report_type, **kwargs):
        """
            Adds a report to the collection.
            
            
            report: Promise of a Report object
            report_type: A string that describes the "type" of the report
        
            kwargs:  str->str,int,float  parameters used for grouping
        """         
        if not isinstance(report_type, str):
            msg = 'Need a string for report_type, got %r.' % describe_value(report_type)
            raise ValueError(msg)
        
        from compmake import Promise
        if not isinstance(report, Promise):
            msg = ('ReportManager is mean to be given Promise objects, '
                   'which are the output of comp(). Obtained: %s' 
                   % describe_type(report))
            raise ValueError(msg)
        
        key = frozendict2(report=report_type, **kwargs)
        
        if key in self.allreports:
            msg = 'Already added report for %s' % key
            raise ValueError(msg)

        self.allreports[key] = report

        dirname = os.path.join(self.outdir, report_type)
        basename = "_".join(map(str, kwargs.values()))  # XXX
        basename = basename.replace('/', '_')  # XXX
        if '/' in basename:
            raise ValueError(basename)
        filename = os.path.join(dirname, basename) 
        self.allreports_filename[key] = filename + '.html'
        
    def create_index_job(self):
        if not self.allreports:
            # no reports necessary
            return
        
        from compmake import comp
        
        # Do not pass as argument, it will take lots of memory!
        # XXX FIXME: there should be a way to make this update or not
        # otherwise new reports do not appear
        if len(self.allreports_filename) > 100:
            allreports_filename = comp_store(self.allreports_filename, 'allfilenames')
        else:
            allreports_filename = self.allreports_filename
                    
        for key in self.allreports:
            job_report = self.allreports[key]
            filename = self.allreports_filename[key] 

            write_job_id = job_report.job_id + '-write'
            # comp_stage_job_id(job_report, 'write')
            
            comp(write_report_and_update,
                 job_report, filename, allreports_filename, self.index_filename,
                 write_pickle=True,
                 job_id=write_job_id)
             

def write_report_and_update(report, report_html, all_reports, index_filename,
                            write_pickle=False):
    if not isinstance(report, Report):
        msg = 'Expected Report, got %s.' % describe_type(report)
        raise ValueError(msg) 
    html = write_report(report, report_html, write_pickle=write_pickle)
    index_reports(reports=all_reports, index=index_filename, update=html)


@contract(report=Report, report_html='str')
def write_report(report, report_html, write_pickle=False): 
    from conf_tools.utils import friendly_path
    logger.debug('Writing to %r.' % friendly_path(report_html))
    if False:
        # Note here they might overwrite each other
        rd = os.path.join(os.path.dirname(report_html), 'images')
    else:
        rd = None
    report.to_html(report_html, write_pickle=write_pickle, resources_dir=rd)
    # TODO: save hdf format
    return report_html


@contract(reports=StoreResults, index=str)
def index_reports(reports, index, update=None):  # @UnusedVariable
    """
        Writes an index for the reports to the file given. 
        The special key "report" gives the report type.
        
        reports[dict(report=...,param1=..., param2=...) ] => filename
    """
    # print('Updating because of new report %s' % update)
    from compmake.utils import duration_human
    import numpy as np
    
    dirname = os.path.dirname(index)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    # logger.info('Writing on %s' % friendly_path(index))
    
    f = open(index, 'w')
    
    f.write("""
        <html>
        <head>
        <style type="text/css">
        span.when { float: right; }
        li { clear: both; }
        a.self { color: black; text-decoration: none; }
        </style>
        </head>
        <body>
    """)
    
    mtime = lambda x: os.path.getmtime(x)
    existing = filter(lambda x: os.path.exists(x[1]), reports.items())

 
    # create order statistics
    alltimes = np.array([mtime(b) for _, b in existing]) 
    
    def order(filename):
        """ returns between 0 and 1 the order statistics """
        assert os.path.exists(filename)
        histime = mtime(filename)
        compare = (alltimes < histime) 
        return np.mean(compare * 1.0)
        
    def style_order(order):
        if order > 0.95:
            return "color: green;"
        if order > 0.9:
            return "color: orange;"        
        if order < 0.5:
            return "color: gray;"
        return ""     
        
    @contract(k=dict, filename=str)
    def write_li(k, filename, element='li'):
        desc = ",  ".join('%s = %s' % (a, b) for a, b in k.items())
        href = os.path.relpath(filename, os.path.dirname(index))
        
        if os.path.exists(filename):
            when = duration_human(time.time() - mtime(filename))
            span_when = '<span class="when">%s ago</span>' % when
            style = style_order(order(filename))
            a = '<a href="%s">%s</a>' % (href, desc)
        else:
            # print('File %s does not exist yet' % filename)
            style = ""
            span_when = '<span class="when">missing</span>'
            a = '<a href="%s">%s</a>' % (href, desc)
        f.write('<%s style="%s">%s %s</%s>' % (element, style, a, span_when,
                                               element))

        
    # write the first 10
    existing.sort(key=lambda x: (-mtime(x[1])))
    nlast = min(len(existing), 10)
    last = existing[:nlast]
    f.write('<h2 id="last">Last %d reports</h2>\n' % (nlast))

    f.write('<ul>')
    for i in range(nlast):
        write_li(*last[i])
    f.write('</ul>')

    if False:
        for report_type, r in reports.groups_by_field_value('report'):
            f.write('<h2 id="%s">%s</h2>\n' % (report_type, report_type))
            f.write('<ul>')
            r = reports.select(report=report_type)
            items = list(r.items()) 
            items.sort(key=lambda x: str(x[0]))  # XXX use natsort   
            for k, filename in items:
                write_li(k, filename)
    
            f.write('</ul>')
    
    f.write('<h2>All reports</h2>\n')

    sections = make_sections(reports)
    
    if  sections['type'] == 'sample':
        # only one...
        sections = dict(type='division', field='raw',
                          division=dict(raw1=sections), common=dict())
        
        
    def write_sections(sections, parents):
        assert 'type' in sections
        assert sections['type'] == 'division', sections
        field = sections['field']
        division = sections['division']

        f.write('<ul>')
        sorted_values = natsorted(division.keys())
        for value in sorted_values:
            parents.append(value)
            html_id = "-".join(map(str, parents))            
            bottom = division[value]
            if bottom['type'] == 'sample':
                d = {field: value}
                if not bottom['key']:
                    write_li(k=d, filename=bottom['value'], element='li')
                else:
                    f.write('<li> <p id="%s"><a class="self" href="#%s">%s = %s</a></p>\n' 
                            % (html_id, html_id, field, value))
                    f.write('<ul>')
                    write_li(k=bottom['key'], filename=bottom['value'], element='li')
                    f.write('</ul>')
                    f.write('</li>')
            else:
                f.write('<li> <p id="%s"><a class="self" href="#%s">%s = %s</a></p>\n' 
                        % (html_id, html_id, field, value))

                write_sections(bottom, parents)
                f.write('</li>')
        f.write('</ul>') 
                
    write_sections(sections, parents=[])
    
    f.write('''
    
    </body>
    </html>
    
    ''')
    f.close()


def make_sections(allruns, common=None):
    # print allruns.keys()
    if common is None:
        common = {}
        
    # print('Selecting %d with %s' % (len(allruns), common))
        
    if len(allruns) == 1:
        key = allruns.keys()[0]
        value = allruns[key]
        return dict(type='sample', common=common, key=key, value=value)
    
    fields_size = [(field, len(list(allruns.groups_by_field_value(field))))
                    for field in allruns.field_names_in_all_keys()]
        
    # Now choose the one with the least choices
    fields_size.sort(key=lambda x: x[1])
    
    if not fields_size:
        # [frozendict({'i': 1, 'n': 3}), frozendict({'i': 2, 'n': 3}), frozendict({}), frozendict({'i': 0, 'n': 3})]
        msg = 'Not all records of the same type have the same fields'
        msg += pformat(allruns.keys())
        raise ValueError(msg)
        
    field = fields_size[0][0]
    division = {}
    for value, samples in allruns.groups_by_field_value(field):
        samples = samples.remove_field(field)   
        c = dict(common)
        c[field] = value
        division[value] = make_sections(samples, common=c)
        
    return dict(type='division', field=field,
                division=division, common=common)

    
    