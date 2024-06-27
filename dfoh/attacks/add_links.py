from dfoh import utils
from config import Config
from dfoh.dfoh_run import DFOHRunner
import random
import os
import time


class AddLinkAttack:
    def __init__(self):
        pass

    def _single_run(self, n_run):
        runner = DFOHRunner(n_run)
        start_time = time.time()
        print('Running DFOH...')
        runner.start()
        print(f'Execution time: {time.time()/60 - start_time/60} minutes')

    def run_single_attacker(self, attacker_as, max_runs=5):
        """
        Run the attack for a single attacker.
        """
        utils.reset_runs("unknown")

        for n_run in range(0, max_runs):
            print(f"Run {n_run}")
            if n_run == 0:
                self._generate_dataset(n_run, attacker_as)
            else:
                self._add_leg_to_topology(n_run)

            self._single_run(n_run)

        utils.reset_runs(attacker_as)

    def run_country_diff_degrees(self, country, max_runs=5):
        """
        Run the attack for a COUNTRY, with 3 different attackers.
        Those attackers have different degrees, to test the impact of the degree in the attack.
        """
        utils.reset_runs("unknown")
        topo = utils.load_topo()
        possible_attackers = utils.load_country(country)
        treshold_degree = [(1, 10), (100, 300), (500, 3000)]
        attackers = []

        print("Finding attackers")
        while len(treshold_degree) > 0:
            # get random attacker
            if len(possible_attackers) == 0:
                raise ValueError("No more possible attackers")

            attacker = random.choice(list(possible_attackers))

            try:
                d_attacker = topo.degree[attacker]
            except KeyError:
                possible_attackers.remove(attacker)
                continue

            for min_degree, max_degree in treshold_degree:
                if d_attacker >= min_degree and d_attacker <= max_degree:
                    print(
                        f'Attacker found: {attacker} with degree {d_attacker}')
                    attackers.append(attacker)
                    treshold_degree.remove((min_degree, max_degree))
                    break
            possible_attackers.remove(attacker)

            attackers = sorted(attackers, key=lambda x: topo.degree[x])

        for attacker in attackers:
            print(
                f"Attacker {attacker} with degree {topo.degree[attacker]}")
            self.run_single_attacker(attacker, max_runs)

    def _generate_dataset(self, n_run, attacker_as):
        """
        Generate a dataset where the attacker AS tries to hijack every AS in the network.
        """

        print(f"Generating dataset for attacker AS {attacker_as}")

        graph = utils.load_topo(True)
        paths = utils.load_paths(attacker_as)

        already_processed = set()
        total_paths = len(paths)
        dataset = []

        for node in graph.nodes():
            if node == attacker_as:
                continue

            if graph.has_edge(attacker_as, node) or graph.has_edge(node, attacker_as):
                continue

            if node in already_processed:
                continue

            already_processed.add(node)

            # convention degree as1 > degree as2
            as1 = attacker_as
            as2 = node
            if int(as1) > int(as2):
                as1, as2 = as2, as1

            # Take a random number of paths to add to the dataset
            n_paths = random.randint(1, min(5, total_paths))
            tmp = []
            while len(tmp) < n_paths:
                path = random.choice(paths)
                flat_path = ' '.join([str(asn)
                                     for sublist in path for asn in sublist])
                if flat_path not in tmp:
                    tmp.append(flat_path)
                    s = f"{as1} {as2},{flat_path} {node}"
                    dataset.append(s)
            pass

        if not os.path.exists(f"{Config.DFOH_TEMP_DIR}/{n_run}"):
            os.makedirs(f"{Config.DFOH_TEMP_DIR}/{n_run}")

        data_path = f"{Config.DFOH_TEMP_DIR}/{n_run}/dataset.txt"
        with open(data_path, "w") as f:
            for line in dataset:
                f.write(f"{line}\n")
        print(f"Dataset generated at {data_path}")

    def _add_leg_to_topology(self, n_run):
        """
            Get the results from n_run-1 and add the links to the topology.
            It also create the new dataset, with the removed legitimate links.
        """
        print(f"Adding links to topology for run {n_run-1}")

        prev_run_fold = f"{Config.DFOH_TEMP_DIR}/{n_run-1}"
        if not os.path.exists(prev_run_fold):
            raise ValueError(f"Folder {prev_run_fold} does not exist.")

        if not os.path.exists(f"{prev_run_fold}/dataset.txt") or \
                not os.path.exists(f"{prev_run_fold}/parsed_results.txt"):
            raise ValueError(f"Files not found in {prev_run_fold}.")

        leg_edges = utils.load_leg(n_run-1)

        # create new folder if it does not exist
        new_run_fold = f"{Config.DFOH_TEMP_DIR}/{n_run}"
        if not os.path.exists(new_run_fold):
            os.makedirs(new_run_fold)

        print(f"Copying dataset from {n_run-1} to {n_run}")
        with open(f"{prev_run_fold}/dataset.txt", "r") as f, \
                open(f"{new_run_fold}/dataset.txt", "w") as f2:
            for line in f:
                linetab = line.rstrip().split(',')[0].split(' ')
                as1 = int(linetab[0])
                as2 = int(linetab[1])
                if (as1, as2) in leg_edges:
                    continue
                f2.write(line)

        print("Add links to topology")
        # backup the current topology
        os.system(f"cp {Config.DFOH_DB_DIR}/merged_topology/{Config.DATE_EXPERIMENT}.txt "
                  f"{new_run_fold}/topology_backup.txt")
        topology_file = f"{Config.DFOH_DB_DIR}/merged_topology/{Config.DATE_EXPERIMENT}.txt"
        # append the new links to the topology
        with open(topology_file, "a") as f:
            for as1, as2 in leg_edges:
                f.write(f"{as1} {as2}\n")
