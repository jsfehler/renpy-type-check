init -2 python:
    import re


    # Specific variable name is inserted while checking
    # Check if a variable is set using SetVariable action
    SETVARIABLE_REGEX_PATTERN = r'(SetVariable\()(.*{}.*)(,.*)'
    # Check if a variable is set using =
    VARIABLE_ASSIGN_REGEX_PATTERN = r'(\b.*{}\b)(.=)(?!=)(.*)'


    class VariableInfo(object):
        """Stores information about a variable with a type comment."""
        __slots__ = (
            'filename',
            'lineno',
            'varname',
            'value',
            'type',
            'setvariable_regex',
            'variable_assign_regex',
        )

        def __init__(self, node):
            self.filename = node.filename.replace('game/', '')
            self.lineno = node.linenumber
            self.varname = node.varname
            self.value = node.code.source

            self.type = None

            self.setvariable_regex = re.compile(
                SETVARIABLE_REGEX_PATTERN.format(node.varname))

            self.variable_assign_regex = re.compile(
                VARIABLE_ASSIGN_REGEX_PATTERN.format(node.varname))

        def __repr__(self):
            return '{}:{} {} is defined as {}'.format(
                self.filename, self.lineno, self.varname, self.type
            )

        def check_reasign_via_setvariable(self, line, node):
            """Case: variable assignment via SetVariable Action."""
            match = self.setvariable_regex.search(line)
            if match:
                _, varname, _ = match.groups()
                name = varname.strip('"').strip("'")
                current_type = check_setvariable(
                    node,
                    line,
                    name,
                )
                return current_type
            return self.type

        def check_reasign_via_equals_sign(self, line, node):
            """Case: variable assignment via equals sign."""
            match = self.variable_assign_regex.search(line)
            if match:
                varname, _, _ = match.groups()
                current_type = check_reassigned_variable_type(
                    node,
                    line,
                    varname,
                )
                return current_type
            return self.type


    def check_reassigned_variable_type(node, line, varname):
        """Evaluate line and see what the type of the variable is.

        Arguments:
            node (Node)
            line (str)
            varname (str)

        """
        name = varname.strip()
        check_line = '{}\ncurrent_type = type({})'

        try:
            c = check_line.format(line.strip(), name)
            exec(c)
        # Evaluate entire block of code
        except Exception as e:
            c = check_line.format(node.code.source, name)
            exec(c)

        return current_type


    def check_setvariable(node, line, varname):
        """Evaluate line and see what the type of the variable is.

        Arguments:
            node (Node)
            line (str)
            varname (str)

        """
        name = varname.strip()
        check_line = '{}()\ncurrent_type = type({})'

        try:
            c = check_line.format(line.strip(), name)
            exec(c)
        # Evaluate entire block of code
        except Exception as e:
            c = check_line.format(node.code.source, name)
            exec(c)

        return current_type
