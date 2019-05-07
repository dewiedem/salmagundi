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

OUTPUT_FILENAME = 'JANA_CIF_Helper.cif'  # Name of the output CIF file
BLOCK_NAME = 'global'                    # Name of the CIF data block to store information in
PHASE_NUMBER = 1                         # Number of phase to put information out on


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
    sig_pos = math.floor(math.log10(abs(values[1])))  # position of first significant digit
    sig_3 = math.trunc(values[1] * 10 ** (2 - sig_pos)) / 10 ** (2 - sig_pos)  # first three significant digits of s.u.
    sig_3 *= 10 ** -(sig_pos + 1)  # s.u. moved directly behind decimal separator (final range: 0.100-0.999)

    if sig_3 < 0.195:  # round to two digits (final s.u. range: 0.10-0.19)
        su = round(values[1], 1 - sig_pos)
        avg = round(values[0], 1 - sig_pos)
        sig_len = 2
    elif sig_3 < 0.950:  # round to one digit (final s.u. range: 0.2-0.9)
        su = round(values[1], -sig_pos)
        avg = round(values[0], -sig_pos)
        sig_len = 1
    else:  # round to two digits and move forward (final s.u.: 0.10)
        su = 0.10
        avg = round(values[0], -1 - sig_pos)
        sig_len = 2

    if sig_pos > 0:  # only integral part for s.u. >= 1.95
        avg_str = ('{:' + str(sig_pos) + '.0f}').format(avg).strip()
        su_str = ('{:' + str(sig_pos) + '.0f}').format(abs(su))
    else:  # fractional and possibly integral part for s.u. < 1.95
        avg_str = ('{:.' + str(-sig_pos + sig_len - 1) + 'f}').format(avg)
        su_str = '{:.0f}'.format(abs(su / 10 ** (sig_pos - sig_len + 1)))
    return '{:s}({:s})'.format(avg_str, su_str)


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
name_cif = os.path.join(os.path.split(name_stem)[0], OUTPUT_FILENAME)

# Greeting
print("Hiiieee! My name is yours, what's JANA CIF Helper?\n")

# Scan for and read the values from *.m41
print('Reading from *.m41 ...', end='')
skipped = []
phase_select = []
with open(name_m41, 'r') as read_file:
    for line in read_file:
        if line.startswith('bckgtype'):
            select = dict(zip(line.split()[::2], line.split()[1::2]))
        elif line.startswith('absor'):
            select.update(zip(line.split()[::2], line.split()[1::2]))
        elif line.startswith('skipfrto'):
            skipped.append((line.split()[1], line.split()[2]))
        elif line.startswith('phase'):
            line = read_file.readline() + read_file.readline()
            phase_select.append(dict(zip(line.split()[::2], line.split()[1::2])))
        elif line.startswith('end'):
            break
    while not line.startswith('# Shift parameters'):
        line = read_file.readline()
    shift = dict(zip(['zero', 'sycos', 'sysin'], read_file.readline().split()[0:3]))  # TODO: not split, 9 numbers
    while not line.startswith('# Asymmetry'):
        line = read_file.readline()
    if select['asymm'] == '1':
        asymm = read_file.readline()[0:9]
print(select, phase_select, shift, asymm)
print(' Done.')

# Scan for and read the values from *.ref
print('Reading from *.ref ...', end='')
phase_count = 0
with open(name_ref, 'r') as read_file:
    for line in read_file:
        if line.startswith('Cycle  RFobs'):
            phase_count = +1
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
    cif_block['_exptl_absorpt_process_details'] = '\ncorrection for a cylindrical sample with \\mR = 0.041 as ' \
                                                  'implemented in JANA2006 (Pet\\<r\\\'i\\<cek et al., 2014)'

cif_block['_refine_ls_R_I_factor'] = '{:2.4f}'.format(rb_obs / 100)

skipped_string = []
for region in skipped:
    skipped_string.append('from {:3.2f} to {:3.2f}\\%: '.format(float(region[0]), float(region[1])))
    cif_block['_pd_proc_info_excluded_regions'] = skipped_string
    cif_block.CreateLoop(['_pd_proc_info_excluded_regions'])

pd_proc_ls_special_details = '\n'
if shift['zero'] != '0.000000':
    pd_proc_ls_special_details += 'zero-point correction: ' + shift['zero']
cif_block['_pd_proc_ls_special_details'] = pd_proc_ls_special_details

_pd_proc_ls_profile_function = '\n'
if phase_select[PHASE_NUMBER-1]['proffun'] == '3':
    _pd_proc_ls_profile_function += 'pseudo-Voigt profile according to Thompson, Cox & Hastings (1987): '
# pseudo-Voigt profile according to Thompson, Cox & Hastings (1987): G~U~ =, G~V~ =, G~W~ =, L~X~ =, L~Y~ = 0;
if select['asymm'] == '1':
    _pd_proc_ls_profile_function += ';\nasymmetry correction according to Howard (1982): P = ' + asymm  # TODO: value with esd
cif_block['_pd_proc_ls_profile_function'] = _pd_proc_ls_profile_function

_pd_proc_ls_background_function = '\n'
if select['manbckg'] == '1':
    _pd_proc_ls_background_function += 'manual background (visual estimation, unrefined)'
if select['manbckg'] == '1' and select['bckgtype'] == '1':
    _pd_proc_ls_background_function += ' interpolated by '
if select['bckgtype'] == '1':
    _pd_proc_ls_background_function += select['bckgnum'] + ' Legendre polynomials (1st: '
for i in range(2, int(select['bckgnum']) + 1):
    _pd_proc_ls_background_function += ', {:s}: '.format(ordinal(i)) + '0.00'  # TODO: actual values
_pd_proc_ls_background_function += ')'
cif_block['_pd_proc_ls_background_function'] = _pd_proc_ls_background_function
print(' Done.')

# Store static items
cif_block['_reflns_threshold_expression'] = 'I>3\\s(I)'
cif_block['_refine_ls_structure_factor_coef'] = 'Inet'
cif_block['_refine_ls_matrix_type'] = 'fullcycle'
cif_block['_refine_ls_weighting_details'] = 'w=1/[\\s^2^(I)+(0.01*I)^2^]'

# Output CIF
print('Writing to %s ...' % OUTPUT_FILENAME, end='')
with open(name_cif, 'w') as write_file, Suppressor():
    write_file.write(cif.WriteOut())
print(' Done.')

# Sendoff
print('\nYour makeup is NOT terrible. Byyyeee!')
