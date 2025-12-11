# ---- Accra EmOC OD matrix: ORS (Ghana, local) ----

library(dplyr)
library(tibble)
library(glue)
library(sf)
library(units)
library(openrouteservice)
library(furrr)
library(purrr)
library(mapview)

# 1) change path to input file directory
# setwd("/Users/mingyu.zhu/projects/accra-emoc-od")

# Local ORS setting
host <- "localhost"
port <- 8022

# ORS matrix single attempt threshold （must < 2500）
MAX_DEST_PER_CALL <- 2000L

# ---------- 2. read data ----------
origin_pts <- st_read("healthcare_facilities_emoc.geojson")
dest_pts   <- st_read("grid_centroids.gpkg")

cat("Origin columns:\n"); print(names(origin_pts))
cat("Dest columns:\n");   print(names(dest_pts))

# origin 列：Region, District, FacilityName, Type, Town, Ownership, Latitude, Longitude, geometry
# dest   列：grid_id, latitude, longitude, pop, geom

# add id for origin （OD matrix use this origin_id）
if (!"origin_id" %in% names(origin_pts)) {
  origin_pts <- origin_pts |> mutate(origin_id = dplyr::row_number())
}

# In vase geom does not exist, but geometry does，just rename
if (!"geom" %in% names(dest_pts) && "geometry" %in% names(dest_pts)) {
  dest_pts <- dest_pts |> dplyr::rename(geom = geometry)
}

# ---------- 3. calculate single origin to all dest （sepeate in batch based on dest） ----------
process_row <- function(i, origin_pts, dest_pts, host, port, max_dest = MAX_DEST_PER_CALL) {
  origin_pts_subset <- origin_pts[i, , drop = FALSE]
  
  # origin coordinates (X=lon, Y=lat)
  origin_pts_subset_coords <- map(
    origin_pts_subset$geometry |> st_centroid(),
    ~ {
      xy <- st_coordinates(.x)
      c(xy[1, 1], xy[1, 2])  # (lon, lat)
    }
  )
  
  # separate all dest in batched based on max_dest
  n_dest <- nrow(dest_pts)
  dest_indices_list <- split(seq_len(n_dest), ceiling(seq_len(n_dest) / max_dest))
  
  all_results <- vector("list", length(dest_indices_list))
  
  for (k in seq_along(dest_indices_list)) {
    idx <- dest_indices_list[[k]]
    dest_subset <- dest_pts[idx, , drop = FALSE]
    
    # dest coordinates (X=lon, Y=lat)
    dest_pts_coords <- map(
      dest_subset$geom |> st_centroid(),
      ~ {
        xy <- st_coordinates(.x)
        c(xy[1, 1], xy[1, 2])  # (lon, lat)
      }
    )
    
    coord_list_run <- c(origin_pts_subset_coords, dest_pts_coords)
    
    options(openrouteservice.url = glue("http://{host}:{port}/ors"))
    
    res1 <- NULL
    attempt <- 1
    while (is.null(res1) && attempt <= 10) {
      tryCatch({
        res1 <- ors_matrix(
          coord_list_run,
          sources   = 0,                         # NO.0 is origin
          metrics   = c("duration", "distance"),
          units     = "km",
          api_key   = "",
          output    = "parsed",
          profile   = "driving-car"
        )
      }, error = function(e) {
        message("Origin ", i,
                " | chunk ", k, "/", length(dest_indices_list),
                " | Attempt ", attempt, " failed: ", conditionMessage(e))
        Sys.sleep(2)
      })
      attempt <- attempt + 1
    }
    
    if (is.null(res1)) {
      stop(glue("Origin {i}, chunk {k}: Failed to get a valid response after {attempt - 1} attempts."))
    }
    
    if (length(res1$durations) != length(coord_list_run)) {
      stop(glue(
        "Origin {i}, chunk {k}: Returned less durations than expected. Expected {length(coord_list_run)}, got {length(res1$durations)}."
      ))
    }
    
    # remove first item of origin→origin
    chunk_result <- tibble(
      origin_id        = origin_pts_subset$origin_id |> rep(length(dest_pts_coords)),
      destination_id   = dest_subset$grid_id,
      duration_seconds = as.numeric(res1$durations[-1]),
      distance_km      = as.numeric(res1$distances[-1])
    )
    
    all_results[[k]] <- chunk_result
  }
  
  dplyr::bind_rows(all_results)
}

# ---------- 4. run all origin in parallel ----------
plan(multisession, workers = 4)

# try part of the origin，like 1:3，to confirm it is working
# seq_to_run <- 1:3
seq_to_run <- seq_len(nrow(origin_pts))

results_matrix <- future_map_dfr(
  seq_to_run,
  origin_pts = origin_pts,
  dest_pts   = dest_pts,
  host       = host,
  port       = port,
  max_dest   = MAX_DEST_PER_CALL,
  .f         = process_row
)

plan(sequential)

cat("Total OD pairs:", nrow(results_matrix), "\n")
print(head(results_matrix))

# ---------- 5. Export the results ----------
write.csv(results_matrix, "OD-matrix-accra-access-emoc.csv", row.names = FALSE)

st_write(origin_pts, "accra_emoc_healthfacilities_with_origin_id.geojson", append = FALSE)
st_write(dest_pts,   "accra_emoc_grid_centroids_with_grid_id.geojson", append = FALSE)

cat("Done. Files written:\n")
cat("  - OD-matrix-accra-access-emoc.csv\n")
#cat("  - accra_emoc_healthfacilities_with_origin_id.geojson\n")
#cat("  - accra_emoc_grid_centroids_with_grid_id.geojson\n")
