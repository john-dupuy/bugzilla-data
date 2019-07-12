import argparse
import bugzilla
import matplotlib.pyplot as plt
import sys
import yaml

from cached_property import cached_property
from itertools import chain
from matplotlib.offsetbox import AnchoredText


class BugzillaData:
    """ Class representation of BZ Data, contains methods for plotting."""

    def __init__(self, query_file, url):
        self.query_file = query_file
        self.bzapi = bugzilla.Bugzilla(url)
        self.query = None
        self.queries = None
        try:
            with open(self.query_file, "r") as stream:
                queries = yaml.load(stream, Loader=yaml.FullLoader)
                if len(queries) > 1:
                    self.queries = [
                        query["query"] for query in queries
                    ]
                else:
                    self.query = queries[0].get("query")
        except IOError:
            print("IOError: Query file not present at {}, exiting...".format(self.query_file))
            sys.exit(1)

    @cached_property
    def bugs(self):
        bugs = []
        if self.queries:
            for query in self.queries:
                print(query)
                bugs.extend(self.bzapi.query(query))
        else:
            bugs.extend(self.bzapi.query(self.query))
        return bugs

    @property
    def title(self):
        title = "{status} BZ's"
        if self.queries:
            status = [query.get("status", "") for query in self.queries]
            status = list(dict.fromkeys(list(chain.from_iterable(status))))
        else:
            status = self.query.get("status", "")
        return title.format(status=", ".join(map(str, status)))

    @property
    def product(self):
        if self.queries:
            product = [query.get("product", "") for query in self.queries]
            product = list(dict.fromkeys(list(chain.from_iterable(product))))
        else:
            product = self.query.get("product", "")
        return ", ".join(map(str, product))

    def get_plot_data(self, plot_style):
        bz_data = [getattr(bug, plot_style) for bug in self.bugs]
        bz_counts = {
            attr: bz_data.count(attr) for attr in bz_data
        }
        sorted_counts = sorted(bz_counts.items(), key=lambda item: item[1], reverse=True)
        xvals = range(len(sorted_counts))
        return xvals, sorted_counts

    def generate_plot(self, plot_style, save=False):
        xvals, sorted_counts = self.get_plot_data(plot_style)
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
            plt.savefig("{}.png")
        plt.show()


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-q", "--query", type=str, default="conf/query.yaml",
        help="Path to query yaml file"
    )
    parser.add_argument(
        "-p", "--plot", type=str, default="component",
        help=(
            "Plot bar chart for BZs found via <query> according to one of: "
            "[component, qa_contact]"
        )
    )
    parser.add_argument(
        "-u", "--url", type=str, default="bugzilla.redhat.com",
        help="Bugzilla URL"
    )
    parser.add_argument(
        "--save", action="store_true", default=False,
        help="Save the plot"
    )
    args = parser.parse_args()
    # instantiate object
    bz_data = BugzillaData(args.query, args.url)
    # generate the plot
    bz_data.generate_plot(args.plot, save=args.save)


if __name__ == "__main__":
    main()
