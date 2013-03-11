#!/bin/bash
# cribbed from csnover's Dojo Boilerplate project. Provided under the dojo license:
# Copyright (c) 2005-2006, The Dojo Foundation
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#   * Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   * Neither the name of the Dojo Foundation nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
set -e

# Base directory for this entire project
BASEDIR=$(cd $(dirname $0) && pwd)

# Source directory for unbuilt code
SRCDIR="$BASEDIR/webclient"

# Directory containing dojo build utilities
TOOLSDIR="$SRCDIR/util/buildscripts"

# Destination directory for built code
DISTDIR="$BASEDIR/dist"

# Module ID of the main application package loader configuration
LOADERMID="frack/run"

# Main application package loader configuration
LOADERCONF="$SRCDIR/$LOADERMID.js"

# Main application package build configuration
PROFILE="$SRCDIR/frack/frack.profile.js"

# Configuration over. Main application start up!

if [ ! -d "$TOOLSDIR" ]; then
    echo "Can't find Dojo build tools -- did you initialise submodules? (git submodule update --init --recursive)"
    exit 1
fi

echo "Building application with $PROFILE to $DISTDIR."

echo -n "Cleaning old files..."
rm -rf "$DISTDIR"
echo " Done"

cd "$TOOLSDIR"

if which node >/dev/null; then
    node ../../dojo/dojo.js load=build --require "$LOADERCONF" --profile "$PROFILE" --releaseDir "$DISTDIR" "$@"
elif which java >/dev/null; then
    java -Xms256m -Xmx256m  -cp ../shrinksafe/js.jar:../closureCompiler/compiler.jar:../shrinksafe/shrinksafe.jar org.mozilla.javascript.tools.shell.Main  ../../dojo/dojo.js baseUrl=../../dojo load=build --require "$LOADERCONF" --profile "$PROFILE" --releaseDir "$DISTDIR" "$@"
else
    echo "Need node.js or Java to build!"
    exit 1
fi

cd "$BASEDIR"

LOADERMID=${LOADERMID//\//\\\/}

# Copy & minify index.html to dist
cat "$SRCDIR/ticket.html" | tr '\n' ' ' | \
perl -pe "
  s/<\!--.*?-->//g;                          # Strip comments
  s/isDebug: *1/deps:['$LOADERMID']/;        # Remove isDebug, add deps
  s/<script src=\"$LOADERMID.*?\/script>//;  # Remove script app/run
  s/\s+/ /g;                                 # Collapse white-space" > "$DISTDIR/ticket.html"

echo "Build complete"
