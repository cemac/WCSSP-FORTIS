Before running this web app, ensure the sqlite3 database users.db is present. If it isn't,
ensure users.csv (not version controlled) is present and build the sqlite3 database using:
$ ./makeUsersDB.sh
Also ensure the sqlite3 database workshops.db is present. If it isn't, build using:
$ ./makeWorkshopDB.sh
Also ensure files.db is present. If it isn't, create a new blank database using:
$ sqlite3 files.db < files.sql
(The above commands rely on sqlite3 being installed)

Note that in order for the app to run successfully, the file AppSecretKey.txt must also
be present in the app's root directory (not version-controlled)

To run the app in development mode (on localhost), do the following:
- In FORTISApp.py, change the subdomain variable (subd) near the top of the script from "/WSCCP-FORTIS" to "" (i.e. an empty string)
- In FORTISApp.py, add "debug=True" inside the parentheses in the call to app.run near the bottom of the script
- If on the FOE system, load the appropriate python modules by typing: $ module load python3 python-libs
- Run the application by typing: $ python3 FORTISApp.py
- Open up a web browser and navigate to localhost:5000

***Don't forget to reset subd and remove from debug mode before committing to GitHub (production mode)***
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

To make any code changes take effect on the server, ssh into it, update the git repo, and perform a restart:
$ ssh -Y <serverName>
$ cd /www/<projectDir>/
$ git pull
$ sudo systemctl restart httpd
