import argparse

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText

from bugzilla_data import BugzillaData as VanillaBugzillaData

# requires PyQt5
matplotlib.use("Qt5Agg")


class BugzillaData(VanillaBugzillaData):
    """ Inherit from base BugzillaData class to include plotting """

    def generate_plot(self, save=False):
        xvals, sorted_counts = self.get_plot_data()
        # create the figure
        fig, ax = plt.subplots()
        ax.bar(xvals, [s[1] for s in sorted_counts], align="center")
        plt.xticks(xvals, [s[0] for s in sorted_counts], rotation="vertical")
        plt.ylabel("BZ Count")
        plt.title(self.title)
        if self.product:
            ax.add_artist(AnchoredText(self.product, loc=1))
        plt.tight_layout()
        if save:
            plt.savefig("{}.png".format(self.plot_style))
        plt.show()


def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-q", "--query", type=str, default="conf/query.yaml", help="Path to query yaml file"
    )
    parser.add_argument(
        "-p",
        "--plot",
        type=str,
        default="component",
        help=(
            "Plot bar chart for BZs found via <query> sorted according to one of: "
            "[component, qa_contact, assigned_to, creator]"
        ),
    )
    parser.add_argument("-u", "--url", type=str, default="bugzilla.redhat.com", help="Bugzilla URL")
    parser.add_argument("--save", action="store_true", default=False, help="Save the plot")
    parser.add_argument(
        "--output",
        action="store_true",
        default=False,
        help="Output bugzilla data from query to stdout",
    )
    parser.add_argument(
        "--noplot", action="store_true", default=False, help="Do not generate any plot"
    )
    parser.add_argument(
        "--report", action="store_true", default=False, help="Generate a bz yaml file report"
    )
    parser.add_argument(
        "--login",
        action="store_true",
        default=False,
        help="Login to Bugzilla before making query. Required to use e.g. savedsearch and to get "
        "some hidden fields.",
    )
    parser.add_argument(
        "--credential_file",
        type=str,
        default="conf/credentials.yaml",
        help="Path to credential yaml file",
    )
    return parser.parse_args()


def main(args=None):
    args = args if args else get_args()
    args.output = True if args.noplot else args.output
    # instantiate object
    bz_data = BugzillaData(
        args.query, args.url, args.plot, login=args.login, credential_file=args.credential_file
    )
    # print out info if necessary
    if args.output:
        print(bz_data.generate_output())
    if args.report:
        bz_data.generate_report()
    # generate the plot
    if not args.noplot:
        bz_data.generate_plot(save=args.save)


if __name__ == "__main__":
    main()
