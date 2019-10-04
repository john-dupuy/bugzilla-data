import argparse
import textwrap

from bugzilla_data import BugzillaData


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
        for bug in bz_data.bugs:
            bug_string = """
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
            print(textwrap.dedent(bug_string))
    # generate the plot
    if not args.noplot:
        bz_data.generate_plot(save=args.save)


if __name__ == "__main__":
    main()
