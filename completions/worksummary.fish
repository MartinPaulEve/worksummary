# worksummary fish completion
#
# Two reasons this exists instead of using `_WORKSUMMARY_COMPLETE=fish_source
# worksummary` to generate it:
#
# 1. Click 8.4's generated parser splits its response on newlines and then
#    indexes $metadata[2]/$metadata[3] per line — but Click emits one item
#    as three newline-separated fields (type, value, help), so those indices
#    are always out of range and nothing ever completes. This file walks the
#    response three lines at a time, which is what Click actually intends.
#
# 2. The generated script uses `env VAR=val … worksummary` to set
#    completion env vars. In at least some fish setups that subprocess
#    returns no output (Click sees no completion instruction and the call
#    silently produces nothing). Setting the vars with `set -lx` in fish
#    and calling worksummary directly avoids the problem entirely.
#
# Drop this file into ~/.config/fish/completions/ (fish will auto-load it).

function _worksummary_completion
    set -lx _WORKSUMMARY_COMPLETE fish_complete
    set -lx COMP_WORDS (commandline -cp)
    set -lx COMP_CWORD (commandline -t)
    set -l response (worksummary)

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
