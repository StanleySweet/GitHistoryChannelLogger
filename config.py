###
# Copyright (c) 2024, Stanislas Daniel Claude Dolcini
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

from supybot import conf, registry

def configure(advanced):
    conf.registerPlugin('GitHistoryChannelLogger', True)

GitHistoryChannelLogger = conf.registerPlugin('GitHistoryChannelLogger')

conf.registerGlobalValue(GitHistoryChannelLogger, 'repos',
        registry.SpaceSeparatedListOfStrings([], """Channels to log commits to."""))

# Register dynamic configuration for repositories
def registerRepo(name):
    group = conf.registerGroup(GitHistoryChannelLogger, name)
    conf.registerGlobalValue(group, 'url',
        registry.String('', """URL of the repository."""))
    conf.registerGlobalValue(group, 'branch',
        registry.String('master', """Branch to track."""))
    conf.registerGlobalValue(group, 'channels',
        registry.SpaceSeparatedListOfStrings([], """Channels to log commits to."""))
    conf.registerGlobalValue(group, 'sleepTime',
        registry.NonNegativeInteger(30, "Wait for this many seconds between checks."))

# Register existing repositories from configuration
repos = GitHistoryChannelLogger.repos()
for repo in repos:
    registerRepo(repo)

GitHistoryChannelLogger.repos.addCallback(registerRepo)
