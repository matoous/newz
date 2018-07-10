# News

### Project structure

* views - Views handling functions
* models - Models and forms
* config - Configuration and application setup
* lib - Various utilities, almost everything is here
* scripts - Scripts which shell be run separatly
* static - Css, Js, Fonts and Images
* templates - Templates, obviously

If you want to hop in I recommend going through models and views first, If anything is unclear or hidden
under some function it will probably be in lib where almost everything is.

### Models

Most models extend Base which is wrapper around Model from Orator library and provides base functions
for DB access and caching. If anything is unclear it can most likely be found on [Orator docs](https://orator-orm.com/)
or in Base model.

Everything is heavily cached so all changes are written to DB and also to Redis which is considered
a second source of truth. To access the cache and perform modifications to existing objects try to use
as much from Base model as possible and be really careful when creating model-specific functions.

### Views

We try to keep views as simple as possible and also human readable. Models and lib should handle most
things and views just use function provided by these components.

Function should be named by method name + underscore + what thay do, e.g.: get_feed_links or post_new_link

### Things that are persisted in redis and need special care

* votes (there's load_votes function in scripts in case the votes need to be re-fetched)
* bans

### Instalation

Minimal requirements: Python3.6 and PostgreSQL

Instalation:

### Tech stack

* PostgreSQL
* Python3.6 (Flask)
* Gunicorn
* Redis - [Info here](https://redis.io/)
* Apache Solr - [Info here](http://lucene.apache.org/solr/)
* StatsD - [Info here](https://github.com/statsite/statsite), 
            [Python Client](http://statsd.readthedocs.io/en/v3.2.2/index.html)
* Graphite - [Info here](https://graphite.readthedocs.io/en/latest/index.html)
* Sentry - [Info here](https://sentry.io/)
* Administration - https://cockpit-project.org/


### More
[Kube CSS](https://imperavi.com/kube/docs/messages/)  
[Configuring PostgreSQL](http://thebuild.com/presentations/not-your-job.pdf)

### TODO list
* archive links after month
* update scores in solr
* fix feed description and look
* implement 'delete account'
* user preferences
* feed images
* reports - remove, act etc.