init -1 python:
    import re


    # Checks for the 'type:' declaration
    TYPE_COMMENT_REGEX = re.compile(r"\s*# type:(.*)")

    warn_if_untyped = True

    def get_defaults(statements):
        """Gather default statements and collect their nodes in a list.

        Arguments:
            statements (list)

        Returns:
            list

        """
        defaults = []

        # Gather defaults (No distinction for special namespaces)
        for node in statements:
            if isinstance(node, renpy.ast.Default):
                # Ignore engine code in the renpy directory
                if not node.filename.startswith('renpy/'):
                    defaults.append(VariableInfo(node))

        for node in renpy.ast.default_statements:
            node.set_default(False)

        return defaults


    def get_defaults_with_type_comments(defaults):
        """Collect defaults with type comments.

        Each file with a default is scanned and checked for a type comment.

        Arguments:
            defaults (list)

        Returns:
            list
        """
        defaults_with_type_comments = []

        for item in defaults:
            with renpy.file(item.filename) as f:
                for i, line in enumerate(f):
                    if i + 1 == item.lineno:
                        match = TYPE_COMMENT_REGEX.search(line)
                        if match:
                            m = match.groups()
                            item.type = eval(m[0].strip())
                            defaults_with_type_comments.append(item)

        return defaults_with_type_comments


    def type_mismatch_message(item, current_type, node):
        return '{} but redefined as {} at {}:{}'.format(
            str(item), current_type, node.filename, node.linenumber,
        )

    def report_type_change(item, node, line):
        current_type = item.check_reasign_via_equals_sign(line, node)
        if current_type != item.type:
            print(type_mismatch_message(item, current_type, node))
            return True

        # Scenario: Called SetVariable in Python instead of screen action.
        current_type = item.check_reasign_via_setvariable(line, node)
        if current_type != item.type:
            print(type_mismatch_message(item, current_type, node))
            return True

        return False


    def check_type_comments():
        all_statements = renpy.game.script.all_stmts

        # Execute default statements so they can be checked for reassignment
        defaults = get_defaults(all_statements)
        defaults_with_type_comments = get_defaults_with_type_comments(defaults)

        if warn_if_untyped:
            untyped_defaults = [i for i in defaults if i not in defaults_with_type_comments]
            for d in untyped_defaults:
                print("Warning: {} is untyped.".format(d.varname))

        # Scan statements for any reassignment of defaults
        for node in all_statements:
            # Screen
            if isinstance(node, renpy.ast.Screen):
                const_ast = node.screen.const_ast
                if const_ast:
                    for child in const_ast.children:
                        # Python code
                        if isinstance(child, renpy.sl2.slast.SLPython):
                            if item.varname in child.code.source.split(' '):
                                report_type_change(item, node, child.code.source)

                        # Displayable
                        elif isinstance(child, renpy.sl2.slast.SLDisplayable):
                            for t in child.keyword:
                                if "SetVariable" in t[1]:
                                    for item in defaults_with_type_comments:
                                        current_type = item.check_reasign_via_setvariable(t[1], None)
                                        if current_type != item.type:
                                            print(type_mismatch_message(item, current_type, node))
                                            break
            # Python code
            elif isinstance(node, renpy.ast.Python):
                logical_lines = node.code.source.split('\n')

                for line in logical_lines:
                    for item in defaults_with_type_comments:
                        if item.varname in line.split(' '):
                            if report_type_change(item, node, line):
                                break
