# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Test Config Library"""

import copy
import datetime
import filecmp
import json
import os
import tempfile

from tvm.autotvm.config_library import ConfigLibrary
from tvm.autotvm.task.dispatcher import ApplyHistoryBest
from tvm.autotvm.tuner.callback import log_to_file
from tvm.autotvm.record import encode

from test_autotvm_common import get_sample_records


def get_random_configs(n):
    hard_configs = [
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 141, 126, 115, 'float32'], {'i': 0, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 1]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[1], 0, 0, 1574432749.5476737], 'v': 0.1, 't': [10, 'TunerA', 25]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 45, 217, 17, 'float32'], {'i': 1, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 2]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[2], 0, 1, 1574432749.5476935], 'v': 0.1, 't': [2, 'TunerC', 104]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 120, 14, 102, 'float32'], {'i': 2, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 4]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[3], 0, 2, 1574432749.5477045], 'v': 0.1, 't': [0, 'TunerA', 223]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 215, 113, 230, 'float32'], {'i': 3, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 8]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[4], 0, 3, 1574432749.547714], 'v': 0.1, 't': [10, 'TunerC', 558]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 4, 82, 217, 'float32'], {'i': 4, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 16]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[5], 0, 4, 1574432749.5477228], 'v': 0.1, 't': [9, 'TunerB', 828]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 111, 173, 53, 'float32'], {'i': 5, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 32]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[6], 0, 5, 1574432749.5477316], 'v': 0.1, 't': [5, 'TunerB', 159]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 184, 177, 136, 'float32'], {'i': 6, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 64]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[7], 0, 6, 1574432749.5477402], 'v': 0.1, 't': [1, 'TunerB', 99]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 64, 194, 41, 'float32'], {'i': 7, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 128]], ['tile_x', 'sp', [-1, 1]]]}], 'r': [[8], 0, 7, 1574432749.547748], 'v': 0.1, 't': [0, 'TunerC', 470]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 186, 99, 36, 'float32'], {'i': 8, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 1]], ['tile_x', 'sp', [-1, 2]]]}], 'r': [[9], 0, 8, 1574432749.547757], 'v': 0.1, 't': [8, 'TunerB', 849]},
        {'i': ['llvm', 'matmul', [128, 128, 128, 'float32'], {}, ['matmul', 149, 41, 120, 'float32'], {'i': 9, 't': '', 'c': None, 'e': [['tile_y', 'sp', [-1, 2]], ['tile_x', 'sp', [-1, 2]]]}], 'r': [[10], 0, 9, 1574432749.5477653], 'v': 0.1, 't': [0, 'TunerC', 233]},
    ]
    random_configs = []
    for i in range(n):
        random_configs.append(hard_configs[i // 10])

    return random_configs


def test_initialise_config_library():
    with tempfile.TemporaryDirectory() as tmp_config_dir:
        # Check library can initialise when directory exists
        _ = ConfigLibrary(tmp_config_dir)
        # Check library can initialise when directory doesn't exist
        config_library = ConfigLibrary(tmp_config_dir + "/nested")
        with open(config_library.library_index) as f:
            library_index = json.load(f)

        # Check library index contents are correct
        library_root = library_index["root"]
        assert library_root == os.path.join(tmp_config_dir, "nested")
        assert library_index["targets"] == {}
        assert library_index["jobs_index"] == config_library.JOBS_INDEX_FILE_NAME
        assert library_index["jobs_dir"] == config_library.JOBS_DIRECTORY_NAME
        # Check library job file/dir have been created properly
        assert os.path.isdir(os.path.join(library_root, library_index["jobs_dir"]))
        assert os.path.isfile(os.path.join(library_root, library_index["jobs_index"]))


def test_save_config():
    with tempfile.TemporaryDirectory() as tmp_config_dir:
        config_library = ConfigLibrary(tmp_config_dir)
        records = get_sample_records(4)
        configs = []
        for record in records:
            inp, result = record
            config = json.loads(encode(inp, result))
            config["t"] = [0, "TestTuner", 100]
            configs.append(config)

        # Alternative target
        configs[0]["i"][0] = "opencl"
        # Alternative workload
        configs[1]["i"][4][1] = 256
        # Slow config
        configs[2]["r"][0][0] = 1.0
        # Fast config
        configs[3]["r"][0][0] = 0.5

        for config in configs:
            config_library.save_config(config)

        # Check the target configs files have been created
        llvm_file = os.path.join(tmp_config_dir, "llvm.configs")
        opencl_file = os.path.join(tmp_config_dir, "opencl.configs")
        backup_llvm_file = os.path.join(
            tmp_config_dir, ConfigLibrary.BACKUP_DIRECTORY_NAME, "llvm.configs.backup"
        )
        backup_opencl_file = os.path.join(
            tmp_config_dir, ConfigLibrary.BACKUP_DIRECTORY_NAME, "opencl.configs.backup"
        )
        assert os.path.isfile(llvm_file)
        assert os.path.isfile(opencl_file)
        assert os.path.isfile(backup_llvm_file)
        assert os.path.isfile(backup_opencl_file)
        with open(llvm_file) as f:
            f.seek(0)
            configs = json.load(f)
            assert len(configs) == 2, len(configs)
            for workload in configs:
                config = configs[workload]
                assert json.loads(workload.replace("'", '"')) == config["i"][4], workload
                if config["i"][4][1] == 128:
                    assert config["r"][0][0] == 0.5, config


def test_get_config_file():
    with tempfile.TemporaryDirectory() as tmp_config_dir:
        config_library = ConfigLibrary(tmp_config_dir)
        same_targets = [
            "llvm -mcpu=test1 -mfloat-abi=hard -mattr=+neon -target=aarch64-linux-gnu",
            "llvm -mfloat-abi=hard -mcpu=test1 -target=aarch64-linux-gnu -mattr=+neon",
            "llvm -target=aarch64-linux-gnu -mattr=+neon -mcpu=test1 -mfloat-abi=hard",
        ]
        different_targets = [
            "opencl -device=bifrost",
            "llvm -target=aarch64-linux-gnu",
            "llvm -target=aarch64-linux-gnu -mattr=+neon",
        ]
        same_config_files = set()
        for target in same_targets:
            config_file = config_library.get_config_file(target, create=True)
            same_config_files.add(config_file)

        # Check that the same targets point to the same file
        assert len(same_config_files) == 1, same_config_files
        correct_name = "llvm--mattr=+neon--mcpu=test1--mfloat-abi=hard"\
                       "--target=aarch64-linux-gnu.configs"
        correct_path = os.path.join(tmp_config_dir, correct_name)
        # Check that the file has the correct name
        generated_path = same_config_files.pop()
        assert generated_path == correct_path, generated_path
        different_config_files = set()
        for target in different_targets:
            config_file = config_library.get_config_file(target, create=True)
            different_config_files.add(config_file)

        # Check that different targets point to different files
        assert len(different_config_files) == 3, different_config_files


def test_get_config():
    with tempfile.TemporaryDirectory() as tmp_config_dir:
        config_library = ConfigLibrary(tmp_config_dir)
        configs = get_random_configs(100)
        for config in configs:
            config_library.save_config(config)

        # Check all saved configs can be retrieved from the library
        for config in configs:
            workload = config["i"][4]
            target = config["i"][0]
            saved_config = config_library.get_config(target, workload)
            assert saved_config == config, saved_config


def test_load():
    with tempfile.TemporaryDirectory() as tmp_config_dir:
        config_library = ConfigLibrary(tmp_config_dir)
        configs = get_random_configs(100)
        for config in configs:
            config_library.save_config(config)

        context = config_library.load("llvm")
        assert type(context) == ApplyHistoryBest


def test_save_job():
    class _MockJob:
        pass

    with tempfile.TemporaryDirectory() as tmp_config_dir:
        config_library = ConfigLibrary(tmp_config_dir)
        # Make a mock TuningJob object
        mock_job = _MockJob()
        mock_job.target = "llvm"
        mock_job.platform = {"board": "hikey960"}
        mock_job.content = {"model": "resnet50v2"}
        mock_job.start_time = datetime.datetime.utcnow().isoformat()
        mock_job.end_time = datetime.datetime.utcnow().isoformat()
        # Make mock results
        records = get_sample_records(4)
        results_by_workload = {}
        inputs = []
        results = []
        correct_tasks = []
        for i, record in enumerate(records):
            inp, result = copy.deepcopy(record)
            workload = ('matmul', i, 128, 128, 'float32')
            inp.task.workload = workload
            tuner = "TestTuner"
            trials = i*100
            inputs.append(inp)
            results.append(result)
            config_entry = json.loads(encode(inp, result, 'json'))
            config_entry["t"] = ["1", tuner, trials]
            correct_tasks.append(json.dumps(config_entry))
            results_by_workload[workload] = copy.copy([inp, result, tuner, trials])

        mock_job.results_by_workload = results_by_workload
        # Make mock tuning log
        tuning_log = os.path.join(tmp_config_dir, 'tuning.log')
        logging_callback = log_to_file(tuning_log)
        logging_callback("TestTuner", inputs, results)
        mock_job.log = tuning_log
        # Save the mock job
        config_library.save_job(mock_job, save_history=True)
        backup_job_index = os.path.join(
            tmp_config_dir,
            ConfigLibrary.BACKUP_DIRECTORY_NAME,
            ConfigLibrary.JOBS_INDEX_FILE_NAME + ".backup",
        )
        assert os.path.isfile(backup_job_index)
        saved_log = os.path.join(tmp_config_dir, "jobs/1_llvm.log")
        with open(config_library.jobs_index) as f:
            jobs_index = json.load(f)
            correct_index = {
                "1":
                    {
                        "id": "1",
                        "log": saved_log,
                        "target": mock_job.target,
                        "platform": mock_job.platform,
                        "content": mock_job.content,
                        "start_time": mock_job.start_time,
                        "end_time": mock_job.end_time,
                    }
            }
            tasks = jobs_index["1"].pop("tasks")
            # Check the saved tasks are correct
            assert set(tasks) == set(correct_tasks), tasks
            # Check the index entry is correct
            assert jobs_index == correct_index, jobs_index

        # Check saved tuning log exists
        assert os.path.isfile(saved_log)
        # Check saved tuning log is equal to the original log
        assert filecmp.cmp(saved_log, tuning_log)


if __name__ == "__main__":
    test_initialise_config_library()
    test_save_config()
    test_get_config_file()
    test_get_config()
    test_load()
    test_save_job()
