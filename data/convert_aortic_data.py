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
import re
import csv
import glob
import re
import time
import pandas as pd
import dateutil.parser
from biobank_utils import *
import parse_cvi42_xml

DICOM_ZIP_PATTERN = re.compile('(\d+)_20210_(\d+)_0.zip')
AORTIC_DIR = "20210-aortic"

if __name__ == '__main__':

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f'Usage: {sys.argv[0]} <data_dir> [<output_dir>]', file=sys.stderr)
        exit(-1)
    
    # data_path is the path to the ukbb data
    # structure of input data dir
    # <data_dir>/
    #      |
    #      +--20210-aortic/
    #              |
    #              +--<eid1>_20210_<num>_0.zip
    #              +--<eid2>_20210_<num>_0.zip
    #              +--<eid3>_20210_<num>_0.zip
    #              ...
    # -----------------------------------------
    # structure of output dir
    # <output_dir>/
    #      |
    #      +--<eid1>_<num>/
    #      |       |
    #      |       +--ao.nii.gz
    #      |
    #      +--<eid2>_<num>/
    #      |       |
    #      |       +--ao.nii.gz
    #      |
    #     ...
    # -----------------------------------------
    data_path = sys.argv[1]
    # remove trailing slash if any
    if data_path.endswith('/'):
        data_path = data_path[:-1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else f'{data_path}.converted'

    ao_data_dir = os.path.join(data_path, AORTIC_DIR)
    if not os.path.isdir(ao_data_dir):
        print(f'{ao_data_dir} not found', file=sys.stderr)
        exit(-1)


    tmp_dir = os.path.join(os.getenv('HOME'), 'tmp')
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    zip_files = {}  # dictionary mapping from <eid>_<num> to list of zip file paths(relative to data_path)
    # iterate over aortic images
    for item in os.listdir(ao_data_dir):
        m = DICOM_ZIP_PATTERN.match(item)
        if not m:
            continue
        eid, num = m.group(1), m.group(2)
        key = f'{eid}_{num}'
        zip_list = zip_files.get(key, [])   # get or create list
        zip_list.append(os.path.join(AORTIC_DIR, item))    # append to the list
        zip_files[key] = zip_list   # update the dict

    skipped = 0
    # Convert image data for each <eid>_<num>
    for eid_and_num, zip_list in sorted(zip_files.items(), key=lambda x:x[0]):
        sub_output_dir = os.path.join(output_dir, eid_and_num)
        if os.path.exists(sub_output_dir):
            # print(f'skipping completed {eid_and_num}')
            skipped += 1
            continue
        if skipped > 0:
            print(f'{skipped} completed subjects skipped')
            skipped = 0
        print(f'converting {eid_and_num}...', end='', flush=True)
        tmp_sub_output_dir = os.path.join(output_dir, f'{eid_and_num}.working')
        if os.path.exists(tmp_sub_output_dir):
            shutil.rmtree(tmp_sub_output_dir)
        os.mkdir(tmp_sub_output_dir)
        # Decompress the zip files for this <eid>_<num>
        dicom_dir = os.path.join(tmp_dir, f'{eid_and_num}_dicom')
        if not os.path.exists(dicom_dir):
            os.mkdir(dicom_dir)
        
        for f in zip_list:
            # convert to full path
            zip_path = os.path.join(data_path, f)
            os.system(f'unzip -q -o {zip_path} -d {dicom_dir}')

            # Process the manifest file
            source_manifest = os.path.join(dicom_dir, 'manifest.csv');
            if not os.path.exists(source_manifest):
                source_manifest = os.path.join(dicom_dir, 'manifest.cvs');  # some(or all?) has extension .cvs
            dest_manifest = os.path.join(dicom_dir, 'manifest2.csv')
            process_manifest(source_manifest, dest_manifest)
            df2 = pd.read_csv(dest_manifest, error_bad_lines=False)

            # Organise the dicom files
            # Group the files into subdirectories for each imaging series
            for series_name, series_df in df2.groupby('series discription'):
                series_dir = os.path.join(dicom_dir, series_name)
                if not os.path.exists(series_dir):
                    os.mkdir(series_dir)
                for series_file in series_df['filename']:
                    sf_path = os.path.join(dicom_dir, series_file)
                    if os.path.exists(sf_path):
                        shutil.move(sf_path, series_dir)

        # Rare cases when no dicom file exists
        # e.g. 12xxxxx/1270299
        if not os.listdir(dicom_dir):
            print('Warning: empty dicom directory! Skip this one.')
            continue

        # Convert dicom files into nifti images
        dset = Biobank_Dataset(dicom_dir, None, suppress_warning=True)
        dset.read_dicom_images()
        dset.convert_dicom_to_nifti(tmp_sub_output_dir)

        # Remove intermediate files
        shutil.rmtree(dicom_dir, ignore_errors=True)

        # rename temp working dir to the final dir
        shutil.move(tmp_sub_output_dir, sub_output_dir)


        print('done')
    
    if skipped > 0:
        print(f'{skipped} completed subjects skipped')