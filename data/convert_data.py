# Copyright 2017, Wenjia Bai. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""
    The data converting script for UK Biobank Application 2964, which contributes
    the manual annotations of 5,000 subjects.

    This script assumes that the images and annotations have already been downloaded
    as zip files. It decompresses the zip files, sort the DICOM files into subdirectories
    according to the information provided in the manifest.csv spreadsheet, parse manual
    annotated contours from the cvi42 xml files, read the matching DICOM and cvi42 contours
    and finally save them as nifti images.
    """
import os
import sys
import shutil
import csv
import glob
import re
import time
import pandas as pd
import dateutil.parser
from biobank_utils import *
import parse_cvi42_xml


if __name__ == '__main__':

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f'Usage: {sys.argv[0]} <data_dir> [<output_dir>]', file=sys.stderr)
        exit(-1)
    
    # data_path is the path to the ukbb data
    # structure of input data dir
    # <data_dir>/
    #      |
    #      +--<subject_id1>/
    #      |       |
    #      |       +--<subject_id1>_cvi42.zip
    #      |       +--<subject_id1>_long.zip
    #      |       +--<subject_id1>_short.zip
    #      |
    #      +--<subject_id2>/
    #      |       |
    #      |       +--<subject_id2>_cvi42.zip
    #      |       +--<subject_id2>_long.zip
    #      |       +--<subject_id2>_short.zip
    #     ...    
    # -----------------------------------------
    # structure of output dir
    # <output_dir>/
    #      |
    #      +--<subject_id1>/
    #      |       |
    #      |       +--la_2ch.nii.gz
    #      |       +--la_3ch.nii.gz
    #      |       +--la_4ch.nii.gz
    #      |       +--sa.nii.gz
    #      |       +--label_*.nii.gz (optional)
    #      |
    #      +--<subject_id2>/
    #      |       |
    #     ...
    data_path = sys.argv[1]
    # remove trailing slash if any
    if data_path.endswith('/'):
        data_path = data_path[:-1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else f'{data_path}.converted'

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # For each subject in the subdirectory
    for eid in sorted(os.listdir(data_path)):
        data_dir = os.path.join(data_path, eid)
        if not os.path.isdir(data_dir):
            continue    # skip non-directory files
        print(f'converting {eid}...', end='', flush=True)
        sub_output_dir = os.path.join(output_dir, eid)
        if not os.path.exists(sub_output_dir):
            os.mkdir(sub_output_dir)
        # Decompress the zip files in this directory
        files = glob.glob('{0}/{1}_*.zip'.format(data_dir, eid))
        dicom_dir = os.path.join(data_dir, 'dicom')
        if not os.path.exists(dicom_dir):
            os.mkdir(dicom_dir)

        for f in files:
            if os.path.basename(f) == '{0}_cvi42.zip'.format(eid):
                os.system('unzip -q -o {0} -d {1}'.format(f, data_dir))
            else:
                os.system('unzip -q -o {0} -d {1}'.format(f, dicom_dir))

                # Process the manifest file
                process_manifest(os.path.join(dicom_dir, 'manifest.csv'),
                                    os.path.join(dicom_dir, 'manifest2.csv'))
                df2 = pd.read_csv(os.path.join(dicom_dir, 'manifest2.csv'), error_bad_lines=False)

                # Organise the dicom files
                # Group the files into subdirectories for each imaging series
                for series_name, series_df in df2.groupby('series discription'):
                    series_dir = os.path.join(dicom_dir, series_name)
                    if not os.path.exists(series_dir):
                        os.mkdir(series_dir)
                    series_files = [os.path.join(dicom_dir, x) for x in series_df['filename']]
                    os.system('mv {0} {1}'.format(' '.join(series_files), series_dir))

        cvi42_contours_dir = None
        xml_name = os.path.join(data_dir, f'{eid}.cvi42wsx')
        json_name = os.path.join(data_dir, f'{eid}.json')
        txt_name = os.path.join(data_dir, f'{eid}.txt')
        if os.path.exists(xml_name):
            # Parse cvi42 xml file
            cvi42_contours_dir = os.path.join(data_dir, 'cvi42_contours')
            if not os.path.exists(cvi42_contours_dir):
                os.mkdir(cvi42_contours_dir)
            parse_cvi42_xml.parseFile(xml_name, cvi42_contours_dir)
            

        # Rare cases when no dicom file exists
        # e.g. 12xxxxx/1270299
        if not os.listdir(dicom_dir):
            print('Warning: empty dicom directory! Skip this one.')
            continue

        # Convert dicom files and annotations into nifti images
        dset = Biobank_Dataset(dicom_dir, cvi42_contours_dir)
        dset.read_dicom_images()
        dset.convert_dicom_to_nifti(sub_output_dir)

        # Remove intermediate files
        shutil.rmtree(dicom_dir, ignore_errors=True)
        shutil.rmtree(cvi42_contours_dir, ignore_errors=True)

        for file_path in (xml_name, json_name, txt_name):
            if os.path.exists(file_path):
                os.remove(file_path)
        print('done')
