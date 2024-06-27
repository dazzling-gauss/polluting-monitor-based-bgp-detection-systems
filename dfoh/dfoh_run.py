import subprocess
import csv
import os
from config import Config

FAST = False  # If set to True, dfoh will re-use previously computed models


class DFOHRunner:
    """
    This class is used to run the DFOH pipeline.
    It will expect the dataset.txt file to be in the {Config.DFOH_TEMP_DIR}/{n_run} folder.
    This file should contain the links (with path) to be analyzed.
    """

    def __init__(self, n_run=0):
        self.DATA_NAME = "dataset.txt"
        self.DATA_FILE = os.path.abspath(
            f"{Config.DFOH_TEMP_DIR}/{n_run}/dataset.txt")
        self.DB_DIR = os.path.abspath(Config.DFOH_DB_DIR)
        self.DATE = Config.DATE_EXPERIMENT
        self.RESULT_FOLDER = f"{Config.DFOH_TEMP_DIR}/{n_run}"

        pass

    def start(self):
        self.run_bidirectionality()
        self.run_peeringdb()
        self.run_topological()
        self.run_aspath()
        file = self.merge_data()
        self.run_inference(file)
        self.parse_results()

    def start_container(self, db_dir, docker_image, docker_name, file_name=None,
                        cmds=None, copy_file=None, copy_output=False):
        # kill and remove the docker container.
        subprocess.run("docker kill {}".format(docker_name), shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("docker rm {}".format(docker_name), shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Run the docker container.
        docker_cmd = "docker run -itd --name=\"{}\" \
        --hostname=\"{}\" \
        -v {}:/tmp/db \
        {}".format(docker_name, docker_name, db_dir, docker_image)
        subprocess.run(docker_cmd, shell=True)
        print("[RUNNER] Running container: {}".format(docker_name))

        if file_name is not None:
            docker_cmd = "docker cp {} {}:{}".format(
                file_name, docker_name, "/tmp/")
            print("[RUNNER] Running command: {}".format(docker_cmd))
            subprocess.run(docker_cmd, shell=True)

        output = None

        if cmds is not None:
            docker_cmd = "docker exec -it {} {}".format(docker_name, cmds)
            print("[RUNNER] Running command: {}".format(docker_cmd))
            sp = subprocess.run(docker_cmd, shell=True,
                                stdout=subprocess.PIPE if copy_output else None)
            if copy_output:
                output = sp.stdout.decode()

        if copy_file is not None:
            docker_cmd = "docker cp {}:{} {}".format(
                docker_name, "/tmp/{}".format(copy_file), self.RESULT_FOLDER)
            print("[RUNNER] Running command: {}".format(docker_cmd))
            subprocess.run(docker_cmd, shell=True)

        subprocess.run("docker kill {}".format(docker_name), shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("docker rm {}".format(docker_name), shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output

    def run_bidirectionality(self):
        # Run Bidirectionality features
        print("[RUNNER] Running Bidirectionality features")
        docker_name = "dfoh_bidirectionality"
        copy_file = "bidirectionality_results.txt"
        cmd = f"python3 orchestrator.py --db_dir=/tmp/db --date={self.DATE} --link_file=/tmp/{self.DATA_NAME}"  \
            f" --outfile=/tmp/{copy_file}"
        self.start_container(self.DB_DIR, "dfoh_bidirectionality",
                             docker_name, self.DATA_FILE, cmd, copy_file)

    def run_peeringdb(self):
        # Run PeeringDB features
        print("[RUNNER] Running PeeringDB features")
        docker_name = "dfoh_peeringdb"
        copy_file = "peeringdb_results.txt"
        clean_flag = "False" if FAST else "True"
        cmd = f"python3 orchestrator.py --clean={clean_flag} --db_dir=/tmp/db --date={self.DATE}" \
            f" --link_file=/tmp/{self.DATA_NAME} --outfile=/tmp/{copy_file}"
        self.start_container(self.DB_DIR, "dfoh_peeringdb",
                             docker_name, self.DATA_FILE, cmd, copy_file)

    def run_topological(self):
        # Run Topological features
        print("[RUNNER] Running Topological features")
        docker_name = "dfoh_topological"
        copy_file = "topological_results.txt"
        cmd = f"python3 topo_feat.py --db_dir=/tmp/db --date={self.DATE} --link_file=/tmp/{self.DATA_NAME}" \
            f" --outfile=/tmp/{copy_file} --nb_threads={Config.N_THREADS}"
        self.start_container(self.DB_DIR, "dfoh_topological",
                             docker_name, self.DATA_FILE, cmd, copy_file)

    def run_aspath(self):
        print("[RUNNER] Running ASPath features")
        docker_name = "dfoh_aspathfeat"
        copy_file = "aspath_results.txt"
        overide_flg = "1" if not FAST else "0"
        cmd = f"python3 aspath_feat.py --db_dir=/tmp/db --overide_model={overide_flg} --date={self.DATE}" \
            f" --aspath_file=/tmp/{self.DATA_NAME} --outfile=/tmp/{copy_file}"
        self.start_container(self.DB_DIR, "dfoh_aspathfeat",
                             docker_name, self.DATA_FILE, cmd, copy_file)

    def merge_data(self):
        name_files = ["bidirectionality_results.txt",
                      "peeringdb_results.txt", "topological_results.txt"]
        # merge the columns of the files
        data = {}
        for file_name in name_files:
            with open(os.path.join(self.RESULT_FOLDER, file_name), 'r') as file:
                reader = csv.reader(file, delimiter=' ')
                # first row is the header
                header = next(reader)
                for row in reader:
                    id = (row[0], row[1])
                    if id not in data:
                        data[id] = {}
                    for i in header:
                        data[id][i] = row[header.index(i)]

        as_paths_file = "aspath_results.txt"
        with open(os.path.join(self.RESULT_FOLDER, as_paths_file), 'r') as file:
            reader = csv.reader(file, delimiter=' ')
            # first row is the header
            header = next(reader)
            for row in reader:
                id = (row[0], row[1])
                if id not in data:
                    continue
                if "paths" not in data[id]:
                    data[id]["paths"] = []
                data[id]["paths"].append({})

                for i in header:
                    data[id]["paths"][-1][i] = row[header.index(i)]

        # write the merged data to a new file
        i = 0
        # check if file results_{i}.txt exists
        while os.path.exists(os.path.join(self.RESULT_FOLDER, "merged_results_{}.txt".format(i))):
            i += 1

        if len(data) == 0:
            print("[RUNNER] No data to write")
            return

        header = data[list(data.keys())[0]].keys()
        header_no_paths = [x for x in header if x != "paths"]
        header_no_paths.extend(data[list(data.keys())[0]]["paths"][0].keys())

        with open(os.path.join(self.RESULT_FOLDER, "merged_results_{}.txt".format(i)), 'w') as file:
            writer = csv.writer(file, delimiter=' ')
            writer.writerow(header_no_paths)
            for id in data:
                for j in range(len(data[id]["paths"])):
                    row = []
                    for x in header:
                        if x != "paths":
                            row.append(data[id][x])
                        else:
                            for y in data[id]["paths"][j]:
                                row.append(data[id]["paths"][j][y])

                    writer.writerow(row)

        return "merged_results_{}.txt".format(i)

    def run_inference(self, merged_name):
        # Run Inference
        fpr_weights = "1,2,3,4,5,6,7,8,9,10"
        nb_days_training = 60
        docker_name = "dfoh_inference"
        overide_flg = "1" if not FAST else "0"
        cmd = "python3 inference_maker.py --date={} --input_file=/tmp/{} --fpr_weights={} --overide={}" \
              " --nb_days_training_data={}".format(
                  self.DATE, merged_name, fpr_weights, overide_flg, nb_days_training)

        output = self.start_container(self.DB_DIR, "dfoh_inference",
                                      docker_name, os.path.join(self.RESULT_FOLDER, merged_name), cmd, copy_output=True)
        output = output.split("\n")

        s = ""
        for line in output:
            if "[" in line or line.strip() == "":
                continue
            s += line + "\n"

        with open(os.path.join(self.RESULT_FOLDER, "inference_results.txt"), 'w') as file:
            file.write(s)

    def parse_results(self):
        csv_results = []
        with open(os.path.join(self.RESULT_FOLDER, "inference_results.txt"), 'r') as file:
            next(file)
            for line in file:
                csv_results.append(line.split())

        dict_res = {}
        fd_out = open(os.path.join(
            self.RESULT_FOLDER, "parsed_results.txt"), 'w')

        for line in csv_results:
            as1 = line[0]
            as2 = line[1]

            if int(as1) > int(as2):
                as1, as2 = as2, as1

            # asp = line[2].split('|')
            label = int(line[3])
            # proba = line[4]
            sensitivity = line[5]

            if (as1, as2) not in dict_res:
                dict_res[(as1, as2)] = {}
            if sensitivity not in dict_res[(as1, as2)]:
                dict_res[(as1, as2)][sensitivity] = []
            dict_res[(as1, as2)][sensitivity].append(label)

        for as1, as2 in dict_res:
            sus = 0
            leg = 0
            asp_count = 0

            for sensitivity in dict_res[(as1, as2)]:
                if dict_res[(as1, as2)][sensitivity].count(0) > dict_res[(as1, as2)][sensitivity].count(1):
                    leg += 1
                else:
                    sus += 1
                asp_count += 1

            if sus == 0:
                fd_out.write('!leg {} {} {} {} {}\n'.format(
                    as1, as2, leg, sus, asp_count))
            else:
                fd_out.write('!sus {} {} {} {} {}\n'.format(
                    as1, as2, leg, sus, asp_count))

            for sensitivity in dict_res[(as1, as2)]:
                fd_out.write("{} {} {} {} {}\n".format(
                    as1,
                    as2,
                    sensitivity,
                    dict_res[(as1, as2)][sensitivity].count(0),
                    dict_res[(as1, as2)][sensitivity].count(1)))

        fd_out.close()
