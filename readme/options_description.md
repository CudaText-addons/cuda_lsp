# Options description

* root_dir_source - LSP server root directory source (accepts list of values for fallback):
    * 0 - parent directory of '.cuda-proj'
    * 1 - first directory in project
    * 2 - project main-file's directory

* send_change_on_request - send changes only before request
    * false - changes to the documents are sent to server after edit and a short delay (default)
    * true - sent only before requests (will delay server's analysis)

* enable_mouse_hover - when 'false' - 'hover' only accessible via a command

* hover_dlg_max_lines - hover dialog max lines number, default is 10

* hover_additional_commands - list of additional commands to show in hover dialog; possible values:
    * "definition"
    * "references"
    * "implementation"
    * "declaration"
    * "type definition"

* hover_with_ctrl - if 'true', Ctrl-key must be pressed when you want to show the hover dialog (by moving and stopping the mouse)

* cudatext_in_py_env - add CudaText API to Python server

* lint_type - lint display manner; string, combination of the following characters:
    * 'd' - icons to indicate severity of lint message on the line
    * 'b' - bookmarks with icons and message details on hover (overrides 'd')
    * 'B' - same as 'b' and also highlights line backgrounds (overrides 'b' and 'd')
    * 'c' - underline message's text range

* lint_underline_style - style of underline for lint target text; possible values:
    * 0 - "solid"
    * 1 - "dotted"
    * 2 - "dashes"
    * 3 - "wave"

* enable_code_tree - fill "Code Tree" from the LSP server

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

* auto_append_bracket - after selecting a method in code completion listbox try to append parentheses automatically if they are missing

* hard_filter - autocompletion items will be filtered more strictly (only from beginning of the word and only same letter case).

* use_cache - simple caching of autocompletion results. improves speed.

* servers_shutdown_max_time - maximum amount of seconds to wait for LSP servers to shut down. default is 2 seconds. user can set this to 0 to improve CudaText's shutdown speed. use at your own risk.

* enable_semantic_tokens - enable language specific symbol colorization (if supported by server). cuda_lsp tries to get additional color information for language specific symbols like classes, functions, variables, parameters, etc..

* semantic_max_lines - maximum lines in editor for semantic tokens to work.

* semantic_colors_* - colors for semantic tokens separated by comma, in the following order:
    * "namespace, class, method, function, variable, parameter, macro, property, enumMember, constant".
    * for example default value for "semantic_colors_light": '#BC7676,#15AD00,#BF00AF,#BF00AF,,,#FF2436,,#d79e3f,#00B3B7'
    * you can skip colors, so they will not be painted by LSP server.
    * additionally, color for `types` will be taken from current syntax theme (Id2).

* disabled_contexts - how to disable auto-completion in "comments" and "strings" for all servers. If "c" in value - disable in "comments", if "s" in value - disable in "strings". Can be overriden in server config.

* use_markers - whether to show markers (the little red triangles) when showing autocompletion snippets

* complete_from_text - include autocomplete results from "Complete From Text" plugin.

* diagnostics_in_a_corner - show diagnostics for current line in a corner of editor.
