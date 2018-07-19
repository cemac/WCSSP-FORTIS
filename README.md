After any required setup steps, run this app locally using:
$ python manage.py runserver
and go to localhost:5000 in a web browser

To make changes to the GitHub repo:
- If you are a collaborator, you can simply push local changes to the main repo
- If you are not a collaborator, follow these instructions:
  - Fork and clone the main repo
  - Configure your local forked repo to sync with the main repo:
    $ git remote add upstream https://github.com/cemac-tech/WCSSP-FORTIS.git
  - You can then keep your local forked repo up-to-date with any changes to the main repo using:
    $ git fetch upstream; git merge upstream
    OR
    $ git pull upstream master
  - Make a new branch for a particular new development/bug fix:
    $ git checkout -b branchName
  - Commit changes locally as normal, and push to the remote forked repo using:
    $ git push origin branchName
  - Once happy with your changes, open a pull request (PR) from your remote forked repo's GitHub page
  - This PR wil be reviewed by one of the code owners and, once any follow-up changes are made, pulled into th main repo
  - It is then good practice to delete the branch in both the remote forked repo (can be done via GitHub) and the local forked repo:
    $ git branch -d branchName

To make any code changes take effect on Heroku:
$ git push heroku master
