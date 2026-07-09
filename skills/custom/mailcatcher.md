---
name: mailcatcher
version: '0.1'
category: experimental
status: active
triggers:
- mailcatcher
- catch mail
- test email delivery
- smtp server
command: python3 /home/junaid-eko/cortex/scripts/synthesized/mailcatcher.py {query}
ram_mb: 50
requires:
- ruby
source_repo: mailcatcher
source_url: https://github.com/sj26/mailcatcher
synthesized_at: '2026-06-27T11:34:30.286857'
---
# Mailcatcher Skill

MailCatcher is a simple SMTP server that intercepts all emails sent to it and provides a web interface to view them. It's useful for testing email functionality in development environments and debugging SMTP issues without needing an external mail server. It does not send actual emails, but instead acts as a local inbox for incoming messages. All interactions after starting the server happen via its web interface.

**Source repo:** [mailcatcher](https://github.com/sj26/mailcatcher)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/mailcatcher.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.
