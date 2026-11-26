import sys
import os
import re

class JackTokenizer:
    KEYWORDS = {
        'class', 'constructor', 'function', 'method', 'field', 'static',
        'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
        'this', 'let', 'do', 'if', 'else', 'while', 'return'
    }
    SYMBOLS = {
        '{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/',
        '&', '|', '<', '>', '=', '~'
    }

    def __init__(self, input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = self._remove_comments(content)
        self.tokens = self._tokenize(content)
        self.current_idx = -1
        self.current_token = None
        self.current_type = None

    def _remove_comments(self, text):
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'//.*', '', text)
        return text

    def _tokenize(self, text):
        token_pattern = r'"[^"\n]*"|[{}()\[\].,;+\-*/&|<>=~]|[A-Za-z_]\w*|\d+'
        raw_tokens = re.findall(token_pattern, text)
        parsed = []
        for t in raw_tokens:
            if t in self.KEYWORDS:
                parsed.append(('KEYWORD', t))
            elif t in self.SYMBOLS:
                parsed.append(('SYMBOL', t))
            elif t.isdigit():
                parsed.append(('INT_CONST', int(t)))
            elif t.startswith('"') and t.endswith('"'):
                parsed.append(('STRING_CONST', t[1:-1]))
            else:
                parsed.append(('IDENTIFIER', t))
        return parsed

    def has_more_tokens(self):
        return self.current_idx + 1 < len(self.tokens)

    def advance(self):
        if self.has_more_tokens():
            self.current_idx += 1
            self.current_type, self.current_token = self.tokens[self.current_idx]

    def peek(self):
        if self.has_more_tokens():
            return self.tokens[self.current_idx + 1]
        return (None, None)

    def token_type(self):
        return self.current_type


class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.indices = {'STATIC': 0, 'FIELD': 0, 'ARG': 0, 'VAR': 0}

    def start_subroutine(self):
        self.subroutine_scope.clear()
        self.indices['ARG'] = 0
        self.indices['VAR'] = 0

    def define(self, name, var_type, kind):
        kind = kind.upper()
        idx = self.indices[kind]
        self.indices[kind] += 1
        entry = {'type': var_type, 'kind': kind, 'index': idx}
        if kind in ('STATIC', 'FIELD'):
            self.class_scope[name] = entry
        else:
            self.subroutine_scope[name] = entry

    def var_count(self, kind):
        return self.indices[kind.upper()]

    def kind_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]['kind']
        if name in self.class_scope:
            return self.class_scope[name]['kind']
        return None

    def type_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]['type']
        if name in self.class_scope:
            return self.class_scope[name]['type']
        return None

    def index_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]['index']
        if name in self.class_scope:
            return self.class_scope[name]['index']
        return None


class VMWriter:
    KIND_TO_SEGMENT = {
        'STATIC': 'static',
        'FIELD': 'this',
        'ARG': 'argument',
        'VAR': 'local'
    }

    def __init__(self, output_file):
        self.f = open(output_file, 'w', encoding='utf-8')
        self.line_count = 0

    def _write(self, text):
        self.f.write(text + "\n")
        self.line_count += 1

    def write_push(self, segment, index):
        seg = self.KIND_TO_SEGMENT.get(segment.upper(), segment.lower())
        self._write(f"push {seg} {index}")

    def write_pop(self, segment, index):
        seg = self.KIND_TO_SEGMENT.get(segment.upper(), segment.lower())
        self._write(f"pop {seg} {index}")

    def write_arithmetic(self, command):
        self._write(command.lower())

    def write_label(self, label):
        self._write(f"label {label}")

    def write_goto(self, label):
        self._write(f"goto {label}")

    def write_if(self, label):
        self._write(f"if-goto {label}")

    def write_call(self, name, n_args):
        self._write(f"call {name} {n_args}")

    def write_function(self, name, n_locals):
        self._write(f"function {name} {n_locals}")

    def write_return(self):
        self._write("return")

    def close(self):
        self.f.close()


class CompilationEngine:
    OP_MAP = {
        '+': 'add', '-': 'sub', '&': 'and', '|': 'or',
        '<': 'lt', '>': 'gt', '=': 'eq'
    }

    def __init__(self, tokenizer, vm_writer):
        self.tokenizer = tokenizer
        self.vm = vm_writer
        self.symbols = SymbolTable()
        self.class_name = ""
        self.label_counter = 0

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
            self.compile_class()

    def _new_label(self, prefix="L"):
        label = f"{self.class_name}_{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def _eat(self, expected=None):
        token = self.tokenizer.current_token
        if expected is not None and token != expected:
            raise SyntaxError(f"Expected '{expected}', got '{token}'")
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
        return token

    def compile_class(self):
        self._eat('class')
        self.class_name = self._eat()
        self._eat('{')

        while self.tokenizer.current_token in ('static', 'field'):
            self.compile_class_var_dec()

        while self.tokenizer.current_token in ('constructor', 'function', 'method'):
            self.compile_subroutine()

        self._eat('}')

    def compile_class_var_dec(self):
        kind = self._eat()
        var_type = self._eat()
        var_name = self._eat()
        self.symbols.define(var_name, var_type, kind)

        while self.tokenizer.current_token == ',':
            self._eat(',')
            var_name = self._eat()
            self.symbols.define(var_name, var_type, kind)

        self._eat(';')

    def compile_subroutine(self):
        self.symbols.start_subroutine()
        sub_type = self._eat()
        self._eat()
        sub_name = self._eat()

        if sub_type == 'method':
            self.symbols.define('this', self.class_name, 'ARG')

        self._eat('(')
        self.compile_parameter_list()
        self._eat(')')

        self._eat('{')
        while self.tokenizer.current_token == 'var':
            self.compile_var_dec()

        n_locals = self.symbols.var_count('VAR')
        self.vm.write_function(f"{self.class_name}.{sub_name}", n_locals)

        if sub_type == 'constructor':
            n_fields = self.symbols.var_count('FIELD')
            self.vm.write_push('constant', n_fields)
            self.vm.write_call('Memory.alloc', 1)
            self.vm.write_pop('pointer', 0)
        elif sub_type == 'method':
            self.vm.write_push('argument', 0)
            self.vm.write_pop('pointer', 0)

        self.compile_statements()
        self._eat('}')

    def compile_parameter_list(self):
        if self.tokenizer.current_token != ')':
            var_type = self._eat()
            var_name = self._eat()
            self.symbols.define(var_name, var_type, 'ARG')

            while self.tokenizer.current_token == ',':
                self._eat(',')
                var_type = self._eat()
                var_name = self._eat()
                self.symbols.define(var_name, var_type, 'ARG')

    def compile_var_dec(self):
        self._eat('var')
        var_type = self._eat()
        var_name = self._eat()
        self.symbols.define(var_name, var_type, 'VAR')

        while self.tokenizer.current_token == ',':
            self._eat(',')
            var_name = self._eat()
            self.symbols.define(var_name, var_type, 'VAR')

        self._eat(';')

    def compile_statements(self):
        while self.tokenizer.current_token in ('let', 'if', 'while', 'do', 'return'):
            stmt = self.tokenizer.current_token
            if stmt == 'let':
                self.compile_let()
            elif stmt == 'if':
                self.compile_if()
            elif stmt == 'while':
                self.compile_while()
            elif stmt == 'do':
                self.compile_do()
            elif stmt == 'return':
                self.compile_return()

    def compile_let(self):
        self._eat('let')
        var_name = self._eat()
        kind = self.symbols.kind_of(var_name)
        index = self.symbols.index_of(var_name)

        is_array = False
        if self.tokenizer.current_token == '[':
            is_array = True
            self._eat('[')
            self.compile_expression()
            self._eat(']')
            self.vm.write_push(kind, index)
            self.vm.write_arithmetic('add')

        self._eat('=')
        self.compile_expression()
        self._eat(';')

        if is_array:
            self.vm.write_pop('temp', 0)
            self.vm.write_pop('pointer', 1)
            self.vm.write_push('temp', 0)
            self.vm.write_pop('that', 0)
        else:
            self.vm.write_pop(kind, index)

    def compile_if(self):
        else_label = self._new_label("ELSE")
        end_label = self._new_label("IF_END")

        self._eat('if')
        self._eat('(')
        self.compile_expression()
        self._eat(')')
        self.vm.write_arithmetic('not')
        self.vm.write_if(else_label)

        self._eat('{')
        self.compile_statements()
        self._eat('}')
        self.vm.write_goto(end_label)

        self.vm.write_label(else_label)
        if self.tokenizer.current_token == 'else':
            self._eat('else')
            self._eat('{')
            self.compile_statements()
            self._eat('}')

        self.vm.write_label(end_label)

    def compile_while(self):
        exp_label = self._new_label("WHILE_EXP")
        end_label = self._new_label("WHILE_END")

        self.vm.write_label(exp_label)
        self._eat('while')
        self._eat('(')
        self.compile_expression()
        self._eat(')')
        self.vm.write_arithmetic('not')
        self.vm.write_if(end_label)

        self._eat('{')
        self.compile_statements()
        self._eat('}')
        self.vm.write_goto(exp_label)

        self.vm.write_label(end_label)

    def compile_do(self):
        self._eat('do')
        self._compile_subroutine_call()
        self._eat(';')
        self.vm.write_pop('temp', 0)

    def compile_return(self):
        self._eat('return')
        if self.tokenizer.current_token != ';':
            self.compile_expression()
        else:
            self.vm.write_push('constant', 0)
        self._eat(';')
        self.vm.write_return()

    def compile_expression(self):
        self.compile_term()
        while self.tokenizer.current_token in ('+', '-', '*', '/', '&', '|', '<', '>', '='):
            op = self._eat()
            self.compile_term()
            if op in self.OP_MAP:
                self.vm.write_arithmetic(self.OP_MAP[op])
            elif op == '*':
                self.vm.write_call('Math.multiply', 2)
            elif op == '/':
                self.vm.write_call('Math.divide', 2)

    def compile_term(self):
        t_type = self.tokenizer.token_type()
        token = self.tokenizer.current_token

        if t_type == 'INT_CONST':
            self.vm.write_push('constant', self._eat())

        elif t_type == 'STRING_CONST':
            s = self._eat()
            self.vm.write_push('constant', len(s))
            self.vm.write_call('String.new', 1)
            for ch in s:
                self.vm.write_push('constant', ord(ch))
                self.vm.write_call('String.appendChar', 2)

        elif t_type == 'KEYWORD':
            kw = self._eat()
            if kw == 'true':
                self.vm.write_push('constant', 0)
                self.vm.write_arithmetic('not')
            elif kw in ('false', 'null'):
                self.vm.write_push('constant', 0)
            elif kw == 'this':
                self.vm.write_push('pointer', 0)

        elif token == '(':
            self._eat('(')
            self.compile_expression()
            self._eat(')')

        elif token in ('-', '~'):
            op = self._eat()
            self.compile_term()
            self.vm.write_arithmetic('neg' if op == '-' else 'not')

        elif t_type == 'IDENTIFIER':
            next_type, next_token = self.tokenizer.peek()
            if next_token == '[':
                var_name = self._eat()
                self._eat('[')
                self.compile_expression()
                self._eat(']')
                self.vm.write_push(self.symbols.kind_of(var_name), self.symbols.index_of(var_name))
                self.vm.write_arithmetic('add')
                self.vm.write_pop('pointer', 1)
                self.vm.write_push('that', 0)
            elif next_token in ('(', '.'):
                self._compile_subroutine_call()
            else:
                var_name = self._eat()
                self.vm.write_push(self.symbols.kind_of(var_name), self.symbols.index_of(var_name))

    def _compile_subroutine_call(self):
        first_name = self._eat()
        n_args = 0

        if self.tokenizer.current_token == '.':
            self._eat('.')
            sub_name = self._eat()
            var_type = self.symbols.type_of(first_name)

            if var_type is not None:
                self.vm.write_push(self.symbols.kind_of(first_name), self.symbols.index_of(first_name))
                full_name = f"{var_type}.{sub_name}"
                n_args = 1
            else:
                full_name = f"{first_name}.{sub_name}"
        else:
            self.vm.write_push('pointer', 0)
            full_name = f"{self.class_name}.{first_name}"
            n_args = 1

        self._eat('(')
        n_args += self.compile_expression_list()
        self._eat(')')
        self.vm.write_call(full_name, n_args)

    def compile_expression_list(self):
        count = 0
        if self.tokenizer.current_token != ')':
            self.compile_expression()
            count += 1
            while self.tokenizer.current_token == ',':
                self._eat(',')
                self.compile_expression()
                count += 1
        return count


def compile_file(jack_path):
    base_name, _ = os.path.splitext(jack_path)
    vm_path = base_name + '.vm'
    tokenizer = JackTokenizer(jack_path)
    vm_writer = VMWriter(vm_path)
    CompilationEngine(tokenizer, vm_writer)
    vm_writer.close()
    print(f"Compiled: {jack_path} -> {vm_path} ({vm_writer.line_count} lines)")


def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)

    _, target = sys.argv
    if os.path.isfile(target) and target.endswith('.jack'):
        compile_file(target)
    elif os.path.isdir(target):
        for filename in os.listdir(target):
            if filename.endswith('.jack'):
                compile_file(os.path.join(target, filename))
    else:
        print("Error: Invalid path.")
        sys.exit(1)


if __name__ == '__main__':
    main()
