import sys
import textwrap
from contextlib import contextmanager
from itertools import chain

import bugzilla
import yaml
from bugzilla.transport import BugzillaError
from cached_property import cached_property


class BugzillaData:
    """ Class representation of BZ Data, contains methods for plotting."""

    def __init__(self, query_file, url, plot_style, **kwargs):
        self.query_file = query_file
        self.bzapi = bugzilla.Bugzilla(url)
        self.plot_style = plot_style
        self.login_required = kwargs.get("login", False)
        self.creds = kwargs.get("credentials")
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
            if not self.creds and self.login_required:
                with open(self.credential_file, "r") as stream:
                    creds = yaml.load(stream, Loader=yaml.FullLoader)[0]
                self.creds = creds.get("login_info")
        except IOError:
            print("IOError: Credential file not present at {}".format(self.credential_file))

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

    def generate_output(self):
        bug_strings = []
        for bug in self.bugs:
            bug_strings.append(
                """
                BZ {bug_id}:
                    reported_by: {creator}
                    summary: {summary}
                    status: {status}
                    qa_contact: {qa_contact}
                    assignee: {assigned_to}
                    fixed_in: {fixed_in}
            """.format(
                    bug_id=bug.id,
                    creator=getattr(bug, "creator", ""),
                    summary=getattr(bug, "summary", ""),
                    status=getattr(bug, "status", ""),
                    qa_contact=getattr(bug, "qa_contact", ""),
                    assigned_to=getattr(bug, "assigned_to", ""),
                    fixed_in=getattr(bug, "fixed_in", ""),
                )
            )
        return textwrap.dedent("".join(bug_strings))

    def get_bug_info(self):
        for bug in self.bugs:
            # get rid of bugzilla object in dict repr
            bug.__dict__.pop("bugzilla")
        return [{bug.id: bug.__dict__} for bug in self.bugs]

    def generate_report(self, filename="bz-report.yaml"):
        """ Save a report on BZs to a yaml file """
        info = self.get_bug_info()
        with open(filename, "w") as outfile:
            yaml.dump(info, outfile, default_flow_style=False)
        return
