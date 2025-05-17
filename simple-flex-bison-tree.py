import re
from collections import namedtuple

# ====== Token definition =======
Token = namedtuple("Token", ["type", "value"])

# ====== Lexer =======
token_specification = [
    ('COMMENT',   r'\(\*.*?\*\)'),  # комментарии вида (* ... *)
    ('ASSIGN',    r':='),           # :=
    ('OP_NOT',    r'not'),
    ('OP_AND',    r'and'),
    ('OP_OR',     r'or'),
    ('OP_XOR',    r'xor'),
    ('LPAREN',    r'\('),
    ('RPAREN',    r'\)'),
    ('SEMICOLON', r';'),
    ('CONST',     r'\btrue\b|\bfalse\b'),
    ('HEX',       r'\b[0-9][0-9a-fA-F]*\b'),  # шестнадцатеричные числа
    ('ROMAN',     r'\b[IVXLCDM]+\b'),     # римские числа
    ('IDENT',     r'\b[a-zA-Z_][a-zA-Z_0-9]{0,31}\b'),
    ('SKIP',      r'[ \t\n]+'),     # пропуск пробелов и табуляции
    ('MISMATCH',  r'.'),            # ошибки
]

token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
master_pat = re.compile(token_regex, re.DOTALL)

def lex(text):
    tokens = []
    for mo in master_pat.finditer(text):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'Лексическая ошибка: {value}')
        else:
            tokens.append(Token(kind, value))
    return tokens

# ====== Parser =======

class Node:
    def __init__(self, name, children=None, token=None):
        self.name = name
        self.children = children or []
        self.token = token

    def display(self, prefix='', is_tail=True):
        connector = '└── ' if is_tail else '├── '
        print(prefix + connector + self.name)
        new_prefix = prefix + ('    ' if is_tail else '│   ')
        for i, child in enumerate(self.children):
            child.display(new_prefix, i == len(self.children) - 1)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def match(self, expected_type):
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == expected_type:
            token = self.tokens[self.pos]
            self.pos += 1
            return Node(token.value, token=token)
        else:
            expected = expected_type
            actual = self.tokens[self.pos].type if self.pos < len(self.tokens) else 'EOF'
            raise RuntimeError(f'Ожидалось {expected}, найдено {actual}')

    def parse(self):
        return self.S()

    def S(self):
        children = [Node("a", [self.match("IDENT")])]
        children.append(self.match("ASSIGN"))
        children.append(self.F())
        children.append(self.match("SEMICOLON"))
        return Node("S", children)

    def F(self):
        node = self.T()
        while self.peek("OP_OR") or self.peek("OP_XOR"):
            op = self.match(self.tokens[self.pos].type)
            right = self.T()
            node = Node("F", [node, op, right])
        return node

    def T(self):
        node = self.E()
        while self.peek("OP_AND"):
            op = self.match("OP_AND")
            right = self.E()
            node = Node("T", [node, op, right])
        return node

    def E(self):
        if self.peek("LPAREN"):
            lpar = self.match("LPAREN")
            f = self.F()
            rpar = self.match("RPAREN")
            return Node("E", [lpar, f, rpar])
        elif self.peek("OP_NOT"):
            not_ = self.match("OP_NOT")
            lpar = self.match("LPAREN")
            f = self.F()
            rpar = self.match("RPAREN")
            return Node("E", [not_, lpar, f, rpar])
        elif self.peek("IDENT") or self.peek("CONST") or self.peek("ROMAN") or self.peek("HEX"):
            token = self.match(self.tokens[self.pos].type)
            return Node("E", [Node("a", [token])])
        else:
            raise RuntimeError("Ожидалось выражение")

    def peek(self, token_type):
        return self.pos < len(self.tokens) and self.tokens[self.pos].type == token_type


# ====== Main =======
if __name__ == "__main__":
    try:
        with open("input.txt", encoding="utf-8") as f:
            text = f.read()

        tokens = lex(text)

        print("Таблица лексем:")
        print("================")
        for t in tokens:
            print(f"{t.type}: {t.value}")

        parser = Parser(tokens)
        print("\nДерево разбора:")
        print("================")
        tree = parser.parse()
        tree.display()

    except RuntimeError as e:
        print(f"Ошибка: {e}")
    except FileNotFoundError:
        print("Файл 'input.txt' не найден.")

