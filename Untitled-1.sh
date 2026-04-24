#!/usr/bin/env bash

shopt -s nullglob

for icon in ./icons/*.ico; do
  # Convert ICO to PNG(s)
  magick "$icon" "./icons/$(basename "${icon%.ico}")-%d.png"

  # Get all generated PNGs for this icon
  pngs=(./icons/"$(basename "${icon%.ico}")"-*.png)

  if [ ${#pngs[@]} -eq 0 ]; then
    continue
  fi

  # Find the PNG with the largest dimensions
  largest=""
  max_pixels=0
  for png in "${pngs[@]}"; do
    # Get width and height
    read width height < <(magick identify -format "%w %h" "$png")
    pixels=$((width * height))
    if ((pixels > max_pixels)); then
      max_pixels=$pixels
      largest="$png"
    fi
  done

  # Rename the largest to the base icon name
  mv "$largest" "./icons/$(basename "${icon%.ico}").png"

  # Remove all other PNGs
  for png in "${pngs[@]}"; do
    [ "$png" != "$largest" ] && rm "$png"
  done

  # Remove the original .ico
  rm "$icon"
done
