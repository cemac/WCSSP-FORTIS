<div align="center">
<a href="https://www.cemac.leeds.ac.uk/">
  <img src="https://github.com/cemac/cemac_generic/blob/master/Images/cemac.png"></a>
  <br>
</div>

 <h1> <center> WCSSP FORTIS teaching app </center> </h1>
<<<<<<< HEAD

<!--- release table --->

| Version            | Release                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **Current Stable** | [![GitHubrelease](https://img.shields.io/badge/release-v.1.0-blue.svg)](https://github.com/cemac/WCSSP-FORTIS/releases/tag/1.0) |
| **2019**           | _coming soon_                                                                                                                   |

<!--- table --->
=======
 
[![GitHub release](https://img.shields.io/github/release/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS/releases) [![GitHub top language](https://img.shields.io/github/languages/top/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS) [![GitHub issues](https://img.shields.io/github/issues/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS/issues) [![GitHub last commit](https://img.shields.io/github/last-commit/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS/commits/master) [![GitHub All Releases](https://img.shields.io/github/downloads/cemac/WCSSP-FORTIS/total.svg)](https://github.com/cemac/WCSSP-FORTIS/releases)
>>>>>>> 86f7d40... :octocat: :tophat: badges update

Repository for the [WCSSP FORTIS](https://www.metoffice.gov.uk/research/collaboration/newton/wcssp-se-asia/wp3) training tool. [(fortis-training.herokuapp.com)](http://fortis-training.herokuapp.com).

<hr>

## Requirements

* anaconda (reccomended) *see Requirements.txt*
* git-crypt (optional sharing api keys)
* heroku and googlecloud capability

## Installation (UNIX)

Recommended via anaconda - see

```
```


<hr>

## Usage

<<<<<<< HEAD
* [Developers](https://github.com/cemac/WCSSP-FORTIS/wiki/Developers-Guide)
* [Users](https://github.com/cemac/WCSSP-FORTIS/wiki/User-Guide)
=======
```bash
git clone repo.git
cd repo
conda create -f fortis.yaml
source .env # git-crypted
python manage.py db upgrade
python manage runserver
```
>>>>>>> 73028c9... :memo: note on git crypt

**NB** .env can [be decrypted for CEMAC users](https://github.com/cemac/cemac_generic/wiki/Sensitive-information/)

*example .env coming soon*

<hr>

## Hosting

To make any code changes take effect on Heroku:
$ git push heroku master

## Backups

_coming soon_

## Flask App Custom features

_coming soon_

<hr>

<!--- release table --->
|  Version            | Release          |
|---------------------|------------------|
| **Current Stable**  | [![GitHubrelease](https://img.shields.io/badge/release-v.1.0-blue.svg)](https://github.com/cemac/WCSSP-FORTIS/releases/tag/1.0)|
| **2019**            | *coming soon*    |
<!--- table --->
## License Information

This code is currently licensed under the [MIT license](https://choosealicense.com/licenses/mit/).

## Acknowledgements

_coming soon_
