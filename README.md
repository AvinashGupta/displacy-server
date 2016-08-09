Dependency Parse Tree Visualization with CSS & JavaScript
=========================================================

displaCy is a web application that allows you to visualise the output of
a syntactic dependency parser. It was written for [https://spacy.io](spaCy), and
doesn't currently support any other parsers. Pull request with support for
other parsing software would be very welcome.

The server is implemented as a Flask app, that both serves the static resources
for the front-end (i.e., the HTML, CSS and Javascript files), and provides
the spaCy parser as a REST service.

This is a fairly small and specific code-base, that was written in quite a hurry,
and now feels rather old. However, it makes the spaCy dependency parser significantly
easier to use. I usually use it as a sort of manual-by-example. Instead of a long document
describing the parser's target annotations, I type in simple sentences and look at the
predicted annotations.

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

* [Developing displaCy](https://ines.io/blog/developing-displacy), by [@ines](https://github.com/ines)

* [Displaying linguistic structure](http://spacy.io/blog/displacy-dependency-visualizer) by [@honnibal](https://github.com/honnibal)

Authors
-------

* [@ines](https://github.com/ines): Front-end

* [@honnibal](https://github.com/honnibal): NLP logic

* [@henningpeters](https://github.com/henningpeters): Flask service
