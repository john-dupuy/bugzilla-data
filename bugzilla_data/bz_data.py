import sys
from contextlib import contextmanager
from itertools import chain

import bugzilla
import matplotlib.pyplot as plt
import yaml
from bugzilla.transport import BugzillaError
from cached_property import cached_property
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
                    self.queries = [query["query"] for query in queries]
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
                        bugs.extend(self.bzapi.query(self.bzapi.build_query(**query)))
                else:
                    bugs.extend(self.bzapi.query(self.bzapi.build_query(**self.query)))
        else:
            if self.queries:
                for query in self.queries:
                    bugs.extend(self.bzapi.query(self.bzapi.build_query(**query)))
            else:
                bugs.extend(self.bzapi.query(self.bzapi.build_query(**self.query)))
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
            status=", ".join(map(str, status)), plot_style=self.plot_style.capitalize()
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
        bz_counts = {attr: bz_data.count(attr) for attr in bz_data}
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
