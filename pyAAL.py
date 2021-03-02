#!/usr/bin/env python

import subprocess

# make sure /tmp is in the Matlab path
aal_nii = '/usr/local/MATLAB/R2019a/toolbox/spm12/toolbox/aal/ROI_MNI_V5.nii'
aal_txt = aal_nii.replace('.nii', '.txt')

matlab_cmd = 'matlab'


def parseTemplate(d, template):

    from string import Template
    with open(template, 'r') as f:
        return Template(f.read()).safe_substitute(d)


def launchCommand(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                  timeout=None, nice=0):
    """Execute a program in a new process

    Args:
        command: a string representing a unix command to execute
        stdout: a file object that provides output from the child process
        stderr: a file object that provides error from the child process
        timeout: Number of seconds before a process is consider inactive,
            useful against deadlock
        nice: run cmd with an adjusted niceness, which affects process
            scheduling

    Returns:
        return a 3 elements tuples representing the command execute, the
        standards output and the standard error message

    Raises:
        OSError:      the function trying to execute a non-existent file.
        ValueError :  the command line is called with invalid arguments"""

    from lib import util
    binary = cmd.split(' ').pop(0)
    if util.which(binary) is None:
        print('Command {} not found'.format(binary))

    print('Launch {} command line...'.format(binary))
    print('Command line submit: {}'.format(cmd))

    (executedCmd, output, error) = util.launchCommand(cmd, stdout, stderr,
                                                      timeout, nice)
    if not (output == '' or output == 'None' or output is None):
        print('Output produce by {}: {} \n'.format(binary, output))

    if not (error == '' or error == 'None' or error is None):
        print('Error produce by {}: {}\n'.format(binary, error))


def to_dataframe(out):
    import pandas as pd
    d = [e.split('\\t') for e in out if '\\t' in e]

    columns = d[1]
    columns.append('')
    return pd.DataFrame(d[2:], columns=columns)


def pyAAL(source, contrast, k=50, threshold=3.11, mode=0, verbose=True,
          aal_nii=aal_nii, matlab_cmd=matlab_cmd):
    '''`threshold` is a threshold on the spmT map.'''
    import subprocess
    import tempfile
    import os.path as op

    if not op.isfile(source):
        raise Exception('%s should be an existing file' % source)
    if not op.isfile(aal_nii):
        raise Exception('Please check path to AAL (%s not found)' % aal_nii)

    filename, ext = op.splitext(source)
    workingDir = op.split(source)[0]
    tpl_fp = op.join(op.split(__file__)[0], 'pyAAL.tpl')
    matlab_tpl = op.join(op.split(__file__)[0], 'matlab.tpl')

    modes = ['grg_list_dlabels', 'grg_list_plabels', 'grg_clusters_plabels']
    # 0: Local Maxima Labeling - 1: Extended Local Maxima Labeling
    # - 2: Cluster Labeling
    tags = {'aal_nii': aal_nii}
    grgf = op.join(op.split(__file__)[0], '%s.m' % modes[mode])
    template = parseTemplate(tags, grgf)

    fh, fp = tempfile.mkstemp(suffix='.m')
    w = open(fp, 'w')
    w.write(template)
    w.close()

    tags = {'spm_mat_file': source,
            'contrast': contrast,
            'mode': op.splitext(op.basename(fp))[0],
            'threshold': threshold,
            'k': k}

    template = parseTemplate(tags, tpl_fp)

    code, tmpfile = tempfile.mkstemp(suffix='.m')
    if verbose:
        print('creating tempfile %s' % tmpfile)

    with open(tmpfile, 'w') as f:
        f.write(template)

    tmpbase = op.splitext(tmpfile)[0]
    tags = {'matlab_cmd': matlab_cmd,
            'script': tmpbase,
            'workingDir': workingDir}
    cmd = parseTemplate(tags, matlab_tpl)
    if verbose:
        print(cmd)

    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    # Returns the STATISTICS part
    start = False
    old = ''
    res = []
    for each in str(out).split('\\n'):
        if old == 'CONTRAST':
            print(['Contrast:', each])
        if 'STATISTICS' in each:
            start = True
        if start:
            res.append(each)
        old = each

    if res == []:
        error = 'Command returned an empty result. Make sure `%s` is in '\
                'Matlab path.' % matlab_cmd
        print(err)
        raise Exception(error)
    return res


def AAL_label(region_name, aal_txt=aal_txt):
    import string
    lines = [e.rstrip('\n') for e in open(aal_txt).readlines()
             if region_name in e]
    if len(lines) != 1:
        msg = 'Region name returned a not-unique occurrence in %s: %s' \
              % (aal_txt, lines)
        raise NameError(msg)
    return string.atoi(lines[0].split('\t')[-1])


def AAL_name(region_label, aal_txt=aal_txt):
    lines = [e.rstrip('\n') for e in open(aal_txt).readlines()
             if e.split('\t')[-1] == '%s\n' % region_label]
    if len(lines) != 1:
        msg = 'Region name returned a not-unique occurrence in %s: %s' \
              % (aal_txt, lines)
        raise NameError(msg)
    return lines[0].split('\t')[1]


def roi_mask(region_name, aal_nii=aal_nii):
    from nilearn import image
    import numpy as np
    aal = image.load_img(aal_nii)
    d = np.array(aal.dataobj)
    d[d != AAL_label(region_name)] = 0
    return image.new_img_like(aal, d)


if __name__ == '__main__':
    import argparse
    import textwrap

    desc = 'pyAAL: calls SPM/AAL on a given SPM.mat and collects the '\
           'resulting clusters in a textfile.\n\n'\
           'Usage:\n'\
           'pyAAL -i SPM.mat --mode 1'

    rdhf = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=rdhf,
                                     description=textwrap.dedent(desc))

    parser.add_argument('-i', dest='input', type=str, help='Existing SPM.mat',
                        required=True)
    parser.add_argument('-c', dest='contrast', type=str, required=True,
                        help='Index of the contrast of interest')
    msg = '0: Local Maxima Labeling - 1: Extended Local Maxima Labeling - '\
          '2: Cluster Labeling'
    parser.add_argument('--mode', type=int, required=False, default=0,
                        help=msg)
    parser.add_argument('--aal_nii', type=str, required=False, default=aal_nii,
                        help='Path to AAL_MNI_V?.nii')
    parser.add_argument('--matlab', type=str, required=False, default=matlab_cmd,
                        help='Path to MATLAB command')
    parser.add_argument('-o', dest='output', type=str, help='Output textfile',
                        required=False)

    args = parser.parse_args()
    stats = pyAAL(args.input, args.contrast, args.mode, aal_nii=args.aal_nii,
                  matlab_cmd=args.matlab)

    # Writing the output (the part containing stats) in a file
    # or display on stdout

    if args.output is not None:
        f = open(args.output, 'w')
        for each in stats:
            f.write('%s\n' % each)
        f.close()
    else:
        for each in stats:
            print(to_dataframe(each))
