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


def pyAAL(source, mode=0):
def to_dataframe(out):
    import pandas as pd
    d = [e.split('\t') for e in out if '\t' in e]
    columns = d[1]
    columns.append('')
    return pd.DataFrame(d[2:], columns=columns)


    assert(osp.isfile(source))
    filename, ext = osp.splitext(source)
    print ext
    workingDir = osp.split(source)[0]
    tpl_fp = '/home/grg/git/alfa/pyAAL/pyAAL.tpl'
    matlab_tpl = '/home/grg/denoising/matlab.tpl'

    modes = ['greg_list_dlabels', 'greg_list_plabels', 'greg_clusters_plabels']
    #0: Local Maxima Labeling - 1: Extended Local Maxima Labeling - 2: Cluster Labeling

    tags={ 'spm_mat_file': source,
            'mode':modes[mode]}

    template = parseTemplate(tags, tpl_fp)

    import tempfile
    code, tmpfile = tempfile.mkstemp(suffix='.m')
    print 'creating tempfile %s'%tmpfile
    createScript(tmpfile, template)

    tmpbase = osp.splitext(tmpfile)[0]
    tags={ 'script': tmpbase, 'workingDir': workingDir}
    cmd = parseTemplate(tags, matlab_tpl)
    print cmd

    import subprocess
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    # Returns the STATISTICS part of the output
    start = False
    res = []
    for each in out.split('\n'):
        if 'STATISTICS' in each:
            start = True
        if start:
            res.append(each)
    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
                    pyAAL: calls SPM/AAL on a given SPM.mat and collects the resulting clusters in a textfile.

                    Usage:
                    pyAAL -i SPM.mat --mode 1'''))

    parser.add_argument("-i", dest='input', type=str, help='Existing SPM.mat', required=True)
    parser.add_argument("--mode", type=int, help='0: Local Maxima Labeling - 1: Extended Local Maxima Labeling - 2: Cluster Labeling', required=False, default=0)
    parser.add_argument("-o", dest='output', type=str, help='Output textfile', required=False)

    args = parser.parse_args()
    source = args.input
    output = args.output
    mode = args.mode

    stats = pyAAL(source, mode)

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

