# worksummary fish completion
#
# Two reasons this exists instead of using `_WORKSUMMARY_COMPLETE=fish_source
# worksummary` to generate it:
#
# 1. Click 8.4's generated parser splits its response on newlines and then
#    indexes $metadata[2]/$metadata[3] per line — but Click emits one item
#    as three newline-separated fields (type, value, help), so those indices
#    are always out of range and nothing ever completes.
#
# 2. The generated script uses `env VAR=val … worksummary` to set
#    completion env vars. In at least some fish setups that subprocess
#    returns no output (Click sees no completion instruction and the call
#    silently produces nothing). Setting the vars with `set -lx` in fish
#    and calling worksummary directly avoids the problem entirely.
#
# Click's wire format also differs between versions, and worksummary runs
# against both (Ubuntu ships 8.4; nixpkgs ships an older Click), so parse both:
#
#   Click >= 8.2:  three newline-separated fields per item — type, value, help
#                  (help is "_" when absent)
#   Click <  8.2:  one line per item — "type,value", with an optional
#                  tab-separated help, e.g. "plain,add\tAdd a work item."
#
# Drop this file into ~/.config/fish/completions/ (fish will auto-load it). The
# Nix package installs it into share/fish/vendor_completions.d/ automatically.

function _worksummary_emit --argument-names type value help
    switch $type
        case dir
            __fish_complete_directories $value
        case file
            __fish_complete_path $value
        case plain
            if test -z "$help" -o "$help" = _
                echo $value
            else
                printf '%s\t%s\n' $value $help
            end
    end
end

function _worksummary_completion
    set -lx _WORKSUMMARY_COMPLETE fish_complete
    set -lx COMP_WORDS (commandline -cp)
    set -lx COMP_CWORD (commandline -t)
    set -l response (worksummary)

    test (count $response) -gt 0; or return

    if string match -qr '^(plain|file|dir),' -- $response[1]
        # Click < 8.2: "type,value" with an optional tab-separated help.
        for line in $response
            set -l head (string split -m1 ',' -- $line)
            set -l fields (string split -m1 \t -- $head[2])
            set -l help ""
            if test (count $fields) -ge 2
                set help $fields[2]
            end
            _worksummary_emit $head[1] $fields[1] $help
        end
    else
        # Click >= 8.2: type, value and help on three consecutive lines.
        set -l n (count $response)
        set -l i 1
        while test $i -le $n
            _worksummary_emit $response[$i] $response[(math $i + 1)] $response[(math $i + 2)]
            set i (math $i + 3)
        end
    end
end

complete --no-files --command worksummary --arguments "(_worksummary_completion)"
