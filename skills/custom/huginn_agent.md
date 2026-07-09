---
name: huginn_agent
version: '0.1'
category: experimental
status: active
triggers:
- track the weather
- list terms that you care about
- watch for air travel or shopping deals
- follow your project names on Twitter and get updates when people mention them
- scrape websites and receive email when they change
- connect to HipChat, FTP, IMAP, Jabber, JIRA, MQTT, nextbus, Pushbullet, Pushover,
  RSS, Bash, Slack, StubHub, translation APIs, Twilio, Twitter, and Weibo
- send digest email with things that you care about at specific times during the day
- track counts of high frequency events and send an SMS within moments when they spike
- send and receive WebHooks
- run custom JavaScript functions
- track your location over time
- create Amazon Mechanical Turk workflows as the inputs, or outputs, of agents (the
  Amazon Turk Agent is called the "HumanTaskAgent")
command: python3 /home/junaid-eko/cortex/scripts/synthesized/huginn_agent.py {query}
ram_mb: 512
requires: []
install_command: git clone https://github.com/huginn/huginn.git
source_repo: huginn
source_url: https://github.com/huginn/huginn
synthesized_at: '2026-06-28T17:58:17.867475'
---
# Huginn Agent Skill

Huginn is a system for building agents that perform automated tasks for you online. They can read the web, watch for events, and take actions on your behalf. Huginn's Agents create and consume events, propagating them along a directed graph. Think of it as a hackable version of IFTTT or Zapier on your own server. You always know who has your data. You do.

**Source repo:** [huginn](https://github.com/huginn/huginn)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/huginn_agent.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.
