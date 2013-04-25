# -*- mode: org -*-

Frack, A Completely Ridiculous Issue Tracker
============================================

This was written because twistedmatrix.com has a Trac instance full of
valuable data, and Trac has become increasingly annoying over the past
7 years. Frack is an attempt to provide a better face on that data.


How It Works
------------
Right now, it's just a normal website (like from the 90s) for interacting with
Trac tickets.


How To Run It
-------------

If you want to develop Frack, the tests can be run via 'trial frack.test'. For
running a development server:


Install the packages listed in `requirements.txt`

    pip install -r requirements.txt


Load some test data into an sqlite db

    sqlite3 < frack/test/trac_test.sql trac.db


Start the server (the URL here must be the url at which you will access the site)

    twistd -n frack --baseUrl=http://localhost:1353/ --sqlite_db=trac.db


Authentication is done with Persona


To create a new ticket go to:

    http://localhost:1353/tickets/newticket


To view existing tickets go to:

    http://localhost:1353/tickets/ticket/<ticket_number>


Ticket numbers in the test database are: `3312`, `5622`, `5517`, `2723`, `4712`.
