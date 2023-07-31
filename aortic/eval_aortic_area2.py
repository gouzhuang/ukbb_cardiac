# Copyright 2018, Wenjia Bai. All Rights Reserved.
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
import os
import numpy as np
import nibabel as nib
import pandas as pd
import re
import argparse
from ukbb_cardiac.common.cardiac_utils import aorta_pass_quality_control

DATA_PATTERN = re.compile('(\d+)_(\d+)')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', metavar='dir_name', default='', required=True)
    parser.add_argument('--pressure_csv', metavar='csv_name', default='', required=True)
    parser.add_argument('--output_csv', metavar='csv_name', default='', required=True)
    args = parser.parse_args()

    # Read the spreadsheet for blood pressure information
    # Use central blood pressure provided by the Vicorder software
    # [1] Steffen E. Petersen et al. UK Biobank’s cardiovascular magneticresonance protocol. JCMR, 2016.
    # Aortic distensibility represents the relative change in area of the aorta per unit pressure,
    # taken here as the "central pulse pressure".
    #
    # The Vicorder software calculates values for central blood pressure by applying a previously described
    # brachial-to-aortic transfer function. What I observed from the data and Figure 5 in the SOP pdf
    # (https://biobank.ctsu.ox.ac.uk/crystal/docs/vicorder_in_cmri.pdf) is that after the transfer, the DBP
    # keeps the same as the brachial DBP, but the SBP is different.
    #
    # The csv file look like below. The values are mean
    # -----------------EXAMPLE BEGIN------------------------
    # eid,Central augmentation pressure during PWA,Central pulse pressure during PWA,Central systolic blood pressure during PWA,Central systolic blood pressure during PWA,Mean arterial pressure during PWA,Systolic brachial blood pressure,Systolic brachial blood pressure during PWA, Vicorder results plausible
    # 4313087,9,48,126,13:57:47,102,127,127,Yes
    # 1386687,33,102,161,9:32:50,102,162,162,Yes
    # 1386687,33,102,161,9:32:50,102,162,162,Yes
    # 1955226,11,43,115,11:54:25,89,116,116,Yes
    # 2612263,14,83,146,18:40:30,96,149,149,Yes
    # 5872277,19,80,163,17:57:56,116,164,164,Yes
    # 5888452,14,71,131,13:49:25,86,138,138,Yes
    # 1626662,8,54,135,15:01:23,104,140,140,Yes
    # 1439252,2,5,41,8:58:23,38,41,41,Yes
    # 1958186,6,63,138,9:15:19,99,147,147,Yes
    # -----------------EXAMPLE END------------------------

    df_info = pd.read_csv(args.pressure_csv, header=[0], index_col=0)
    central_pp = df_info['Central pulse pressure during PWA']

    # Discard central blood pressure < 10 mmHg
    central_pp[central_pp < 10] = np.nan

    data_path = args.data_dir
    data_list = sorted(os.listdir(data_path))
    table = []
    processed_list = []
    for data in data_list:
        data_dir = os.path.join(data_path, data)
        image_name = os.path.join(data_dir, 'ao.nii.gz')
        seg_name = os.path.join(data_dir, 'seg_ao.nii.gz')

        m = DATA_PATTERN.match(data)
        if not m:
            print(f'warning: skip invalid data "{data}"')
            continue
        eid = int(m.group(1))
        if os.path.exists(image_name) and os.path.exists(seg_name):
            print(data)
            
            central_pp_value = central_pp.loc[eid] if eid in central_pp.index else np.nan

            # Read image
            nim = nib.load(image_name)
            dx, dy = nim.header['pixdim'][1:3]
            area_per_pixel = dx * dy
            image = nim.get_data()

            # Read segmentation
            nim = nib.load(seg_name)
            seg = nim.get_data()

            if not aorta_pass_quality_control(image, seg):
                continue

            # Measure the maximal and minimal area for the ascending aorta and descending aorta
            val = {}
            for l_name, l in [('AAo', 1), ('DAo', 2)]:
                val[l_name] = {}
                A = np.sum(seg == l, axis=(0, 1, 2)) * area_per_pixel
                max_area = A.max()
                min_area = A.min()
                max_diameter = 2*np.sqrt(max_area/np.pi)
                min_diameter = 2*np.sqrt(min_area/np.pi)
                val[l_name]['max area'] = max_area
                val[l_name]['min area'] = min_area
                val[l_name]['max diameter'] = max_diameter
                val[l_name]['min diameter'] = min_diameter
                val[l_name]['distensibility'] = (max_area - min_area) / (min_area * central_pp_value) * 1e3

            line = [val['AAo']['max area'], val['AAo']['min area'], val['AAo']['max diameter'], val['AAo']['min diameter'], val['AAo']['distensibility'],
                    val['DAo']['max area'], val['DAo']['min area'], val['DAo']['max diameter'], val['DAo']['min diameter'], val['DAo']['distensibility']]
            table += [line]
            processed_list += [data]

    # Save the spreadsheet for the measures
    df = pd.DataFrame(table, index=processed_list,
                      columns=['AAo max area (mm2)', 'AAo min area (mm2)', 'AAo max diameter (mm)', 'AAo min diameter (mm)', 'AAo distensibility (10-3 mmHg-1)',
                               'DAo max area (mm2)', 'DAo min area (mm2)', 'DAo max diameter (mm)', 'DAo min diameter (mm)', 'DAo distensibility (10-3 mmHg-1)'])
    df.to_csv(args.output_csv)
