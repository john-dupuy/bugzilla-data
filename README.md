Bugzilla - Data
===============
A tool for visualizing Bugzilla data via component, product, assginee, qa_contact, etc.
Right now, this tool generates bar charts of Bugzilla bugs.
The charts can be sorted according to e.g. bug component, assignee, qa_contact, etc.
The charts will automatically be sorted from highest to lowest. This is the image generated
from the example query yaml (`conf/query.yaml`).

![Alt text](images/example1.png?raw=true)

Getting started
---------------

The basics of using this tool is as simple as,
1) Creating and activating a python 3 virtual environment
2) `pip install -e .`
3) Running `python scripts/make_plot.py`

The allowed parameters to `make_plot.py`  are:
```
usage: make_plot.py [-h] [-q QUERY] [-p PLOT] [-u URL] [--save] [--output]
                  [--login] [--credential_file CREDENTIAL_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -q QUERY, --query QUERY
                        Path to query yaml file (default: conf/query.yaml)
  -p PLOT, --plot PLOT  Plot bar chart for BZs found via <query> sorted
                        according to one of: [component, qa_contact,
                        assigned_to, creator] (default: component)
  -u URL, --url URL     Bugzilla URL (default: bugzilla.redhat.com)
  --save                Save the plot (default: False)
  --output              Output bugzilla data from query to stdout (default:
                        False)
  --login               Login to Bugzilla before making query. Required to use
                        e.g. savedsearch and to get some hidden fields.
                        (default: False)
  --credential_file CREDENTIAL_FILE
                        Path to credential yaml file (default:
                        conf/credentials.yaml)

```
To effectively use this tool, you must define meaningful queries in `conf/query.yaml`.

You can define
 any number of queries within you query file. Each simply must start with `- query:`.


 A simple example query which fetches `NEW` BZ's for Red Hat Cloudforms is provided,
 but these can be much more complicated. For example, you can fetch according to specific users
 who created/reported the BZ via
 ```yaml,
 - query:
    product:
        - Red Hat CloudForms Management Engine
    status:
        - ON_QA
        - NEW
        - POST
        - CLOSED
    include_fields:
        - id
        - summary
        - component
        - description
        - status
        - qa_contact
        - creator
        - assigned_to
        - version
    reporter:
        - <email1>
        - <email2>
        - <email3>
 ```
 You can also search by `qa_contact` or `assigned_to` and then generate plots according to
 these users. More information about the queries can be found at:
 https://github.com/python-bugzilla/python-bugzilla,
as this is the API that is used for bugzilla queries. Note that the `include_fields` list is
not necessary, and can be commented out if you run into attribute errors in the program call.
It can speed up your query if you're dealing with a large number of BZs, since `python-bugzilla`
will only fetch those specific fields.

**Another neat feature** of `python-bugzilla` is the ability to login to Bugzilla and use
a search saved under your login rather than formulating your own query. To do so, create a
credentials file in `conf/credentials.yaml`, with the following content:
```yaml,
- login_info:
    username: <your_bz_username>
    password: <your_bz_password>
```
For the query, you can have the following in `conf/query.yaml`:
```yaml,
- query:
    savedsearch: My Bugs # just an example, can be the name of any search defined in your Bugzilla
```
Then run the script passing the `--login` so the script knows that a login is required.
```
python scripts/make_plot.py --login
```
