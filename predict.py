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
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <data_dir>', file=sys.stderr)
        exit(-1)

    # setup PYTHONPATH
    PYTHONPATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # The GPU device id
    CUDA_VISIBLE_DEVICES = 0

    DATA_DIR = sys.argv[1]

    # remove trailing slash
    if DATA_DIR.endswith('/'):
        DATA_DIR = DATA_DIR[:-1]

    if DATA_DIR.endswith('.converted') or DATA_DIR.endswith('-converted') or DATA_DIR.endswith('_converted'):
        OUTPUT_CSV_DIR = DATA_DIR[:-10] + '.output_csv'
    else:
        OUTPUT_CSV_DIR = DATA_DIR + 'output_csv'
    if not os.path.exists(OUTPUT_CSV_DIR):
        os.mkdir(OUTPUT_CSV_DIR)

    # Analyse show-axis images
    print('******************************')
    print('  Short-axis image analysis')
    print('******************************')

    # Deploy the segmentation network
    print('Deploying the segmentation network ...')
    os.system(f'PYTHONPATH={PYTHONPATH} CUDA_VISIBLE_DEVICES={CUDA_VISIBLE_DEVICES} python3 common/deploy_network.py --seq_name sa --data_dir {DATA_DIR} '
              f'--model_path trained_model/FCN_sa')

    # Evaluate ventricular volumes
    print('Evaluating ventricular volumes ...')
    os.system(f'PYTHONPATH={PYTHONPATH} python3 short_axis/eval_ventricular_volume.py --data_dir {DATA_DIR} '
              f'--output_csv {OUTPUT_CSV_DIR}/table_ventricular_volume.csv')

    # Evaluate wall thickness
    print('Evaluating myocardial wall thickness ...')
    os.system(f'PYTHONPATH={PYTHONPATH} python3 short_axis/eval_wall_thickness.py --data_dir {DATA_DIR} '
              f'--output_csv {OUTPUT_CSV_DIR}/table_wall_thickness.csv')

    # Evaluate strain values
    if shutil.which('mirtk'):
        print('Evaluating strain from short-axis images ...')
        os.system(f'PYTHONPATH={PYTHONPATH} python3 short_axis/eval_strain_sax.py --data_dir {DATA_DIR} '
                  f'--par_dir par --output_csv {OUTPUT_CSV_DIR}/table_strain_sax.csv')

    # Analyse long-axis images
    print('******************************')
    print('  Long-axis image analysis')
    print('******************************')

    # Deploy the segmentation network
    print('Deploying the segmentation network FCN_la_2ch...')
    os.system(f'PYTHONPATH={PYTHONPATH} CUDA_VISIBLE_DEVICES={CUDA_VISIBLE_DEVICES} python3 common/deploy_network.py --seq_name la_2ch --data_dir {DATA_DIR} '
              f'--model_path trained_model/FCN_la_2ch')

    print('Deploying the segmentation network FCN_la_4ch...')
    os.system(f'PYTHONPATH={PYTHONPATH} CUDA_VISIBLE_DEVICES={CUDA_VISIBLE_DEVICES} python3 common/deploy_network.py --seq_name la_4ch --data_dir {DATA_DIR} '
              f'--model_path trained_model/FCN_la_4ch')

    print('Deploying the segmentation network FCN_la_4ch_seg4...')
    os.system(f'PYTHONPATH={PYTHONPATH} CUDA_VISIBLE_DEVICES={CUDA_VISIBLE_DEVICES} python3 common/deploy_network.py --seq_name la_4ch --data_dir {DATA_DIR} '
              f'--seg4 --model_path trained_model/FCN_la_4ch_seg4')

    # Evaluate atrial volumes
    print('Evaluating atrial volumes ...')
    os.system(f'PYTHONPATH={PYTHONPATH} python3 long_axis/eval_atrial_volume.py --data_dir {DATA_DIR} '
              f'--output_csv {OUTPUT_CSV_DIR}/table_atrial_volume.csv')

    # Evaluate strain values
    if shutil.which('mirtk'):
        print('Evaluating strain from long-axis images ...')
        os.system(f'PYTHONPATH={PYTHONPATH} python3 long_axis/eval_strain_lax.py --data_dir {DATA_DIR} '
                  f'--par_dir par --output_csv {OUTPUT_CSV_DIR}/table_strain_lax.csv')

    # Analyse aortic images
    # print('******************************')
    # print('  Aortic image analysis')
    # print('******************************')

    # # Deploy the segmentation network
    # print('Deploying the segmentation network ...')
    # os.system(f'PYTHONPATH={PYTHONPATH} CUDA_VISIBLE_DEVICES={CUDA_VISIBLE_DEVICES} python3 common/deploy_network_ao.py --seq_name ao --data_dir {DATA_DIR} '
    #           f'--model_path trained_model/UNet-LSTM_ao')

    # Evaluate aortic areas
    # print('Evaluating atrial areas ...')
    # os.system(f'PYTHONPATH={PYTHONPATH} python3 aortic/eval_aortic_area.py --data_dir {DATA_DIR} '
    #           f'--pressure_csv {DATA_DIR}/blood_pressure_info.csv --output_csv {OUTPUT_CSV_DIR}/table_aortic_area.csv')

    print('Done.')
