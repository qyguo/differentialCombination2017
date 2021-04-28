import os, re, random, copy, glob, sys
from os.path import *
from datetime import datetime
import traceback
import subprocess

import logging
import logger
logger.set_basic_format()

import differentials
import ROOT

from time import strftime
GLOBAL_DATESTR = strftime( '%b%d' )

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __deepcopy__(self, memo):
        d = copy.deepcopy({ key : getattr(self, key) for key in self.keys() })
        return AttrDict(**d)

    @staticmethod
    def create_tree(*args):
        base = AttrDict()
        terminal_nodes = [base]
        for branches in args:
            new_terminal_nodes = []
            for node in terminal_nodes:
                for branch in branches:
                    setattr(node, branch, AttrDict())
                    new_terminal_nodes.append(getattr(node, branch))
            terminal_nodes = new_terminal_nodes
        return base

def fast_duplicate_removal(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def deprecated(fn):
    def decorated(*args):
        caller = get_caller()
        logging.warning(
            'Deprecated call to {0}: made by {1}:{2}:{3}'
            .format(fn.__name__, caller.module, caller.function, caller.line)
            )
        return fn(*args)
    return decorated

def get_POIs_oldstyle_scandir(scandir):
    root_files = glob.glob(join(scandir, '*.root'))
    POIs = []
    for root_file in root_files:
        POI = basename(root_file).split('_')[1:6]
        try:
            differentials.core.str_to_float(POI[-1])
        except ValueError:
            POI = POI[:-1]
        POI = '_'.join(POI)
        POIs.append(POI)
    POIs = list(set(POIs))
    POIs.sort(key=differentials.core.range_sorter)
    logging.info('Retrieved following POIs from oldstyle {0}:\n{1}'.format(scandir, POIs))
    return POIs


def datestr():
    return GLOBAL_DATESTR

def get_caller():
    stack = traceback.extract_stack(None, 3)
    stack = stack[0]
    linenumber = stack[1]
    funcname = stack[2]
    cwd = abspath(os.getcwd())
    modulefilename = relpath(stack[0], cwd)
    return AttrDict(module=modulefilename, function=funcname, line=linenumber)

def gittag():
    caller = get_caller()
    datestr_detailed = strftime('%y-%m-%d %H:%M:%S')
    currentcommit = execute(['git', 'log', '-1', '--oneline' ], py_capture_output=True)
    ret = 'Generated on {0} by {1}; current git commit: {2}'.format(datestr_detailed, caller.module, currentcommit.replace('\n',''))
    return ret

TESTMODE = False
def testmode(flag=True):
    global TESTMODE
    TESTMODE = flag
    logger.enable_testmode()
    logging.info('Test mode enabled')

def is_testmode():
    global TESTMODE
    return TESTMODE


def save_root():
    differentials.plotting.canvas.Canvas.save_root = True

def save_png():
    differentials.plotting.canvas.Canvas.save_png = True

def save_png_through_convert():
    differentials.plotting.canvas.Canvas.save_png_through_convert = True

def save_gray():
    differentials.plotting.canvas.Canvas.save_gray = True

# Colors picked to be projector safe and reasonably distinguishable in grayscale
safe_colors = AttrDict(
    black = 1,
    red = 628,
    blue = 601,
    green = 419,
    lightblue = 851,
    )

standard_titles = {
    'hgg' : 'H #rightarrow #gamma#gamma',
    'hzz' : 'H #rightarrow ZZ',
    'combination' : 'Combination',
    'hbb' : 'H #rightarrow bb',
    # 'combWithHbb' : 'Comb. with H#rightarrowbb',
    'combWithHbb' : 'Combination',
    #
    'kappac' : '#kappa_{c}',
    'kappab' : '#kappa_{b}',
    'kappat' : '#kappa_{t}',
    'ct' : '#kappa_{t}',
    'cg' : 'c_{g}',
    'cb' : '#kappa_{b}',
    #
    'pth'  : 'p_{T}^{H}',
    'pth_smH'  : 'p_{T}^{H}',
    'pth_ggH'  : 'p_{T}^{H (ggH)}',
    'njets'    : 'N_{jets}',
    'ptjet'    : 'p_{T}^{jet}',
    'rapidity' : '|y_{H}|',
    #
    'diff_pth' : '#Delta#sigma/#Deltap_{T}^{H} (pb/GeV)',
    'unc_pth' : 'Unc. #Delta#sigma/#Deltap_{T}^{H} (%)',
    #
    # 'SM_Vittorio'       : 'ggH aMC@NLO, NNLOPS + HX',
    'SM_Vittorio'       : 'aMC@NLO, NNLOPS',
    'dnll' : '-2#Delta ln L',
    #
    'BR' : '#bf{#it{#Beta}}',
    # 'BR' : '#mathcal{B}',
    }


standard_titles_latex = {
    'hgg'         : '$\\hboson \\rightarrow \\photon\\photon$',
    'hzz'         : '$\\hboson \\rightarrow \\zboson\\zboson$',
    'combination' : 'Combination',
    'hbb'         : '$\\hboson \\rightarrow \\bquark\\bquark$',
    'combWithHbb' : 'Combination',
    #
    'pth_smH'  : '$\\pth$',
    'pth_ggH'  : '$\\pth$',
    'njets'    : '$\\njets$',
    'ptjet'    : '$\\ptjet$',
    'rapidity' : '$\\absy$',
    }

def get_standard_title(name):
    return standard_titles.get(name, name)

def execute(cmd, capture_output=False, ignore_testmode=False, py_capture_output=False):
    # Allow both lists and strings to be passed as the cmd
    if not isinstance(cmd, basestring):
        cmd = [ l for l in cmd if not len(l.strip()) == 0 ]
        cmd_str = '\n    '.join( cmd )
        cmd_exec = ' '.join(cmd)
    else:
        cmd_str = cmd
        cmd_exec = cmd

    logging.info('Executing the following command:\n{0}'.format(cmd_str))
    logging.trace('Actual passed command: {0}'.format(cmd_exec))
    if not(is_testmode()) and not(ignore_testmode):
        if py_capture_output:
            return subprocess.check_output(cmd_exec, shell=True)
        elif capture_output:
            with RedirectStdout() as redirected:
                os.system(cmd_exec)
                output = redirected.read()
            return output
        else:
            os.system(cmd_exec)


def get_axis(n_points, x_min, x_max):
    dx = (x_max-x_min)/float(n_points-1)
    return [ x_min + i*dx for i in xrange(n_points) ]


def float_to_str(number, nDecimals=None):
    number = float(number)
    if not nDecimals is None:
        string = '{:.{nDecimals}f}'.format(number, nDecimals=nDecimals).replace('-','m').replace('.','p')
        return string
    if number.is_integer():
        number = int(number)
    string = str(number).replace('-','m').replace('.','p')
    return string

def str_to_float(string):
    string = str(string)
    number = string.replace('m','-').replace('p','.')
    number = float(number)

    return number


def __uniqueid__():
    mynow=datetime.now
    sft=datetime.strftime
    # store old datetime each time in order to check if we generate during same microsecond (glucky wallet !)
    # or if daylight savings event occurs (when clocks are adjusted backward) [rarely detected at this level]
    old_time=mynow() # fake init - on very speed machine it could increase your seed to seed + 1... but we have our contingency :)
    # manage seed
    seed_range_bits=14 # max range for seed
    seed_max_value=2**seed_range_bits - 1 # seed could not exceed 2**nbbits - 1
    # get random seed
    seed=random.getrandbits(seed_range_bits)
    current_seed=str(seed)
    # producing new ids
    while True:
        # get current time
        current_time=mynow()
        if current_time <= old_time:
            # previous id generated in the same microsecond or Daylight saving time event occurs (when clocks are adjusted backward)
            seed = max(1,(seed + 1) % seed_max_value)
            current_seed=str(seed)
        # generate new id (concatenate seed and timestamp as numbers)
        #newid=hex(int(''.join([sft(current_time,'%f%S%M%H%d%m%Y'),current_seed])))[2:-1]
        newid=int(''.join([sft(current_time,'%f%S%M%H%d%m%Y'),current_seed]))
        # save current time
        old_time=current_time
        # return a new id
        yield newid

class openroot():
    """Context manager to safely open and close root files"""
    def __init__(self, root_file):
        self._root_file = root_file

    def __enter__(self):
        if not isfile(self._root_file):
            raise IOError('File {0} does not exist'.format(self._root_file))
        self._root_fp = ROOT.TFile.Open(self._root_file)
        return self._root_fp

    def __exit__(self, *args):
        self._root_fp.Close()


def list_POIs(root_file, only_r_=True):
    with openroot(root_file) as root_fp:
        POI_list = ROOT.RooArgList(root_fp.Get('w').set('POI'))

    par_names = []
    for i in xrange(POI_list.getSize()):
        par_name = POI_list[i].GetName()
        if only_r_:
            if par_name.startswith('r_'):
                par_names.append(par_name)
            else:
                continue
        else:
            par_names.append(par_name)
    return par_names


def get_ws(root_file, wsname = 'w'):
    with openroot(root_file) as root_fp:
        w = root_fp.Get(wsname)
    if w == None:
        raise ValueError('Workspace \'{0}\' does not exist in {1}'.format(wsname, root_file))
    return w

def read_set(root_file, setname, return_names=True):
    if isinstance(root_file, ROOT.RooWorkspace):
        w = root_file
    else:
        w = get_ws(root_file)
    if not set_exists(w, setname):
        return []
    argset = w.set(setname)
    arglist = ROOT.RooArgList(argset)

    names = []
    objs = []
    for i in xrange(arglist.getSize()):
        obj = arglist[i]
        obj_name = obj.GetName()
        names.append(obj_name)
        objs.append(obj)
    logging.debug('Found the following object names in set {0}: {1}'.format(setname, names))

    if return_names:
        return names
    else:
        return objs

def set_exists(root_file, setname):
    if isinstance(root_file, ROOT.RooWorkspace):
        w = root_file
    else:
        w = get_ws(root_file)
    s = w.set(setname)
    if s == None:
        logging.info('Set {0} does not exist in {1}'.format(setname, root_file))
        return False
    else:
        return True

def read_data(f, sep=' ', columns=False, make_float=False):
    with open(f, 'r') as fp:
        text = fp.read()

    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('#') or len(line) == 0: continue
        components = line.split(sep) if not sep == ' ' else line.split()
        if make_float:
            components = [float(c) for c in components]
        lines.append(components)

    if columns:
        n_cols = len(lines[0])
        logging.debug('Determined {0} columns from the following line: {1}'.format(n_cols, lines[0]))
        cols = []
        for i_col in xrange(n_cols):
            col = []
            for line in lines:
                try:
                    col.append(line[i_col])
                except IndexError:
                    logging.error('Problem with i_col={0}, line {1}'.format(i_col, line))
                    raise
            cols.append(col)
        return cols

    return lines

def fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd

class RedirectStdout():
    """Context manager to capture stdout from ROOT/C++ prints"""
    def __init__( self, verbose=False ):
        self.stdout_fd = fileno(sys.stdout)
        self.enableDebugPrint = verbose
        self._is_redirected = False
        pass

    def __enter__( self ):
        self.debug_redirected_logging('Entering RedirectStdout')
        self.captured_fd_r, self.captured_fd_w = os.pipe()
        self.debug_redirected_logging('Opened read: {0}, and write: {1}'.format( self.captured_fd_r, self.captured_fd_w ))

        self.debug_redirected_logging('  Copying stdout')
        self.copied_stdout = os.fdopen( os.dup(self.stdout_fd), 'wb' )
        sys.stdout.flush() # To flush library buffers that dup2 knows nothing about

        # Overwrite stdout_fd with the target
        self.debug_redirected_logging('Overwriting target ({0}) with stdout_fd ({1})'.format(fileno(self.captured_fd_w), self.stdout_fd))
        os.dup2(fileno(self.captured_fd_w), self.stdout_fd)
        self._is_redirected = True

        os.close( self.captured_fd_w )
        return self

    def __exit__(self, *args):
        sys.stdout.flush()
        os.dup2( self.copied_stdout.fileno(), self.stdout_fd )  # $ exec >&copied

    def read( self ):
        sys.stdout.flush()
        self.debug_redirected_logging('  Draining pipe')

        # Without this line the reading does not end - is that 'deadlock'?
        os.close(self.stdout_fd)

        captured_str = ''
        while True:
            data = os.read( self.captured_fd_r, 1024)
            if not data:
                break
            captured_str += data
            self.debug_redirected_logging('\n  captured_str: ' + captured_str)

        self.debug_redirected_logging('  Draining completed')
        return captured_str

    def debug_redirected_logging( self, text ):
        if self.enableDebugPrint:
            text = '[Redirected debug] ' + text
            if self._is_redirected:
                os.write(fileno(self.copied_stdout), text + '\n')
            else:
                os.write(fileno(self.stdout_fd), text + '\n')



class enterdirectory():
    """Context manager to (create and) go into and out of a directory"""

    def __init__(self, subdirectory=None, verbose=True):
        self.verbose = verbose
        self._active = False
        if not subdirectory is None and not subdirectory == '':
            self._active = True
            self.backdir = os.getcwd()
            self.subdirectory = subdirectory

    def __enter__(self):
        if self._active:
            logging.info('Would now create/go into \'{0}\''.format(self.subdirectory))
            if not isdir( self.subdirectory ):
                logging.info('Creating \'{0}\''.format(relpath(self.subdirectory, self.backdir)))
                if not is_testmode(): os.makedirs( self.subdirectory )
            logging.info('Entering \'{0}\''.format(relpath(self.subdirectory, self.backdir)))
            if not is_testmode(): os.chdir(self.subdirectory)
        return self

    def __exit__(self, *args):
        if self._active:
            os.chdir(self.backdir)


def make_unique_directory(dirname, n_attempts = 100):
    dirname = abspath(dirname)
    if not isdir(dirname):
        return dirname

    dirname += '_{0}'
    for iAttempt in xrange(n_attempts):
        if not isdir( dirname.format(iAttempt) ):
            dirname = dirname.format(iAttempt)
            break
    else:
        raise RuntimeError('Could not create a unique directory for {0}'.format(dirname.format('X')))

    logging.info('Uniquified directory: {0}'.format(dirname))
    return dirname

def make_unique_filename(filename, n_attempts = 1000):
    filename = abspath(filename)
    if not isfile(filename):
        return filename

    filebase, extension = os.path.splitext(filename)
    filename = '{0}_{{0}}{1}'.format(filebase, extension)
    for iAttempt in xrange(n_attempts):
        if not isfile( filename.format(iAttempt) ):
            filename = filename.format(iAttempt)
            break
    else:
        raise RuntimeError('Could not create a unique directory for {0}'.format(filename.format('X')))

    logging.info('Uniquified filename: {0}'.format(filename))
    return filename


class raise_logging_level():
    """Context manager to temporarily raise the logging level"""
    raise_map = {
        logging.TRACE : logging.DEBUG,
        logging.DEBUG : logging.INFO,
        logging.INFO  : logging.WARNING,
        logging.WARNING : logging.ERROR,
        logging.ERROR : logging.ERROR
        }

    def __init__(self):
        self.old_level = logging.getLogger().getEffectiveLevel()
        self.new_level = self.raise_map[self.old_level]

    def __enter__(self):
        # logging.warning('Temporarily raising logging level to {0}'.format(self.new_level))
        logging.getLogger().setLevel(self.new_level)

    def __exit__(self, *args):
        # logging.info('Setting logging level back to {0}'.format(self.old_level))
        logging.getLogger().setLevel(self.old_level)


# ======================================
# To be replaced by tools in proccesinterpreter.py

# @deprecated
def get_range_from_str(text):
    regular_match = re.search(r'([\dpm\.\-]+)_([\dpm\.\-]+)', text)
    overflow_match = re.search(r'(GE|GT)([\dpm\.\-]+)', text)
    underflow_match = re.search(r'(LE|LT)([\dpm\.\-]+)', text)
    single_match = re.search(r'_([\dpm\.\-]+)', text)

    if regular_match:
        left = str_to_float(regular_match.group(1))
        right = str_to_float(regular_match.group(2))
    elif overflow_match:
        left = str_to_float(overflow_match.group(2))
        right = 'INF'
    elif underflow_match:
        left = '-INF'
        right = str_to_float(underflow_match.group(2))
    elif single_match:
        logging.debug('single_match for {0}; matched text is {1}'.format(text, single_match.group(1)))
        left = str_to_float(single_match.group(1))
        right = 'SINGLE'
    else:
        left = 'UNDEFINED'
        right = 'UNDEFINED'

    return left, right

# @deprecated
def range_sorter(text):
    left, right = get_range_from_str(text)
    if left == 'UNDEFINED':
        return 900000
    elif right == 'SINGLE':
        return left
    elif right == 'INF':
        return 800000
    elif left == '-INF':
        return -800000
    else:
        return left

# @deprecated
def last_bin_is_overflow(POIs):
    """Checks if the last bin is an overflow bin. Assumes POIs are pre-sorted"""
    left, right = get_range_from_str(POIs[-1])
    is_overflow = False
    if right == 'INF':
        is_overflow = True
    logging.debug('Checking if POI \'{0}\' is overflow: found right {1}; overflow={2}'.format(POIs[-1], right, is_overflow))
    return is_overflow

# @deprecated
def first_bin_is_underflow(POIs):
    """Checks if the first bin is an underflow bin. Assumes POIs are pre-sorted"""
    print("POIs: ",POIs)
    left, right = get_range_from_str(POIs[0])
    if left == '-INF':
        return True
    return False

# @deprecated
def binning_from_POIs(POIs_original):
    POIs = copy.copy(POIs_original)
    POIs.sort(key=range_sorter)
    logging.debug(
        'Determining bin boundaries of the following (sorted) POIs:\n    '
        + '\n    '.join(POIs)
        )
    is_underflow = first_bin_is_underflow(POIs)
    is_overflow  = last_bin_is_overflow(POIs)
    binning = []
    if is_underflow:
        POIs = POIs[1:]
        binning.append(-10000)
    for POI in POIs:
        left, right = get_range_from_str(POI)
        binning.append(left)
    if is_overflow:
        binning.append(10000)
    else:
        binning.append(right)
    logging.debug('Determined the following binning: {0}'.format(binning))
    return binning


def get_closest_match(x_val, x_list):
    x_match = 10e9
    mindx = 10e9
    minix = -10e9
    found_atleast_one = False
    for ix, x in enumerate(x_list):
        dx = abs(x-x_val)
        if dx < mindx:
            found_atleast_one = True
            mindx = dx
            x_match = x
            minix = ix
    return x_match, minix


def print_progress_bar(iteration, total, prefix = 'Progress', suffix = 'Complete', decimals = 1, length = 55, fill = '#'):
    """
    from: https://stackoverflow.com/a/34325723/9209944
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print '\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix),
    # Print New Line on Complete
    if iteration == total:
        print

