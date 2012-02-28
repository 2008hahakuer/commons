# ==================================================================================================
# Copyright 2012 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

__author__ = 'John Sirois'

import textwrap

import os

from twitter.common.confluence import Confluence, ConfluenceError
from twitter.common.dirutil import safe_open

from twitter.pants.targets import Page
from twitter.pants.tasks import Task, TaskError
from twitter.pants.tasks import binary_utils

class ConfluencePublish(Task):

  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    option_group.add_option(mkflag("url"), dest="confluence_publish_url",
                            help="The url of the confluence site to post to.")

    option_group.add_option(mkflag("force"), mkflag("force", negate=True),
                            dest = "confluence_publish_force",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Force publish the page even if its contents is "
                                   "identical to the contents on confluence.")

    option_group.add_option(mkflag("open"), mkflag("open", negate=True),
                            dest="confluence_publish_open", default=False,
                            action="callback", callback=mkflag.set_bool,
                            help="[%default] Attempt to open the published confluence wiki page "
                                 "in a browser.")

  def __init__(self, context):
    Task.__init__(self, context)

    self.url = (
      context.options.confluence_publish_url
      or context.config.get('confluence-publish', 'url')
    )

    self.force = context.options.confluence_publish_force
    self.open = context.options.confluence_publish_open
    self.context.products.require('markdown_html')

  def wiki(self):
    raise NotImplementedError('Subclasses must provide the wiki target they are associated with')

  def execute(self, targets):
    try:
      wiki = Confluence.login(self.url)
    except ConfluenceError as e:
      raise TaskError('Failed to login to confluence: %s' % e)

    urls = list()

    genmap = self.context.products.get('markdown_html')
    for page in filter(lambda t: isinstance(t, Page), targets):
      wikiconfig = page.wiki_config(self.wiki())
      if wikiconfig:
        html_info = genmap.get((self.wiki(), page))
        if len(html_info) > 1:
          raise TaskError('Unexpected resources for %s: %s' % (page, html_info))
        basedir, htmls = html_info.items()[0]
        if len(htmls) != 1:
          raise TaskError('Unexpected resources for %s: %s' % (page, htmls))
        with safe_open(os.path.join(basedir, htmls[0])) as contents:
          url = self.publish_page(
            wiki,
            wikiconfig['space'],
            wikiconfig['title'],
            contents.read(),
            parent=wikiconfig.get('parent')
          )
          if url:
            urls.append(url)
            self.context.log.info('Published %s to %s' % (page, url))

    if self.open and urls:
      binary_utils.open(*urls)

  def publish_page(self, wiki, space, title, content, parent=None):
    body = textwrap.dedent('''
    {html}
    %s
    {html}
    ''').strip() % content

    pageopts = dict(
      versionComment = 'updated by pants!'
    )
    existing = wiki.getpage(space, title)
    if existing:
      if not self.force and existing['content'].strip() == body.strip():
        self.context.log.warning("Skipping publish of '%s' - no changes" % title)
        return

      pageopts['id'] = existing['id']
      pageopts['version'] = existing['version']

    try:
      page = wiki.create(space, title, body, parent, **pageopts)
      return page['url']
    except ConfluenceError as e:
      raise TaskError('Failed to update confluence: %s' % e)
