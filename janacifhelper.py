#!/usr/bin/env Python3
# -*- coding: utf-8 -*-
"""A program to provide some CIF items from standard JANA2006 output.

JANA CIF Helper

This program converts several parameters from JANA2006 into standardized CIF items for copying and pasting into the
 final CIF. Just drag-and-drop the *.ref or *.m41 on the script icon and a short CIF file with the additional items will
 be created.

Caveat: This program is not meant to be robust but to provide results quickly (and somewhat dirtily).
"""

import argparse
import datetime
import math
import os
import sys
import traceback
import CifFile

__author__ = 'Dennis Wiedemann'
__copyright__ = 'Copyright 2019, Dr. Dennis Wiedemann'
__credits__ = ['Dennis Wiedemann']
__license__ = 'MIT'
__version__ = '0.1.0'
__maintainer__ = 'Dennis Wiedemann'
__email__ = 'dennis.wiedemann@chem.tu-berlin.de'
__status__ = 'Development'

OUTPUT_FILE_ADDITION = '_add.cif'  # Extension of the output CIF file
BLOCK_NAME = 'global'              # Name of the CIF data block to store information in
PHASE_NUMBER = 1                   # Number of phase to put information out on
NUM_LEN = 9                        # Length of numbers (in characters) stored in *.m41


class Suppressor(object):
    """Suppress text output to `stdout`.
    """

    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, type, value, traceback):
        sys.stdout = self.stdout
        if type is not None:
            raise

    def write(self, x): pass


def ordinal(n):
    """Return an ordinal number representation for a given cardinal.

    :param n: cardinal number
    :type n: int
    :return: ordinal number
    :rtype: str
    """

    return '%d%s' % (n, 'tsnrhtdd'[(math.floor(n // 10) % 10 != 1) * (n % 10 < 4) * n % 10::4])


def iucr_string(values):
    """Convert a central value (average) and its s.u. into an IUCr compliant number representation.

    :param values: pair of central value (average) and s.u.
    :type values: tuple((float, float))
    :return: IUCr compliant representation
    :rtype: str
    """
    if values[1] == 0 or values[1] is None:  # No or zero s.u. given
        return str(values[0])

    sig_pos = math.floor(math.log10(abs(values[1])))  # position of first significant digit
    sig_3 = math.trunc(abs(values[1]) * 10 ** (2 - sig_pos)) / 10 ** (2 - sig_pos)  # 1st three significant s.u. digits
    sig_3 *= 10 ** -(sig_pos + 1)  # s.u. moved directly behind decimal separator (final range: 0.100-0.999)

    if sig_3 < 0.195:  # round to two digits (final s.u. range: 0.10-0.19)
        su = round(abs(values[1]), 1 - sig_pos)
        avg = round(values[0], 1 - sig_pos)
        sig_len = 2
    elif sig_3 < 0.950:  # round to one digit (final s.u. range: 0.2-0.9)
        su = round(abs(values[1]), -sig_pos)
        avg = round(values[0], -sig_pos)
        sig_len = 1
    else:  # round to two digits and move forward (final s.u.: 0.10)
        sig_pos += 1
        su = round(abs(values[1]), 1 - sig_pos)
        avg = round(values[0], 1 - sig_pos)
        sig_len = 2

    if sig_pos > 0:  # only integral part for s.u. >= 1.95
        sign_shift = -1 if values[0] < 0 else 0
        avg_str = ('{:' + str(sig_pos + sign_shift) + '.0f}').format(avg).strip()
        su_str = ('{:' + str(sig_pos) + '.0f}').format(su)
    else:  # fractional and possibly integral part for s.u. < 1.95
        avg_str = ('{:.' + str(-sig_pos + sig_len - 1) + 'f}').format(avg)
        su_str = '{:.0f}'.format(abs(su / 10 ** (sig_pos - sig_len + 1)))

    return '{:s}({:s})'.format(avg_str, su_str)


def nibble_numbers(input_line, count, length=NUM_LEN):
    """Return fixed-length numbers cut from the beginning of a string.

    :param input_line: line to nibble the numbers from
    :type input_line: str
    :param count: numbers of numbers to nibble
    :type count: int
    :param length: length of the nibbles
    :type length: int
    :return: numbers
    :rtype: list(floats)
    """
    numbers = []
    for i in range(0, count):
        numbers.append(float(input_line[i * length:(i + 1) * length]))
    return numbers


# Parse arguments
parser = argparse.ArgumentParser(description='Convert parameters from JANA2006 output into standardized CIF items.')
parser.add_argument('input', metavar='input file', type=argparse.FileType('rb'),
                    help='name of the input *.ref or *.m41 file')
parser.add_argument('-v', '--version', action='version', version=__version__)
args = parser.parse_args()

# Construct file names
name_stem = os.path.splitext(args.input.name)[0]
name_m41 = name_stem + '.m41'
name_ref = name_stem + '.ref'
name_cif = name_stem + OUTPUT_FILE_ADDITION

# Greeting
print("Hiiieee! My name is yours, what's JANA CIF Helper?\n")

# Scan for and read the values from *.m41
print('Reading from *.m41 ...', end='')
skipped = []
phase_select = []
select = {}
with open(name_m41, 'r') as read_file:

    # Read header values (selections)
    for line in read_file:
        if line.startswith('skipfrto'):
            skipped.append((line.split()[1], line.split()[2]))
        elif line.startswith('phase'):
            line = read_file.readline() + read_file.readline()
            phase_select.append(dict(zip(line.split()[::2], line.split()[1::2])))
        elif line.startswith('end'):
            break
        else:
            select.update(zip(line.split()[::2], line.split()[1::2]))
    print(select)

    # Read shift parameters
    while not line.startswith('# Shift'):
        line = read_file.readline()
    shift = dict(zip(['zero', 'sycos', 'sysin'], nibble_numbers(read_file.readline(), 3)))

    # Read background parameters
    while not line.startswith('# Background'):
        line = read_file.readline()
    background = []
    for i in range(0, math.trunc(int(select['bckgnum']) / 6)):
        background.append(nibble_numbers(read_file.readline(), 6))
    if (int(select['bckgnum']) % 6) != 0:
        background.append(nibble_numbers(read_file.readline(), int(select['bckgnum']) % 6))
    background = [item for sublist in background for item in sublist]

    # Read asymmetry parameters
    while not line.startswith('# Asymmetry'):
        line = read_file.readline()
    if select['asymm'] == '1':
        asymm = nibble_numbers(read_file.readline(), 1)[0]

    # Read profile parameters
    phase_count = 0
    profile = {}
    while not phase_count == PHASE_NUMBER:
        line = read_file.readline()
        while not line.startswith('### phase'):
            line = read_file.readline()
        phase_count += 1
    while not line.startswith('# Gaussian'):
        line = read_file.readline()
    for key, value in zip(['GU', 'GV', 'GW', 'GP'], nibble_numbers(read_file.readline(), 4)):
        profile[key] = value
    while not line.startswith('# Lorentzian'):
        line = read_file.readline()
    for key, value in zip(['LX', 'LXe', 'LY', 'LYe'], nibble_numbers(read_file.readline(), 4)):
        profile[key] = value

    # Read shift s.u.'s
    while not line.startswith('# Shift'):
        line = read_file.readline()
    shift_su = dict(zip(['zero', 'sycos', 'sysin'], nibble_numbers(read_file.readline(), 3)))

    # Read background s.u.'s
    while not line.startswith('# Background'):
        line = read_file.readline()
    background_su = []
    for i in range(0, math.trunc(int(select['bckgnum']) / 6)):
        background_su.append(nibble_numbers(read_file.readline(), 6))
    if (int(select['bckgnum']) % 6) != 0:
        background_su.append(nibble_numbers(read_file.readline(), int(select['bckgnum']) % 6))
    background_su = [item for sublist in background_su for item in sublist]

    # Read asymmetry s.u.'s
    while not line.startswith('# Asymmetry'):
        line = read_file.readline()
    if select['asymm'] == '1':
        asymm_su = nibble_numbers(read_file.readline(), 1)[0]

    # Read profile s.u.'s
    phase_count = 0
    profile_su = {}
    while not phase_count == PHASE_NUMBER:
        line = read_file.readline()
        while not line.startswith('### phase'):
            line = read_file.readline()
        phase_count += 1
    while not line.startswith('# Gaussian'):
        line = read_file.readline()
    for key, value in zip(['GU', 'GV', 'GW', 'GP'], nibble_numbers(read_file.readline(), 4)):
        profile_su[key] = value
    while not line.startswith('# Lorentzian'):
        line = read_file.readline()
    for key, value in zip(['LX', 'LXe', 'LY', 'LYe'], nibble_numbers(read_file.readline(), 4)):
        profile_su[key] = value

print(' Done.')

# Scan for and read the values from *.ref
print('Reading from *.ref ...', end='')
phase_count = 0
with open(name_ref, 'r') as read_file:
    for line in read_file:
        if line.startswith('Cycle  RFobs'):
            phase_count += 1
            if phase_count == PHASE_NUMBER:
                while line != '\n':
                    line_old = line
                    line = read_file.readline()
                rb_obs = float(line_old.split()[9])
print(' Done.')

# Construct CIF
print('Assembling CIF items ...', end='')
cif = CifFile.CifFile()
cif[BLOCK_NAME] = CifFile.CifBlock()
cif_block = cif[BLOCK_NAME]

# Set variables
cif.header_comment = ''

# Store introductory items
cif_block['_audit_conform_dict_name'] = ['cif_core.dic', 'cif_pd.dic']
cif_block['_audit_conform_dict_version'] = ['2.4.5', '1.0.1']
cif_block['_audit_conform_dict_location'] = ['ftp://ftp.iucr.org/pub/cif_core.dic', 'ftp://ftp.iucr.org/pub/cif_pd.dic']
cif_block.CreateLoop(['_audit_conform_dict_name', '_audit_conform_dict_version', '_audit_conform_dict_location'])
cif_block['_audit_creation_method'] = 'JANA CIF Helper v.' + __version__
cif_block['_audit_creation_date'] = datetime.datetime.now().strftime('%Y-%m-%d')

# Store extracted items
if select['absor'] == '1':
    cif_block['_exptl_absorpt_correction_type'] = 'cylinder'
    cif_block['_exptl_absorpt_process_details'] = '\ncorrection for a cylindrical sample with \\mR = ' + select['mir'] \
                                                  + ' as implemented in JANA2006 (Pet\\<r\\\'i\\<cek et al., 2014)'

cif_block['_refine_ls_R_I_factor'] = '{:2.4f}'.format(rb_obs / 100)

skipped_string = []
for region in skipped:
    skipped_string.append('from {:3.2f} to {:3.2f}\\%: '.format(float(region[0]), float(region[1])))
    cif_block['_pd_proc_info_excluded_regions'] = skipped_string
    cif_block.CreateLoop(['_pd_proc_info_excluded_regions'])

pd_proc_ls_special_details = '\n'
if shift['zero'] != '0.000000':
    pd_proc_ls_special_details = 'zero-point correction: ' + iucr_string((shift['zero'], shift_su['zero']))
cif_block['_pd_proc_ls_special_details'] = pd_proc_ls_special_details

_pd_proc_ls_profile_function = '\n'
if phase_select[PHASE_NUMBER - 1]['proffun'] == '3':
    _pd_proc_ls_profile_function += 'pseudo-Voigt profile according to Thompson, Cox & Hastings (1987): G~U~ = '
    _pd_proc_ls_profile_function += '0' if profile['GU'] == 0.0 else iucr_string((profile['GU'], profile_su['GU']))
    _pd_proc_ls_profile_function += ', G~V~ = '
    _pd_proc_ls_profile_function += '0' if profile['GV'] == 0.0 else iucr_string((profile['GV'], profile_su['GV']))
    _pd_proc_ls_profile_function += ', G~W~ = '
    _pd_proc_ls_profile_function += '0' if profile['GW'] == 0.0 else iucr_string((profile['GW'], profile_su['GW']))
    if profile['GP'] != 0.0:
        _pd_proc_ls_profile_function += ', G~P~ = ' + iucr_string((profile['GP'], profile_su['GP']))
    _pd_proc_ls_profile_function += ', L~X~ = '
    _pd_proc_ls_profile_function += '0' if profile['LX'] == 0.0 else iucr_string((profile['LX'], profile_su['LX']))
    _pd_proc_ls_profile_function += ', L~Y~ = '
    _pd_proc_ls_profile_function += '0' if profile['LY'] == 0.0 else iucr_string((profile['LY'], profile_su['LY']))
    if profile['LXe'] != 0.0:
        _pd_proc_ls_profile_function += ', L~Xe~ = ' + iucr_string((profile['LXe'], profile_su['LXe']))
    if profile['LYe'] != 0.0:
        _pd_proc_ls_profile_function += ', L~Ye~ = ' + iucr_string((profile['LYe'], profile_su['LYe']))

if select['asymm'] == '1':
    _pd_proc_ls_profile_function += ';\nasymmetry correction according to Howard (1982): P = ' \
                                   + iucr_string((asymm, asymm_su))
cif_block['_pd_proc_ls_profile_function'] = _pd_proc_ls_profile_function

_pd_proc_ls_background_function = '\n'
if select['manbckg'] == '1':
    _pd_proc_ls_background_function += 'manual background (visual estimation, unrefined)'
if select['manbckg'] == '1' and select['bckgtype'] == '1':
    _pd_proc_ls_background_function += ' interpolated by '
if select['bckgtype'] == '1':
    _pd_proc_ls_background_function += select['bckgnum'] + ' Legendre polynomials [1st: ' \
                                       + iucr_string((background[0], background_su[0]))
for i in range(2, int(select['bckgnum']) + 1):
    _pd_proc_ls_background_function += ', {:s}: '.format(ordinal(i)) \
                                       + iucr_string((background[i - 1], background_su[i - 1]))
_pd_proc_ls_background_function += ']'
cif_block['_pd_proc_ls_background_function'] = _pd_proc_ls_background_function
print(' Done.')

# Store static items
cif_block['_reflns_threshold_expression'] = 'I>3\\s(I)'
cif_block['_refine_ls_structure_factor_coef'] = 'Inet'
cif_block['_refine_ls_matrix_type'] = 'fullcycle'
cif_block['_refine_ls_weighting_details'] = 'w=1/[\\s^2^(I)+(0.01*I)^2^]'

# Output CIF
print('Writing to %s ...' % name_cif, end='')
with open(name_cif, 'w') as write_file, Suppressor():
    write_file.write(cif.WriteOut())
print(' Done.')

# Sendoff
print('\nYour makeup is NOT terrible. Byyyeee!')
