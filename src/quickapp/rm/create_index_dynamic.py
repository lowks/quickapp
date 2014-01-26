import os

from contracts import contract, describe_type
import yaml

from compmake.structures import Promise
from reprep import Report
from reprep.report_utils import StoreResults

from .configuration import get_rm_config, get_conftools_rm_reports


__all__ = ['create_job_index_dynamic', 'write_report_single']



@contract(report=Report)
def write_report_single(report, report_job_id, report_nid, report_html,
                                report_html_indexed, key, write_pickle=False):
    from quickapp.report_manager import write_report

    if not isinstance(report, Report):
        msg = 'Expected Report, got %s.' % describe_type(report)
        raise ValueError(msg)
    report.nid = report_nid
    html_filename = write_report(report, report_html, write_pickle=write_pickle)
    metadata_file = os.path.splitext(html_filename)[0] + '.rm_reports.yaml'

    rel_filename = os.path.relpath(os.path.realpath(report_html_indexed),
                                   os.path.dirname(os.path.realpath(metadata_file)))

    entry = dict(id=report_nid, desc='Automatically generated report',
                 code=['quickapp.rm.GeneratedReport',
                       {'key': dict(**key),
                        "file:filename": rel_filename,
                        'report_job_id': report_job_id}])

    with open(metadata_file, 'w') as f:
        f.write(yaml.dump([entry], default_flow_style=False))


def create_job_index_dynamic(context, dirname, index_filename, html_resources_prefix):
    """ Load the dynamically-generated reports """
    if not os.path.exists(dirname):
        print('Reports directory not found. You should rerun this job later.')
        return

    config = get_rm_config()
    config.load(dirname)

    reports = get_conftools_rm_reports()
    id_reports = reports.expand_names('*')
    print('Found reports: %s' % id_reports)

    allreports = StoreResults()
    allreports_filename = StoreResults()
    for id_report in id_reports:
        report = reports.instance(id_report)
        filename = report.filename
        key = report.key
        report_job_id = report.report_job_id
        allreports_filename[key] = filename
        allreports[key] = Promise(report_job_id)

    from quickapp.report_manager import create_write_jobs
    create_write_jobs(context,
                      allreports_filename,
                      allreports,
                      html_resources_prefix,
                      index_filename,
                      suffix='writedyn')


