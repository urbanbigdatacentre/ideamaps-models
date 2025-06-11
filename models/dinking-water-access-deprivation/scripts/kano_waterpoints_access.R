#library(tictoc)
#tic('whole script')
library(tidyverse)
library(glue)
library(sf)
library(units)
library(openrouteservice) # remotes::install_github("GIScience/openrouteservice-r");
library(furrr)
library(purrr)
library(mapview)

#setwd('kano_acces')
# set port on which the local openrouteservice listens for requests
port <- 8022

# Data input
origin_pts <- st_read('data-processing/kano_waterpoints_grid_centroids.geojson')
dest_pts <- st_read('data-processing/kano_waterpoints.geojson')

# check attributes
origin_pts |> names()
#> "fid"       "latitude"  "longitude" "lon_min"   "lat_min"   "lon_max"   "lat_max"   "geometry"

dest_pts |> names()
#>  [1] "fid"           "Submission"    "doYouQueue"    "peopleTrav"    "timeNeeded"    "userPosi_1"    "userPosi_2"    "waterDrink"   
#>  [9] "waterFree"     "waterPubli"    "waterSourc"    "waterState"    "waterType"     "Source.2"      "waterpoint_id" "buffer_m"     
#>  [17] "geometry" 

# add unique id to destination points
#dest_pts <- dest_pts |> mutate(rowid = row_number())



# quick viz to check destinations and origins
mapview(origin_pts, col.regions='red', cex=5) + mapview(dest_pts, cex=1)

#tic('ors matrix requests')
# parallelize for 4 workers
plan(multisession, workers = 4)

# Define Function to process each row ~ 1 origin x all destinations
process_row <- function(i, origin_pts, dest_pts, port) {

  # Select single source pt
  origin_pts_subset <- origin_pts[i, ]

  #create list of coordinate pairs only for both origins and destinations
  origin_pts_subset_coords <- map(origin_pts_subset$geometry |>
                                    st_centroid(), ~ c(st_coordinates(.x)[, 1], st_coordinates(.x)[, 2]))
  dest_pts_coords <- map(dest_pts$geometry |>
                                  st_centroid(), ~ c(st_coordinates(.x)[, 1], st_coordinates(.x)[, 2]))

  # merge to one single list of coords, remember first position is the coord of the origin
  coord_list_run <- c(origin_pts_subset_coords, dest_pts_coords)

  # set local openrouteservice url with port
  # has to be set in this function as options are overwritten in parallel processing
  options(openrouteservice.url = glue("http://localhost:{port}/ors"))

  # while loop in case connection problems, retry 10 times
  attempt <- 1
  while(!exists('res1') && attempt <= 10) {
    tryCatch({
        res1 <- ors_matrix(
        coord_list_run,
        sources = 0, # indicates which coord position is the origin/source, not 1 as in R but 0 as in Python/Java
        metrics = c("duration", "distance"),
        units = "km", # for durations we don't get to choose, they always come in seconds
        api_key = '', # not needed in local setup yay
        output = 'parsed',
        profile = 'foot-walking' # profile to use, see ORS API for more options
      )
    }, error = function(e) {
      message("Attempt ", attempt, " failed: ", conditionMessage(e))
      Sys.sleep(2) # Wait for 2 seconds before retrying
    })
    attempt <- attempt + 1
  }

  # check if we got a response
  if (!exists('res1')) {
    stop(glue("Failed to get a valid response after {attempt} attempts."))
  }

  # check if amount of responses are same as input paris
  if (length(res1$durations)!=length(coord_list_run)) {
    stop(glue("Returned less durations than expected. Expected {length(coord_list_run)}, got {length(res1$durations)}."))
  }

  # convert json response to dataframe
  result <- data.frame(
    origin_id=origin_pts_subset$grid_id |> rep(length(dest_pts_coords)),
    destination_id=dest_pts$waterpoint_id,
    duration_seconds=res1$durations[-1] |> as.numeric(), # exclude first data point which is the origin to itself
    distance_km=res1$distances[-1] |> as.numeric() # exclude first data point which is the origin to itself
  ) |> tibble()
  return(result)
}

results_matrix <- future_map_dfr(
  #1:4,
  1:nrow(origin_pts), # we only submit an index, the slicing/subsetting happens in the process_row function
  origin_pts=origin_pts,
  dest_pts=dest_pts,
  port=port, # we need to pass the port to the function, otherwise in parallel processes its defaulting to the public api
  process_row
)

# free the workers
plan(sequential)
#toc()

results_matrix |> head()
results_matrix |> nrow()

# write out the result dataframe
write.csv(results_matrix, "data-processing/kano_waterpoints_access.csv", row.names = FALSE)

# Don't forget to write dest_pts as we added a unique (row) id
#st_write(dest_pts, 'data-processing/population_centroids_ROWID.geojson', append=F)


#toc()
