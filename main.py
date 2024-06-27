from config import Config
from dfoh.attacks.add_links import AddLinkAttack
from dfoh.attacks.blame import Blamer
from dfoh.plots.blame import BlamePlot
from dfoh.plots.hijack import HijackPlot
from beam.threshold_pollution import ThresholdPollution
import os
import click


def startup_checks():

    # check that Config.DFOH_TEMP_DIR exists
    if not os.path.exists(Config.DFOH_TEMP_DIR):
        os.makedirs(Config.DFOH_TEMP_DIR)

    # check that dfoh/data exists
    if not os.path.exists("dfoh/data"):
        os.makedirs("dfoh/data")

    # if Config.DFOH_DB_DIR does exists, backup the current topology
    tpl_fld = f"{Config.DFOH_DB_DIR}/merged_topology/{Config.DATE_EXPERIMENT}.txt"
    bkp_fld = f"dfoh/data/topology-{Config.DATE_EXPERIMENT}.bkp"
    if os.path.exists(Config.DFOH_DB_DIR) and os.path.exists(tpl_fld) and \
            not os.path.exists(bkp_fld):
        os.system(f"cp {tpl_fld} {bkp_fld}")


@click.group()
def cli():
    pass


@cli.group()
def dfoh():
    pass


@dfoh.command()
@click.argument('attacker_as', type=str)
@click.option('--max_runs', default=5, help='Maximum number of runs per attacker.')
def run_single_attacker(attacker_as, max_runs):
    """
    Run the attack for a single attacker.

    ATTACKER_AS is the AS number of the attacker.
    """
    cls = AddLinkAttack()
    cls.run_single_attacker(attacker_as, max_runs)


@dfoh.command()
@click.argument('country', type=str)
@click.option('--max_runs', default=5, help='Maximum number of runs per attacker.')
def run_country(country, max_runs):
    """
    Run the attack for a COUNTRY, with 3 different attackers.

    COUNTRY is a 2-letter code, e.g., 'BR' for Brazil.
    """
    cls = AddLinkAttack()
    cls.run_country_diff_degrees(country, max_runs)


@dfoh.command()
@click.argument('attacker_as_folder', type=str)
@click.option("--hijacked", is_flag=True, help="Use hijacked links.")
def blame(attacker_as_folder, hijacked):
    """
    Run the blame attack for the attacker AS.

    ATTACKER_AS_FOLDER is the folder of the attacker AS in dfoh/data.
    """
    if not os.path.exists(f"dfoh/data/{attacker_as_folder}"):
        raise ValueError(f"Folder {attacker_as_folder} does not exist.")

    cls = Blamer(attacker_as_folder)
    if hijacked:
        cls.run_with_hijacked()
    else:
        cls.run()


@dfoh.group()
def plot():
    pass


@plot.command(name="blame")
def pblame():
    """
    Plot the blame attack results.
    """
    cls = BlamePlot()
    cls.plot()


@plot.command(name="hijack")
def phijack():
    """
    Plot the hijack attack results.
    """
    cls = HijackPlot()
    cls.plot()


@cli.group()
def beam():
    pass


@beam.command()
def pollution():
    """
    Run the BEAM pollution attack.
    """
    cls = ThresholdPollution()
    cls.pollute()


if __name__ == "__main__":
    startup_checks()
    cli()
