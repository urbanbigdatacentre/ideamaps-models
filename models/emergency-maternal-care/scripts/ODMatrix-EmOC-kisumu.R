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

# Working directory set to the scripts folder
# This script uses a self-hosted instance of the ORS, therefore, server ip address
# Must be changed if the public API ORS is going to be used
# If using local UBDC servers, VPN must be enabled

port <- 8084
host <- '130.209.67.118'

# Data input
getwd()
setwd("D:/githubdp/ideamaps-models/models/emergency-maternal-care/scripts")
origin_pts <- st_read('./Kisumu/data-inputs/healthcare_facilities_kisumu.geojson')
dest_pts <- st_read('Kisumu/data-temp/grid_centroids.gpkg')

# check attributes. This will allow you identify the column names used as
# unique identifiers and geometry. 
# These will be required in the process_row function 
origin_pts |> names()
#> "field_1"                   "Field_1_1"                 "Admin_1"                   "facility_name"            
#> "facility_type"             "owner_type_name"           "latitude"                  "longitude"                
#> "Sub_Couinty"               "LL_Source"                 "ward_name"                 "keph_level_name"          
#> "Operating_Time"            "total_.inpatient_beds"     "general_inpatient_beds"    "cots"                     
#> "maternity_beds"            "emergency_casualty_beds"   "intensive_care_unit_beds"  "high_dependancy_unit_beds"
#> "isolation_beds"            "general_theatres"          "maternity_theatres"        "minor_theatres"           
#> "BMoc"                      "CeMoc"                     "Local_Validation"          "hcf_id"                   
#> "geometry"   

dest_pts |> names()
#> "grid_id"   "latitude"  "longitude" "pop"       "geom" 


# If one of the datasets does not have an id column, you can add a unique id 
# using the following example
#dest_pts <- dest_pts |> mutate(rowid = row_number())

# quick viz to check destinations and origins
mapview(origin_pts, col.regions='red', cex=5) + mapview(dest_pts, cex=1)

#tic('ors matrix requests')
# parallelize for 4 workers
plan(multisession, workers = 4)

# Define Function to process each row ~ 1 origin x all destinations
process_row <- function(i, origin_pts, dest_pts, host, port) {

  # Select single source pt
  origin_pts_subset <- origin_pts[i, ]

  #create list of coordinate pairs only for both origins and destinations
  origin_pts_subset_coords <- map(origin_pts_subset$geometry |>
                                    st_centroid(), ~ c(st_coordinates(.x)[, 1], st_coordinates(.x)[, 2]))
  dest_pts_coords <- map(dest_pts$geom |>
                                  st_centroid(), ~ c(st_coordinates(.x)[, 1], st_coordinates(.x)[, 2]))

  # merge to one single list of coords, remember first position is the coord of the origin
  coord_list_run <- c(origin_pts_subset_coords, dest_pts_coords)

  # set local openrouteservice url with port
  # has to be set in this function as options are overwritten in parallel processing
  options(openrouteservice.url = glue("http://{host}:{port}/ors"))

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
        profile = 'driving-car' # profile to use, see ORS API for more options
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
    origin_id=origin_pts_subset$hcf_id |> rep(length(dest_pts_coords)), # confirm the column names are right
    destination_id=dest_pts$grid_id,   # confirm the column names are right
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
  host=host, # we need to pass the host address to ensure we are using remote servers (not always localhost)
  port=port, # we need to pass the port to the function, otherwise in parallel processes its defaulting to the public api
  process_row
)

# free the workers
plan(sequential)
#toc()

results_matrix |> head()
results_matrix |> nrow()

# write out the result dataframe
write.csv(results_matrix, "data-processing/kisumu_access.csv", row.names = FALSE)

# Don't forget to write dest_pts as we added a unique (row) id
st_write(dest_pts, 'data-processing/population_centroids_ROWID.geojson', append=F)


#toc()
