# jenkins-export

Export Jenkins job configurations into a single text file so you can search across jobs (for example with `grep` or your editor) for build steps, triggers, or other settings.

## Requirements

- Python 3
- [`requests`](https://pypi.org/project/requests/)

Install dependencies:

```bash
pip install requests
```

Your Jenkins user must be allowed to list jobs and read each job’s `config.xml` (typical for admins or users with Job/Read permissions).

## How to run

From this repository:

```bash
python jenkins_export.py
```

The script is interactive. It will ask for:

1. **Jenkins URL** — Base URL of the controller, e.g. `https://jenkins.example.com` or `http://localhost:8080` (no trailing slash required).
2. **Authentication** — Answer `y` if the server requires login, otherwise `n`.
3. If you chose `y`: **username** and **API token or password** — Prefer a [Jenkins API token](https://www.jenkins.io/doc/book/security/user-api-token/) over your account password when possible.

It then downloads every job’s configuration, extracts triggers and build steps where it can, and appends a short slice of the raw XML per job.

Progress is printed in the terminal (job count and current job name).

## Output

A new file is created in the **current working directory**:

`jenkins_configs_YYYYMMDD_HHMMSS.txt`

Open it in an editor or search from the shell, for example:

```bash
grep -i "some-pattern" jenkins_configs_*.txt
```

The file includes, per job: triggers (timer, poll SCM, cron where recognized), build steps (shell, batch, trigger downstream job, etc.), plus the first 50 lines of each job’s XML config for deeper inspection.

## Troubleshooting

- **401 / 403** — Check URL, user, and token/password; confirm the account can access the jobs API and each job’s config.
- **Empty or partial results** — Some job types use plugins whose XML does not match the patterns this script parses; use the embedded XML snippet or Jenkins UI for those jobs.
- **Connection errors** — Confirm the URL is reachable from your machine (VPN, firewall, correct scheme `http` vs `https`).
