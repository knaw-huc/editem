# About

This describes the so-called **preview** workflow for previewing corpora during
development.
When editors are working on the corpus data (tei files, scans, additional
metadata) they want to preview
the published corpus every now and then.

# What is a preview

A preview involves:

1. retrieve the input data (scans, tei, metadata) (only the parts that have changed)
1. run all conversions (TEI => TF => WATM + IIIF)
1. ingest the WATM into TextRepo and AnnoRepo
1. create the search indexes (via Broccoli)
1. restart the k8s deployment

# Upfront actions

For each corpus, we do certain upfront actions

1.  we organize a directory to store all files relevant for the conversion steps
1.  we create a k8s deployment to serve the IIIF manifests and the page images
1.  we set up configuration files for the ingest of the WATM
1.  we set up configuration files for Broccoli
1.  we create a k8s deployment for the corpus website

# Conventions

1.  every corpus is identified by a unique string, consisting of 2 parts
    separated by a `/`, e.g.

	*   `HuygensING/suriano`
	*   `HuygensING/translatin`
	*   `van-gogh/letters`

	The first part is the *org*, the second part is the *repo*.

    It is assumed that the files of the corpus reside in a directory below the
    home directory as follows:

	`~` `/` *backend* `/` *org* `/` *repo*

	where *backend* is one of 

	*   `github` (the real GitHub at github.com)
	*   `gitlab` (the real GitLab at gitlab.com)
	*   `gitlab.huc.knaw.nl` (DI on-premise public-facing gitlab)
	*   `code.huc.knaw.nl` (DI on-premise protected gitlab)

2.  the urls for a corpus all have the following shape:

	```
    editem.huc.knaw.nl/` *org* `/` *repo* `/` *command* *command-dependent-stuff*
    ```

	The following commands are possible:

	*   `run`: trigger the execution of the preview workflow for this corpus
    *   `status`: retrieve the the status of the workflow (indicates which
        processing step is going on, and if the workflow has ended, reports
        success, success with warnings, or failure)
    *   `log`: the complete log of the current or latest workflow run: a list
        of messages with a severity indication (info, warning, error, special)
    *   `report`: entry to various report files generated during the execution
        of the workflow (e.g. validation errors, element statistics, link
        reports, custom checks)
	*   `annorepo`: access annotations in AnnoRepo
	*   `textrepo`: access text fragments in TextRepo
	*   `broccoli`: access Broccoli
	*   `tav` : entry to the published-for-preview corpus (the TAV interface)

# The workflow system

Now we can take a step back and see what the workflow system is supposed to do for us:

1.  one can add corpora to the system (which involves pointing to an input
    directory and configuring a deployment on k8s and writing additional corpus
    dependent config files)
1.  users can then start the execution of a preview run. In this run the input
    is converted to a TAV website
1.  users can get information about the workflow run, its results, logs and reports
1.  users can then use the TAV website for actually previewing the resulting site

# Operation of the workflow

When it comes to adding a new corpus to the preview system, people of Team Text
have to do certain manual actions. They will talk to the content specialist
(Peter Boot) and put the TEI schema variant in place, set parameters that
regulate the conversion TEI-TF-WATM. They may have to write additional checks
and conversions having to do with metadata, page numbers, link checking, and
whatever is important for the corpus in question.

When the corpus is set up, the workflow can be triggered by commands: on the
command line and over the web.

In order to support the web commands, a controller website would be handy that
lists the corpora that have been set up, and shows the latest preview run, its
success, with links to report files and logs.

This web interface is then meant for editors: we should implement a basic
system that authorises editors to run the workflow for the corpora they are
working on.

Team Text people can also run the workflow from the command line, and even in a
Jupyter notebook. These ways of operating are needed for debugging, especially
when additional corpus-dependent checks need to be written.

The idea is that the workflow for a single corpus can be followed by a Jupyter
notebook in the programs directory of that corpus. Ideally, such notebooks can
also be run on the local computer of the developer, in a clone of the repo that
hosts the corpus files.
