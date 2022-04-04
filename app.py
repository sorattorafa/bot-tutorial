import os
from flask import Flask, request
from github import Github, GithubIntegration

app = Flask(__name__)

app_id = '186915'

# Read the bot certificate
with open(
        os.path.normpath(os.path.expanduser('bot-example.2022-04-04.private-key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()
    
# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)

def pr_opened_event(repo, payload):
    pr = repo.get_issue(number=payload['pull_request']['number'])
    author = pr.user.login

    is_first_pr = repo.get_issues(creator=author).totalCount

    if is_first_pr == 1:
        response = f"Thanks for opening this pull request, @{author}! " \
                   f"The repository maintainers will look into it ASAP! :speech_balloon:"
        pr.create_comment(f"{response}")
        pr.add_to_labels("needs review")

def pr_closed_event(repo, payload):
    pr = repo.get_issue(number=payload['pull_request']['number'])
    author = pr.user.login

    merged_by = payload['pull_request']['merged_by']['login']

    #is_first_pr = repo.get_issues(creator=author).totalCount
    is_merged_pr = payload['pull_request']['merged']
    if is_merged_pr == True:
        response = f"Thanks for merge this pull request, @{merged_by}! " \
                   f"@{author} ur issue is closed! :tada:"
        pr.create_comment(f"{response}")

@app.route("/", methods=['POST'])
def bot():
    payload = request.json

    if not 'repository' in payload.keys():
        return "", 204

    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']

    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    # Check if the event is a GitHub pull request creation event
    if all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'opened':
        pr_opened_event(repo, payload)
    # Check if PR are merged
    elif all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'closed':
        pr_closed_event(repo, payload)

    return "", 204

if __name__ == "__main__":
    app.run(debug=True, port=5000)
