from core.scheme_parser import SchemeParser
import docx

def create_test_docx():
    doc = docx.Document()
    text = """Question: Explain the following Git commands with syntax and an example: 1. Push 2. Merge 3. Commit 4. Checkout
Max Marks: 8
Type: Flexible
Min Length: minimum 1 page (20-25)
Answer: The answer should explain each Git command with its purpose, syntax, and one suitable example. Git Push: Used to upload local commits to a remote repository. Syntax: git push <remote_name> <branch_name>. Example: git push origin main. Git Merge: Used to combine changes from one branch into another. Syntax: git merge <branch_name>. Include an example such as merging a feature branch into the main branch. Git Commit: Records staged changes in the local repository with a descriptive message. Syntax: git commit -m "commit message". Explain that the -m option specifies the commit message. Git Checkout: Used to switch between branches or restore files. Syntax: git checkout <branch_name> and git checkout -b <new_branch_name> to create and switch to a new branch. Include an appropriate example for each command.
________________________________________
Question: Illustrate the steps involved in understanding the Git process and Gitflow pattern with a neat diagram.
Max Marks: 7
Type: Flexible
Min Length: None
Answer: The answer should explain the Git workflow with a suitable diagram. The first developer modifies code in the local repository, commits the changes, and pushes them to the remote repository. The second developer pulls the latest code from the remote repository to synchronize the local copy, makes modifications, commits the changes, and pushes the updated version back to the remote repository. Finally, the first developer pulls the latest changes from the remote repository to update the local repository. The explanation should highlight collaboration through local and remote repositories and the synchronization process using commit, push, and pull operations.
________________________________________
Question: Illustrate the process of creating a Continuous Integration pipeline in GitLab using a .gitlab-ci.yml file.
Max Marks: 8
Type: Flexible
Min Length: Minimum 2 and half pages 
Answer: The answer should explain that GitLab CI/CD automates building, testing, and deployment using a .gitlab-ci.yml file placed in the root of the repository. It should describe the stages: Build (compile or package the application), Test (execute automated tests), and Deploy (release the application after successful validation). Include a sample pipeline with jobs such as build_job, test_job, and deploy_job, demonstrating stage definitions and scripts. Mention that deployment can be restricted to the main branch using only: - main. Also explain that pipelines can be viewed in GitLab → CI/CD → Pipelines, where each stage shows its execution status (passed, failed, or running).
________________________________________
Question: Consider the scenario which involves setting up a mechanism that notifies Jenkins as soon as a new push occurs in the GitHub repository. Analyze the above using GitHub Webhook.
Max Marks: 7
Type: Flexible
Min Length: None
Answer: The answer should explain that GitHub Webhooks enable automatic communication between GitHub and Jenkins. The process includes navigating to GitHub Repository → Settings → Webhooks, selecting Add Webhook, entering the Jenkins Payload URL in the format http://<JENKINS_SERVER_URL>:<PORT>/github-webhook/ or https://<JENKINS_SERVER_URL>/github-webhook/, leaving the secret as required, and selecting the Just the push event option. Explain that the Payload URL is the endpoint where GitHub sends an HTTP POST request containing a JSON payload with details such as the user, branch, commits, and event information. Jenkins receives this payload, validates it, and triggers the configured build job automatically. Conclude by mentioning webhook validation to ensure successful integration."""
    for line in text.split('\n'):
        doc.add_paragraph(line)
    doc.save("test_scheme.docx")
    
create_test_docx()
parser = SchemeParser()
q = parser.parse_scheme("test_scheme.docx")
print("Found questions:", len(q))
import pprint
pprint.pprint(q)
