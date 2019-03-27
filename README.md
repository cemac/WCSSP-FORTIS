<div align="center">
<a href="https://www.cemac.leeds.ac.uk/">
  <img src="https://github.com/cemac/cemac_generic/blob/master/Images/cemac.png"></a>
  <br>
</div>


 <h1> <center> WCSSP FORTIS teaching app </center> </h1>
 
[![GitHub release](https://img.shields.io/github/release/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS/releases) [![GitHub top language](https://img.shields.io/github/languages/top/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS) [![GitHub issues](https://img.shields.io/github/issues/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS/issues) [![GitHub last commit](https://img.shields.io/github/last-commit/cemac/WCSSP-FORTIS.svg)](https://github.com/cemac/WCSSP-FORTIS/commits/master) [![GitHub All Releases](https://img.shields.io/github/downloads/cemac/WCSSP-FORTIS/total.svg)](https://github.com/cemac/WCSSP-FORTIS/releases)

Repository for the [WCSSP FORTIS](https://www.metoffice.gov.uk/research/collaboration/newton/wcssp-se-asia/wp3) training tool. [(fortis-training.herokuapp.com)](http://fortis-training.herokuapp.com).

<hr>

## Requirements

*see Pipfile*

## Installation

*coming soon*

<hr>

## Usage

```bash
git clone repo.git
cd repo
conda create -f fortis.yaml
source .env # git-crypted
python manage.py db upgrade
python manage runserver
```

**NB** .env can [be decrypted for CEMAC users](https://github.com/cemac/cemac_generic/wiki/Sensitive-information/)

*example .env coming soon*

<hr>

## Hosting

To make any code changes take effect on Heroku:
$ git push heroku master


## Backups

*coming soon*

## Flask App Custom features

*coming soon*

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

*coming soon*
