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

import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
from supybot import world

from git import Repo
import time
import threading

class GitHistoryChannelLogger(callbacks.Plugin):
    threaded = True

    def __init__(self, irc):
        self.__parent = super(GitHistoryChannelLogger, self)
        self.__parent.__init__(irc)
        self.repos = {}
        self.loadRepos()
        self.startCommitWatcher()

    def loadRepos(self):
        repos_config = self.registryValue('repos')
        for repo in repos_config:
            url = self.registryValue(f'{repo}.url')
            branch = self.registryValue(f'{repo}.branch')
            channels = self.registryValue(f'{repo}.channels')
            self.repos[repo] = {
                'url': url,
                'branch': branch,
                'channels': channels
            }

    def startCommitWatcher(self):
        self.commit_watcher = threading.Thread(target=self.watchCommits)
        self.commit_watcher.daemon = True
        self.commit_watcher.start()

    def watchCommits(self):
        while True:
            for repo, config in self.repos.items():
                self.checkCommits(repo, config)
            time.sleep(60)

    def checkCommits(self, repo, config):
        repo_path = config['url']
        branch = config['branch']
        channels = config['channels']

        try:
            repo = Repo(repo_path)
            commits = list(repo.iter_commits(branch, max_count=5))
            for commit in commits:
                message = f"[{repo}] {commit.hexsha[:7]} - {commit.author.name}: {commit.message.strip()}"
                self.logCommit(channels, message)
        except Exception as e:
            self.log.error(f"Error checking commits for repo {repo}: {e}")

    def logCommit(self, channels, message):
        for irc in world.ircs:
            for channel in channels:
                if channel in irc.state.channels:
                    irc.queueMsg(ircmsgs.privmsg(channel, message))

Class = GitHistoryChannelLogger

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
