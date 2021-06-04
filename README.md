<center><img src="https://raw.githubusercontent.com/colav/colav.github.io/master/img/Logo.png"/></center>

# HunabKu  
Data Server Gateway/  Maya - father of all gods

# Description
Package to load data in MongoDB and to serve the data from mongodb on endpoints using flask. 
The package is handling the endpoints  using a customized plugin system designed by us.

Modules are:
PDBS (Paper DataBase Server)
PDBL  (Paper DataBase Loader)
PDBM (Paper DataBase Manager) (to handle - CRUD) (Not Yet!)

# Installation

## Dependencies
* Install nodejs 
    * Debian based system: `apt-get install nodejs`
    * Redhat based system: `yum install nodejs`
    * Conda: `conda install nodejs`
* Install Apidocjs from https://github.com/apidoc/apidoc
* The other dependecies can be installed with pip installing this package.

## Package
`pip install hunabku`

# Usage
Let's start the server executing
```.sh
hunabku_server
```
Or using some command line options
```.sh
hunabku_server --port 8080 --db_ip x.x.x.x
```

where x.x.x.x is your mongodb ip

you can access to the apidoc documentation for the endpoints for example on: http://127.0.1.1:8888/apidoc/index.html

if depends of the ip and port that you are providen to hunabku.


# License
BSD-3-Clause License 

# Links
http://colav.udea.edu.co/



