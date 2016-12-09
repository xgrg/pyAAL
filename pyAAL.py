#!/usr/bin/env python
from string import Template
import subprocess
import os.path as osp
import os

import argparse
import textwrap

def createScript(source, text):
    """Very not useful and way over simplistic method for creating a file

    Args:
        source: The absolute name of the script to create
        text: Text to write into the script

    Returns:
        True if the file have been created

    """
    try:
        with open(source, 'w') as f:
            f.write(text)
    except IOError:
        return False
    return True


def parseTemplate(dict, template):
    """provide simpler string substitutions as described in PEP 292

    Args:
       dict: dictionary-like object with keys that match the placeholders in the template
       template: object passed to the constructors template argument.

    Returns:
        the string substitute

    """
    with open(template, 'r') as f:
        return Template(f.read()).safe_substitute(dict)


def launchCommand(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=None, nice=0):
    import sys
    from lib import util
    """Execute a program in a new process

    Args:
	command: a string representing a unix command to execute
	stdout: this attribute is a file object that provides output from the child process
	stderr: this attribute is a file object that provides error from the child process
	timeout: Number of seconds before a process is consider inactive, usefull against deadlock
	nice: run cmd  with  an  adjusted  niceness, which affects process scheduling

    Returns
	return a 3 elements tuples representing the command execute, the standards output and the standard error message

    Raises
	OSError:      the function trying to execute a non-existent file.
	ValueError :  the command line is called with invalid arguments

    """
    binary = cmd.split(" ").pop(0)
    if util.which(binary) is None:
	print ("Command {} not found".format(binary))

    print ("Launch {} command line...".format(binary))
    print ("Command line submit: {}".format(cmd))

    (executedCmd, output, error)= util.launchCommand(cmd, stdout, stderr, timeout, nice)
    if not (output is "" or output is "None" or output is None):
	print("Output produce by {}: {} \n".format(binary, output))

    if not (error is '' or error is "None" or error is None):
	print("Error produce by {}: {}\n".format(binary, error))


def to_dataframe(out):
    import pandas as pd
    d = [e.split('\t') for e in out if '\t' in e]
    columns = d[1]
    columns.append('')
    return pd.DataFrame(d[2:], columns=columns)

def pyAAL(source, contrast, mode=0, verbose=True):

    assert(osp.isfile(source))
    filename, ext = osp.splitext(source)
    workingDir = osp.split(source)[0]
    tpl_fp = '/home/grg/git/alfa/pyAAL/pyAAL.tpl'
    matlab_tpl = '/home/grg/denoising/matlab.tpl'

    modes = ['greg_list_dlabels', 'greg_list_plabels', 'greg_clusters_plabels']
    #0: Local Maxima Labeling - 1: Extended Local Maxima Labeling - 2: Cluster Labeling

    tags={ 'spm_mat_file': source,
            'contrast': contrast,
            'mode':modes[mode]}

    template = parseTemplate(tags, tpl_fp)

    import tempfile
    code, tmpfile = tempfile.mkstemp(suffix='.m')
    if verbose:
        print 'creating tempfile %s'%tmpfile
    createScript(tmpfile, template)

    tmpbase = osp.splitext(tmpfile)[0]
    tags={ 'script': tmpbase, 'workingDir': workingDir}
    cmd = parseTemplate(tags, matlab_tpl)
    if verbose:
        print cmd

    import subprocess
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    # Returns the STATISTICS part
    start = False
    old = ''
    res = []
    for each in out.split('\n'):
        if old == 'CONTRAST':
            print 'Contrast:', each
        if 'STATISTICS' in each:
            start = True
        if start:
            res.append(each)
        old = each
    return res


def AAL_label(region_name, aaltxt = '/usr/local/MATLAB/R2014a/toolbox/spm12/toolbox/aal/ROI_MNI_V5.txt'):
    import string
    lines = [e.rstrip('\n') for e in open(aaltxt).readlines() if region_name in e]
    if len(lines) != 1:
        raise NameError('Region name returned a not-unique occurrence in %s: %s'%(aaltxt, lines))
    return string.atoi(lines[0].split('\t')[-1])

def AAL_name(region_label, aaltxt = '/usr/local/MATLAB/R2014a/toolbox/spm12/toolbox/aal/ROI_MNI_V5.txt'):
    lines = [e.rstrip('\n') for e in open(aaltxt).readlines() if e.split('\t')[-1] == '%s\n'%region_label]
    if len(lines) != 1:
        raise NameError('Region name returned a not-unique occurrence in %s: %s'%(aaltxt, lines))
    return lines[0].split('\t')[1]

def roi_mask(region_name, aalfp = '/usr/local/MATLAB/R2014a/toolbox/spm12/toolbox/aal/ROI_MNI_V5.nii'):
    from nilearn import image
    import numpy as np
    aal = image.load_img(aalfp)
    d = np.array(aal.dataobj)
    d[d!=AAL_label(region_name)] = 0
    return image.new_img_like(aal, d)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
                    pyAAL: calls SPM/AAL on a given SPM.mat and collects the resulting clusters in a textfile.

                    Usage:
                    pyAAL -i SPM.mat --mode 1'''))

    parser.add_argument("-i", dest='input', type=str, help='Existing SPM.mat', required=True)
    parser.add_argument("-c", dest='contrast', type=str, help='Index of the contrast of interest', required=True)
    parser.add_argument("--mode", type=int, help='0: Local Maxima Labeling - 1: Extended Local Maxima Labeling - 2: Cluster Labeling', required=False, default=0)
    parser.add_argument("-o", dest='output', type=str, help='Output textfile', required=False)

    args = parser.parse_args()
    spm_mat_file = args.input
    output = args.output
    contrast = args.contrast
    mode = args.mode

    stats = pyAAL(spm_mat_file, contrast, mode)

    # Writing the output (the part containing stats) in a file
    # or display on stdout

    if not args.output is None:
        f = open(output, 'w')
        for each in stats:
            f.write('%s\n'%each)
        f.close()
    else:
        for each in stats:
            print each

