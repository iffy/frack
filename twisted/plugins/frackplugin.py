# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
from twisted.application.service import ServiceMaker

Frack = ServiceMaker(
    "Frack",
    "frack.service",
    ("A parasite upon issue trackers."),
    "frack")
