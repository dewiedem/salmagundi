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


def rnd_sigfig(value, digits):
    """Round a value to a number of significant digits.

    :param value: value to be rounded
    :type value: float
    :param digits: number of significant digits to round to
    :type digits: int
    :return: float
    """

    return round(value, -int(math.floor(math.log10(abs(value))) - (digits - 1)))




def rnd_iucr(average, su):
    """Round a value according to IUCr rules.

    :param avg: average or central value
    :type avg: float
    :param su: standard uncertainty or error
    :type su: float
    :return: rounded value in short notation
    :rtype: str
    """

    pass


# Parse arguments
parser = argparse.ArgumentParser(description='Covert parameters from JANA2006 output into standardized CIF items.')
parser.add_argument('input', metavar='input file', type=argparse.FileType('rb'),
                    help='name of the input *.ref or *.m41 file')
parser.add_argument('-v', '--version', action='version', version=__version__)
args = parser.parse_args()

# Construct file names
file_stem = os.path.splitext(args.input.name)[0]
file_m41 = file_stem + '.m41'
file_ref = file_stem + '.ref'
file_cif = os.path.join(os.path.split(file_stem)[0], OUTPUT_FILENAME)

# Greeting
print("Hiiieee! My name is yours, what's JANA CIF Helper?\n")

# Scan for and read the values from *.m41
print('Reading from *.m41 ...', end='')
with open(file_m41, 'r') as read_file:
    pass
print(' Done.')

# Scan for and read the values from *.ref
print('Reading from *.ref ...', end='')
with open(file_ref, 'r') as read_file:
    pass
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
#_exptl_absorpt_coefficient_mu       0.009
#_pd_char_atten_coef_mu_calc         0.0082
#_exptl_absorpt_correction_type      cylinder
#_exptl_absorpt_process_details
#;
#correction for a cylindrical sample with \mR = 0.041 as implemented in
# JANA2006 (Pet\<r\'i\<cek et al., 2014)
#;
#_refine_ls_R_I_factor               ?
#loop_
#_pd_proc_info_excluded_regions
# 'from 0.05 to 7.50: irregular onset'
# 'from 158.0 to 160.11: cut-off refelection'
#_pd_proc_ls_special_details
#;
#zero - point
#correction:
#;
#_pd_proc_ls_profile_function
#;
#pseudo - Voigt
#profile in TCH
#approach(Thompson
#et
#al., 1987):
#G
#~U
#~ =, G
#~V
#~ =, G
#~W
#~ =, L
#~X
#~ =, L
#~Y
#~ = 0;
#asymmetry
#correction
#according
#to
#Howard(1982):
#P =
#;

#_pd_proc_ls_background_function
#;
#manual
#background(visual
#estimation, unrefined) interpolated
#by
#ten
#Legendre
#polynomials(1
#st:, 2
#nd:, 3
#rd:, 4
#th:, 5
#th: )
#;
print(' Done.')

# Store static items
cif_block['_reflns_threshold_expression'] = 'I>3\\s(I)'
cif_block['_refine_ls_structure_factor_coef'] = 'Inet'
cif_block['_refine_ls_matrix_type'] = 'full'
cif_block['_refine_ls_weighting_details'] = 'w=1/[\\s^2^(F~o~)+(0.01F~o~)^2^]'  # TODO: wrong!

# Output CIF
print('Writing to %s ...' % OUTPUT_FILENAME, end='')
with open(file_cif, 'w') as write_file, Suppressor():
    write_file.write(cif.WriteOut())
print(' Done.')

# Sendoff
print('\nYour makeup is NOT terrible. Byyyeee!')
