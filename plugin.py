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

from git import Repo
import time
import os
import threading

class GitHistoryChannelLogger(callbacks.Plugin):
    threaded = True
    def __init__(self, irc):
        self.__parent = super(GitHistoryChannelLogger, self)
        self.__parent.__init__(irc)
        self.repos = {}
        self.loadRepos()
        self.syncedChannels = []
        self.shouldStop = False
        self.commit_watcher = None

    def do315(self, irc, msg):

        print("do315 in ", msg.args[1])
        print("current channels:", irc.state.channels.items())

        self.syncedChannels.append(msg.args[1])

        # Don't send messages before all channels were synced
        for (channel, _) in irc.state.channels.items():
            if channel not in self.syncedChannels:
                return

        print("Git History - all channels synced", msg.args[1])

        # Notify about recent phabricator stories
        if self.commit_watcher:
            print("thread still already running")
            return

        self.commit_watcher = threading.Thread(target=self.watchCommits, args=(irc,), daemon=True)
        self.commit_watcher.start()

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

    def watchCommits(self, irc):
        while not self.shouldStop:
            for repo, config in self.repos.items():
                self.checkCommits(repo, config, irc)
            time.sleep(self.registryValue(f'{repo}.sleepTime'))


    def die(self):
        self.log.info("Killing GitHistoryChannelLogger bot.")
        if self.commit_watcher is not None:
            self.shouldStop = True
            self.commit_watcher.join()
        self.__parent.die()

    def checkCommits(self, repo, config, irc):
        repo_path = config['url']
        branch = config['branch']
        channels = config['channels']

        try:
            localRepo = Repo(repo_path)
            o = localRepo.remotes.origin
            o.pull()
            if branch not in localRepo.branches:
                self.log.info(f"Branch '{branch}' does not exist.")
                return

            commits = list(localRepo.iter_commits(branch, max_count=5))
            commits.reverse()
            if(len(commits) == 0):
                self.log.info(f"No commits found for repo {repo}")
                return
            
            if(commits[0].hexsha == self.__loadHash(repo, branch)):
                self.log.info(f"No new commits found for repo {repo}")
                return

            for commit in commits:
                author = u"\u200B".join(list(commit.author.name))
                clean_message = commit.message.strip().replace('\n', ' ')
                message = f"News from the Wiki by {author}: {clean_message}"
                for channel in channels:
                    irc.queueMsg(ircmsgs.privmsg(channel, message))

            self.__saveHash(repo, branch, commits[0].hexsha)

        except Exception as e:
            self.log.error("An error occurred when logging commits: %s", e, exc_info=True)

    def __loadHash(self, repo, branch):
        if not os.path.isfile(f"{repo}.{branch}.txt"):
            print(f"{repo}.{branch}.txt", "not found, starting at 0")
            return "0"

        return open(f"{repo}.{branch}.txt", 'r').read().strip()

    def __saveHash(self, repo, branch, hash):

        self.log.info(f"Saving hash '{hash}' in {repo}.{branch}.txt")
        text_file = open(f"{repo}.{branch}.txt", "w")
        text_file.write(str(hash) + "\n")
        text_file.close()

Class = GitHistoryChannelLogger

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
