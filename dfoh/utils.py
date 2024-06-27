from itertools import groupby
from config import Config
import networkx as nx
import os


def load_topo(original=False):
    graph = nx.Graph()
    topo_fld = f"{Config.DFOH_DB_DIR}/merged_topology/{Config.DATE_EXPERIMENT}.txt"
    if original or not os.path.exists(topo_fld):
        topo_fld = f"./dfoh/data/topology-{Config.DATE_EXPERIMENT}.bkp"
    print(f"Loading topology from {topo_fld}")

    if not os.path.exists(topo_fld):
        raise ValueError(f"File {topo_fld} does not exist.")

    with open(topo_fld, "r") as f:
        for line in f:
            src, dst = line.strip().split()
            graph.add_edge(src, dst)

    return graph


def aspath_to_list(path):
    """
    Converts a path from a string to a list of ASes. Copied from DFOH code.
    """
    all_hops = []
    hops = [k for k, g in groupby(path.replace('\n', '').split(" "))]
    # for all the elements in the array
    for i in range(0, len(hops)):
        # If the element is an AS aggregation, desagrege it
        all_hops.append(hops[i].replace('{', '').replace('}', '').split(","))

    return all_hops


def load_paths(as_to_load) -> list:
    aspaths_fld = f"{Config.DFOH_DB_DIR}/paths/{Config.DATE_EXPERIMENT.split('-')[0]}" \
        f"-{Config.DATE_EXPERIMENT.split('-')[1]}-01_paths.txt"

    print(f"Loading paths from {aspaths_fld}")
    if not os.path.exists(aspaths_fld):
        raise ValueError(f"File {aspaths_fld} does not exist.")

    i = 0
    paths = []
    with open(aspaths_fld, "r") as f:
        for line in f:
            i += 1
            if i % 10000000 == 0:
                print(f"Processed {i} lines.")

            if as_to_load not in line:
                continue

            path = line.strip().replace("\n", "")
            path = aspath_to_list(path)

            if len(path) < 3:
                continue
            orig = path[-1][0]
            if orig != as_to_load:
                continue

            paths.append(path)

    print(
        f"Node {as_to_load} has {len(paths)} paths.")
    if len(paths) == 0:
        raise ValueError(f"No paths for node {as_to_load}.")
    return paths


def load_country(country):
    ASes = set()
    COUNTRY_PATH = f"{Config.DFOH_DB_DIR}/peeringdb/{Config.DATE_EXPERIMENT}_country.txt"
    print(f"Getting all nodes from country {country} ...")

    with open(COUNTRY_PATH, 'r') as f:
        for line in f:
            # 31019 NL bgpview
            line = line.strip().split()
            if line[1] == country:
                ASes.add(line[0])

    return ASes


def load_leg(n_run, folder=None):
    file = f"{Config.DFOH_TEMP_DIR}/{n_run}/parsed_results.txt"
    if folder:
        file = f"{folder}/{n_run}/parsed_results.txt"

    if not os.path.exists(file):
        raise ValueError(f"File {file} does not exist.")

    leg_edges = set()
    with open(file, "r") as f:
        for line in f:
            if line.startswith("!leg"):
                # !leg 200690 205218 10 0 10
                linetab = line.rstrip().split(' ')
                as1 = int(linetab[1])
                as2 = int(linetab[2])
                leg_edges.add((as1, as2))

    return leg_edges


def reset_runs(attacker):
    move_tmp_to_data(attacker)
    clean_tmp()
    load_backup()


def move_tmp_to_data(attacker):
    if not os.path.exists(Config.DFOH_TEMP_DIR) or len(os.listdir(Config.DFOH_TEMP_DIR)) == 0:
        return

    data_fld = f"dfoh/data/{attacker}"

    i = 0
    while os.path.exists(data_fld):
        i += 1
        data_fld = f"dfoh/data/{attacker}-{i}"

    os.makedirs(data_fld)
    os.system(f"cp -r {Config.DFOH_TEMP_DIR}/* {data_fld}/")

    not_prune_file = ["parsed_results.txt", "dataset.txt"]
    # walk in all folder and remove all files except the ones in not_prune_file
    for root, dirs, files in os.walk(data_fld):
        for file in files:
            if file not in not_prune_file:
                os.remove(os.path.join(root, file))


def clean_tmp():
    print("Cleaning temp folder")
    if not os.path.exists(Config.DFOH_TEMP_DIR) or len(os.listdir(Config.DFOH_TEMP_DIR)) == 0:
        return

    for folder in os.listdir(Config.DFOH_TEMP_DIR):
        folder_path = os.path.join(Config.DFOH_TEMP_DIR, folder)
        if os.path.isdir(folder_path):
            os.system(f"rm -rf {folder_path}")


def load_backup():
    bkp_fld = f"dfoh/data/topology-{Config.DATE_EXPERIMENT}.bkp"
    if not os.path.exists(bkp_fld):
        raise ValueError(f"File {bkp_fld} does not exist.")

    print(f"Loading backup from {bkp_fld}")
    merged_folder = os.path.join(Config.DFOH_DB_DIR, "merged_topology")
    os.system(f"cp {bkp_fld} {merged_folder}/{Config.DATE_EXPERIMENT}.txt")
    print(f"Backup loaded to {merged_folder}/{Config.DATE_EXPERIMENT}.txt")
