# Kano Access

## Introduction

We setup up a local openrouteservice instance with a osm file of Nigeria. 
However the area of interest is the city of Kano.

Requirements:

- docker
- docker-compose
- R
- RStudio

## openrouteservice

Make sure docker and docker compose are installed on your machine.
If you run on Mac, docker desktop needs to run in the foreground.
This may be true for Windows as well.

### Container setup

The local openrouteservice docker will be configured through a compose file. 
There is an example compose file within this zip archive: `docker-compose.yml`

Important lines:

- Line 7: Name of the service `ors-nga` - `ors-ken` for Kenya
- Line 12: Name of the container `ors-nga` - `ors-nga` for Kenya
- Line 14: Port mapping the first number before : is the host port, the second number is the container port (inside:outside) All communication from the host to the container will be through this port.
- Line 16: The docker image to be used. This is the openrouteservice in version 9.0.0
- Line 19: The user mapping. This is the user that will be used to run the container. The user is created in the Dockerfile. This is an important parameter as the user needs to have permissions on the volumes. Volumes are folders that are mirrored outside and inside the docker. Volumes are defined in line 21.
There are two options:
  - Find out your local user: eg. on a unix machine with the command `id` and map that inside and outside
  - Use the default user id of inside and outside `1000:1000` but then make sure that this user _owns_ the volumes. On a unix machine this can be done with the command `sudo chown -R 1000:1000 /path/to/volume`
For either option you have to create the folder structure for the volume before running the openrouteservice docker. On unix use the command `mkdir -p ors-docker/config ors-docker/elevation_cache ors-docker/files ors-docker/graphs ors-docker/logs`. When you use your local user you can go ahead. When you use the default 1000 user, change ownership of all these created folders with the command from above `sudo chown -R 1000:1000 ors-docker/`
- Line 38: Minimum occupied RAM for the JAVA virtual machine, 2GB should work well
- Line 39: Maximum RAM allowed to be occupied by the JAVA virtual machine, 4GB should be more than enough for Nigeria.

Done. Now you can run the docker with the command `docker-compose up` from the same folder as the `docker-compose.yml` file. 

Starting up for the first time will take a while as the docker image needs to be downloaded.
But shouldn't take more than 5 minutes.

The openrouteservice will be available at `http://localhost:8022/ors/` & `http://localhost:8033/ors/` for Kenya.

In order to check if everything works, you can use the following curl commands or check out the urls in your browser:

- `curl localhost:8022/ors/v2/health` should respond `{"status":"ready"}`
- `curl localhost:8022/ors/v2/status` should respond general infos on languages available but also which profiles and restrictions are available/set.

Your local openrouteservice is ready, however it uses a standard osm data file for Heidelberg only. 
Stop the running docker container. Either with [CTRL+C] or `docker-compose down`.

### Change of osm data file 

First get a pbf for Nigeria from geofabrik

`wget https://download.geofabrik.de/africa/nigeria-latest.osm.pbf`
`wget https://download.geofabrik.de/africa/kenya-latest.osm.pbf`

Move it into the `file` folder/volume via ` mv nigeria-latest.osm.pbf ors-docker/files/.`

### Change of configurations - Matrix limits

But this is not enough, we need to tell openrouteservice via the configuration file that it should use this file.
While we do this we also change some other parameters like the maximum request size for Matrix/many-to-many endpoint.

Open the configuration file located in `ors-docker/config/ors-config.yml`
Change the following lines:

- Line 9: Replace the last part of the path from `heidelberg.test.pbf` to the new osm file `nigeria-latest.osm.pbf`  
- Line 67: Remove the `#` / uncomment to activate the `endpoint` branch of the yaml config file
- Line 80: Same here, remove the `#` / uncomment to activate the `matrix` branch of the yaml config file
- Line 83: First again remove the `#` / uncomment the line. Then change the number of maximum routes to a number of your choice. I am not aware of an upper limit here. For the Kano use case I set it to 2 500 000.

*Note* Added by Diego. Bear in mind that changing the osm file might require that graphs are created again. It is a good idea to delete the contents of the graphs folder to force the instance to recreate all graphs.

Perfekt you are done. 
Now you can start the docker container again as above.
Switch back to the location where your `docker-compose.yml` is located and run `docker-compose up`.

### Adding walking profiles (Added by Diego Pajarito)
Since walking routing options were also needed, we added configurations to the file. This can change the number lines above by adding 2 or 3 units.
Initially thre lines were added
#      foot-walking:
#        enabled: true
#        maximum_distance: 10000

## R & RStudio

Here I used R & RStudio as a client to interact with the local openrouteservice API, but of course you can now use any other client that can send HTTP requests. 
For R and Python as well as JScript we have wrapper libraries available, but you can also use the QGIS plugin.

If you use my provided R script `kano_access.R` you need to install the following packages:

`install.packages(c("tidyverse", "sf","purrr","furrr","mapview","remotes")`

The openrouteservice client you install via `remotes::install_github("GIScience/openrouteservice-r")`.
Awesome, now you are good to go

