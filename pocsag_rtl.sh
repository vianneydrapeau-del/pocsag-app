#!/bin/bash

rtl_fm -f 173.5125M -s 22050 - | \
sox -t raw -r 22050 -esigned -b16 - -t raw - | \
multimon-ng -a POCSAG1200 -a POCSAG2400 -f alpha -t raw - | \
while read -r line; do
  # ignorer lignes vides ou NUL
  if [[ -z "$line" ]] || [[ "$line" == *"<NUL>"* ]]; then
    continue
  fi

  curl -G --silent -X POST \
    --data-urlencode "msg=$line" \
    http://127.0.0.1:8000/add > /dev/null
done


