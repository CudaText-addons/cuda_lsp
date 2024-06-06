# Options description

* root_dir_source - LSP server root directory source (accepts list of values for fallback):
    * 0 - parent directory of '.cuda-proj'
    * 1 - first directory in project
    * 2 - project main-file's directory

* send_change_on_request - how to send editor's changes to server:
    * false - changes are sent to server after editing and a short delay (default).
    * true - changes are sent only before requests (will delay server's analysis).

* enable_mouse_hover - if 'false', hover-dialog is only accessible via a command (from Command Palette).

* hover_dlg_max_lines - hover-dialog max lines number, default is 10.

* hover_additional_commands - list of additional commands to show in the hover-dialog. Possible values:
    * "definition"
    * "references"
    * "implementation"
    * "declaration"
    * "type definition"

* hover_with_ctrl - if 'true', Ctrl-key must be pressed when you want to show the hover-dialog (by moving and stopping the mouse).

* cudatext_in_py_env - add CudaText API to Python server.

* lint_type - how to show linting errors/warnings in editor. Value is string, combination of the following characters:
    * 'd' - gutter decoration icons to indicate severity of lint messages.
    * 'b' - bookmarks with icons; message details will be shown in tooltip on hovering the icon (overrides 'd').
    * 'B' - same as 'b' and also highlights line backgrounds (overrides 'b' and 'd').
    * 'c' - underline message's text range.

* lint_underline_style - style of underline for linting, when "lint_type" is "c". Possible values:
    * 0 - "solid"
    * 1 - "dotted"
    * 2 - "dashes"
    * 3 - "wave"

* enable_code_tree - fill "Code Tree" from LSP server.

* tree_types_show - which document symbols to show in the "Code Tree". Empty string for default value, or comma-separated string of symbol kinds:
    * shown by default:
        * namespace
        * class
        * method
        * constructor
        * interface
        * function
        * struct
    * hidden:
        * file
        * module
        * package
        * property
        * field
        * enum
        * variable
        * constant
        * string
        * number
        * boolean
        * array
        * object
        * key
        * null
        * enummember
        * event
        * operator
        * typeparameter

* auto_append_bracket - after choosing a method in auto-completion listbox, try to append parentheses automatically if they are missing.

* hard_filter - auto-completion items will be filtered more strictly (only from beginning of the word and only same letter case).

* use_cache - use simple caching of auto-completion results, improves speed.

* servers_shutdown_max_time - maximum amount of seconds to wait for LSP server to shut down. Default is 2 seconds. User can set this to 0 to improve CudaText's shutdown speed. Use at your own risk.

* enable_semantic_tokens - enable semantic colorization (if supported by server). LSP plugin tries to get additional color information for language specific symbols like classes, functions, variables, parameters, etc.

* semantic_max_lines - maximum count of lines in editor for semantic colorization to work.

* semantic_colors_* - colors for semantic colorization, separated by comma, in the following order: namespace, class, method, function, variable, parameter, macro, property, enumMember, constant.
    * for example, default value of "semantic_colors_light": '#BC7676,#15AD00,#BF00AF,#BF00AF,,,#FF2436,,#d79e3f,#00B3B7'.
    * you can skip colors, so they will not be painted by LSP server.
    * additionally, color for `types` will be taken from current syntax theme (Id2).

* disabled_contexts - how to disable auto-completion in "comments"/"strings" for all servers. If "c" in value - disable in "comments", if "s" in value - disable in "strings". Can be overriden in server config.

* use_markers - enable markers/tabstops (little red triangles) when inserting auto-completion snippets.

* complete_from_text - include auto-completion results from "Complete From Text" plugin.

* diagnostics_in_a_corner - show diagnostics for current line in the editor's corner.
