# worksummary fish completion
#
# The fish completion script Click 8.4 emits (via
# `_WORKSUMMARY_COMPLETE=fish_source worksummary`) is broken: Click writes
# one completion as three newline-separated fields (type, value, help), but
# the generated script iterates fish's response one line at a time and tries
# to index $metadata[2]/$metadata[3], which are always out of range. The
# practical result is that nothing ever completes.
#
# This file parses Click's three-line-per-item response correctly. Drop it
# into ~/.config/fish/completions/ (fish will auto-load it).

function _worksummary_completion
    set -l response (
        env _WORKSUMMARY_COMPLETE=fish_complete \
            COMP_WORDS=(commandline -cp) \
            COMP_CWORD=(commandline -t) \
            worksummary
    )

    set -l n (count $response)
    set -l i 1
    while test $i -le $n
        set -l type $response[$i]
        set -l value $response[(math $i + 1)]
        set -l help $response[(math $i + 2)]

        if test "$type" = dir
            __fish_complete_directories $value
        else if test "$type" = file
            __fish_complete_path $value
        else if test "$type" = plain
            if test "$help" = _
                echo $value
            else
                echo $value\t$help
            end
        end

        set i (math $i + 3)
    end
end

complete --no-files --command worksummary --arguments "(_worksummary_completion)"
