import argparse
import bugzilla
import matplotlib.pyplot as plt
import sys
import textwrap
import yaml

from bugzilla.transport import BugzillaError
from cached_property import cached_property
from contextlib import contextmanager
from itertools import chain
from matplotlib.offsetbox import AnchoredText


class BugzillaData:
    """ Class representation of BZ Data, contains methods for plotting."""

    def __init__(self, query_file, url, plot_style, **kwargs):
        self.query_file = query_file
        self.bzapi = bugzilla.Bugzilla(url)
        self.plot_style = plot_style
        self.login_required = kwargs.get("login")
        self.credential_file = kwargs.get("credential_file")
        self.query = None
        self.queries = None
        # parse the query file
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
        # parse login info, if there is any
        try:
            with open(self.credential_file, "r") as stream:
                creds = yaml.load(stream, Loader=yaml.FullLoader)[0]
            self.creds = creds.get("login_info")
        except IOError:
            self.creds = None

    @contextmanager
    def logged_into_bugzilla(self):
        # login to bzapi
        if not self.creds:
            # error out if there are no creds available in yamls
            raise BugzillaError("No creds available to log into Bugzilla")
        try:
            yield self.bzapi.login(self.creds.get("username"), self.creds.get("password"))
        except BugzillaError:
            raise
        else:
            self.bzapi.logout()

    @cached_property
    def bugs(self):
        bugs = []
        if self.login_required:
            with self.logged_into_bugzilla():
                if self.queries:
                    for query in self.queries:
                        print(query)
                        bugs.extend(self.bzapi.query(query))
                else:
                    bugs.extend(self.bzapi.query(self.query))
        else:
            if self.queries:
                for query in self.queries:
                    print(query)
                    bugs.extend(self.bzapi.query(query))
            else:
                bugs.extend(self.bzapi.query(self.query))
        return bugs

    @property
    def title(self):
        title = "{status} BZ's sorted by {plot_style}"
        if self.queries:
            status = [query.get("status", "") for query in self.queries]
            status = list(dict.fromkeys(list(chain.from_iterable(status))))
        else:
            status = self.query.get("status", "")
        return title.format(
            status=", ".join(map(str, status)),
            plot_style=self.plot_style.capitalize()
        )

    @property
    def product(self):
        if self.queries:
            product = [query.get("product", "") for query in self.queries]
            product = list(dict.fromkeys(list(chain.from_iterable(product))))
        else:
            product = self.query.get("product", "")
        return ", ".join(map(str, product))

    def get_plot_data(self):
        bz_data = [getattr(bug, self.plot_style) for bug in self.bugs]
        bz_counts = {
            attr: bz_data.count(attr) for attr in bz_data
        }
        sorted_counts = sorted(bz_counts.items(), key=lambda item: item[1], reverse=True)
        xvals = range(len(sorted_counts))
        return xvals, sorted_counts

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


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-q", "--query", type=str, default="conf/query.yaml",
        help="Path to query yaml file"
    )
    parser.add_argument(
        "-p", "--plot", type=str, default="component",
        help=(
            "Plot bar chart for BZs found via <query> sorted according to one of: "
            "[component, qa_contact, assigned_to, creator]"
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
    parser.add_argument(
        "--output", action="store_true", default=False,
        help="Output bugzilla data from query to stdout"
    )
    parser.add_argument(
        "--login", action="store_true", default=False,
        help="Login to Bugzilla before making query. Required to use e.g. savedsearch and to get"
             "some hidden fields."
    )
    parser.add_argument(
        "--credential_file", type=str, default="conf/credentials.yaml",
        help="Path to credential yaml file"
    )
    args = parser.parse_args()
    # instantiate object
    bz_data = BugzillaData(
        args.query,
        args.url,
        args.plot,
        login=args.login,
        credential_file=args.credential_file
    )
    # print out info if necessary
    if args.output:
        for bug in bz_data.bugs:
            bug_string = """
                BZ {bug_id}:
                    reported_by: {creator}
                    summary: {summary}
                    status: {status}
                    qa_contact: {qa_contact}
                    assignee: {assigned_to}
            """.format(
                bug_id=bug.id,
                creator=getattr(bug, "creator", ""),
                summary=getattr(bug, "summary", ""),
                status=getattr(bug, "status", ""),
                qa_contact=getattr(bug, "qa_contact", ""),
                assigned_to=getattr(bug, "assigned_to", "")
            )
            print(textwrap.dedent(bug_string))
    # generate the plot
    bz_data.generate_plot(save=args.save)


if __name__ == "__main__":
    main()
