#!/bin/bash

process_directory() {
    local dir="$1"

    if [[ -f "$dir/hedgedoc.list" ]]; then
        echo "Found hedgedoc.list in: $dir"

        local md_dir="$dir/md"
        mkdir -p "$md_dir"

        local pdf_dir="$dir/pdf"
        mkdir -p "$pdf_dir"

        while IFS= read -r line; do
            name="$(echo "$line" | cut -d':' -f1)"
            url="$(echo "$line" | cut -d':' -f2- | xargs)/download"

            if [[ -n "$name" && -n "$url" ]]; then
                echo "Downloading $url as $name.md"
                curl -s "$url" -o "$md_dir/$name.md"

                echo "Converting $name.md to $name.pdf"
                pandoc "$md_dir/$name.md" -o "$pdf_dir/$name.pdf"
            else
                echo "Skipping malformed line: $line"
            fi
        done < "$dir/hedgedoc.list"
    fi
}

export -f process_directory
find . -type d -exec bash -c 'process_directory "$0"' {} \;

