Dependency Parse Tree Visualization with CSS & JavaScript
=========================================================

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

* [Developing displacy](https://ines.io/blog/developing-displacy), by [@ines](https://github.com/ines)

* [Displaying linguistic structure](http://spacy.io/blog/displacy-dependency-visualizer) by [@honnibal](https://github.com/honnibal)

Authors
-------

* [@ines](https://github.com/ines): Front-end

* [@honnibal](https://github.com/honnibal): NLP logic

* [@henningpeters](https://github.com/henningpeters): Flask service
