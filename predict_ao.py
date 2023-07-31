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
    This script runs inference on a given dataset.
    """
import os
import sys
import urllib.request
import shutil


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <data_dir> <blood_pressure_info.csv>', file=sys.stderr)
        exit(-1)

    # setup PYTHONPATH
    PYTHONPATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # The GPU device id
    CUDA_VISIBLE_DEVICES = 0

    DATA_DIR = sys.argv[1]
    BP_INFO_CSV = sys.argv[2]

    # remove trailing slash
    if DATA_DIR.endswith('/'):
        DATA_DIR = DATA_DIR[:-1]

    if DATA_DIR.endswith('.converted') or DATA_DIR.endswith('-converted') or DATA_DIR.endswith('_converted'):
        OUTPUT_CSV_DIR = DATA_DIR[:-10] + '.output_csv'
    else:
        OUTPUT_CSV_DIR = DATA_DIR + '.output_csv'
    if not os.path.exists(OUTPUT_CSV_DIR):
        os.mkdir(OUTPUT_CSV_DIR)

    # Analyse aortic images
    print('******************************')
    print('  Aortic image analysis')
    print('******************************')

    # Deploy the segmentation network
    print('Deploying the segmentation network ...')
    os.system(f'PYTHONPATH={PYTHONPATH} CUDA_VISIBLE_DEVICES={CUDA_VISIBLE_DEVICES} python3 common/deploy_network_ao.py --seq_name ao --data_dir {DATA_DIR} '
              f'--model_path trained_model/UNet-LSTM_ao')

    # Evaluate aortic areas
    print('Evaluating atrial areas ...')
    os.system(f'PYTHONPATH={PYTHONPATH} python3 aortic/eval_aortic_area2.py --data_dir {DATA_DIR} '
              f'--pressure_csv {BP_INFO_CSV} --output_csv {OUTPUT_CSV_DIR}/table_aortic_area.csv')

    print('Done.')
