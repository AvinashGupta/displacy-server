Displacy: Dependency parse visualizer
=====================================

Displacy is a web application that allows you to visualise the output of
a syntactic dependency parser. It was written for [https://spacy.io](spaCy), and
doesn't currently support any other parsers. Pull request with support for
other parsing software would be very welcome.

The server is implemented as a Flask app, that both serves the static resources
for the front-end (i.e., the HTML, CSS and Javascript files), and provides
the spaCy parser as a REST service.

Install and run
---------------

```bash

git clone https://github.com/spacy-io/displacy-server
cd displacy-server
pip install -r requirements.txt
python application.py
```

Read more
---------

* [https://ines.io/blog/developing-displacy](Developing displacy), by @ines

* [http://spacy.io/blog/displacy-dependency-visualizer](Displaying linguistic structure) by @honnibal

Authors
-------

* @ines: Front-end

* @honnibal: NLP logic

* @henningpeters: Flask service
