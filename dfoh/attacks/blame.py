from dfoh import utils

LEVEL_MAX = 5


class Blamer:
    def __init__(self, attacker_folder):
        self.attacker_as = attacker_folder.split("_")[0]
        self.attacker_folder = attacker_folder
        self.topology = utils.load_topo()
        self.paths = utils.load_paths(self.attacker_as)

        self.paths = set([' '.join(
            [str(asn) for sublist in path for asn in sublist]) for path in self.paths])

        self.dir_folder = f"dfoh/data/{self.attacker_folder}"

        pass

    def run(self, file_name="blamed"):
        """
        Run the blame attack for the attacker AS.
        It runs for multiple path lengths, from 1 to LEVEL_MAX.
        """
        reached = []
        for i in range(1, LEVEL_MAX+1):
            self.visited = {}
            self.blamed = set()
            self.blame_rec(self.attacker_as, "", i)
            print(f"Level {i}: {len(self.blamed)}")
            reached.append(len(self.blamed))

        # write in self.folder/blamed.txt the array
        with open(f"{self.dir_folder}/{file_name}.txt", "w") as f:
            f.write("\n".join([str(x) for x in reached]))

    def run_with_hijacked(self):
        """
        Perform a blame attack using hijackable links, to make the attack more effective.
        """
        self.load_possible_links()

        links_to_use = self.possible_links[:100]
        top_links = {}

        print("Finding the best hijack link to add")
        for link in links_to_use:
            # check if the edge is in the topology
            self.topology.add_edge(self.attacker_as, link)
            self.visited = {}
            self.blamed = set()
            self.blame_rec(self.attacker_as, "", 1)
            top_links[link] = len(self.blamed)
            self.topology.remove_edge(self.attacker_as, link)

        # sort the links by the number of blamed ASes
        links_to_use = sorted(
            links_to_use, key=lambda x: top_links[x], reverse=True)
        links_to_use = links_to_use[:3]
        for link in links_to_use:
            self.topology.add_edge(self.attacker_as, link)

        self.run("blamed_hijacked")

        # remove the edges
        for link in links_to_use:
            self.topology.remove_edge(self.attacker_as, link)

    def blame_rec(self, as_n, path, level_max):
        level = len(path.split(" "))
        if level > level_max:
            return

        # pruning
        level_saved = self.visited.get(as_n, level+1)
        if level_saved <= level:
            return
        else:
            self.visited[as_n] = level

        for neighbor in self.topology.neighbors(as_n):

            # loop check
            phs = path.split(" ") if path != "" else []
            s = set(phs)
            if len(s) != len(phs):
                continue

            check = self.check_as(neighbor, path)
            if not check:
                continue

            p = f"{path} {neighbor}".strip()

            if neighbor not in self.blamed:
                self.blamed.add(neighbor)

            self.blame_rec(neighbor, p, level_max)

    def check_as(self, as_check, path):
        """
            Check if the path contains loops
        """
        p = f"{as_check} {path}"
        return self.filter_loops(self.paths, p)

    def filter_loops(self, paths: list[str], path_to_check: str) -> list[str]:
        ptc = set(path_to_check.split(' '))

        for p in paths:
            ases = set(p.split(' '))
            if not ases.intersection(ptc):
                return True

        return False

    def load_possible_links(self):
        self.possible_links = set()
        with open(f"{self.dir_folder}/0/parsed_results.txt", "r") as f:
            for line in f:
                if line.startswith("!leg"):
                    # !leg 200690 205218 10 0 10

                    linetab = line.rstrip().split(' ')
                    as1 = linetab[1]
                    as2 = linetab[2]

                    as_to_save = as1
                    if as1 == self.attacker_as:
                        as_to_save = as2
                    self.possible_links.add(as_to_save)

        # possible_link to ordered list by degree of as
        self.possible_links = sorted(
            list(self.possible_links),
            key=lambda x: self.topology.degree(x),
            reverse=True)
