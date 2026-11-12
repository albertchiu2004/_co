class Parser:
    def __init__(self, filepath):
        self.lines = []
        self.current_index = -1
        self.current_command = ""

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # 去除註解 (// 後面的內容) 與前後空白
                clean_line = line.split('//')[0].strip()
                if clean_line:
                    self.lines.append(clean_line)

    def has_more_lines(self):
        return self.current_index + 1 < len(self.lines)

    def advance(self):
        self.current_index += 1
        self.current_command = self.lines[self.current_index]

    def reset(self):
        self.current_index = -1
        self.current_command = ""

    def instruction_type(self):
        if self.current_command.startswith('@'):
            return 'A_INSTRUCTION'
        elif self.current_command.startswith('(') and self.current_command.endswith(')'):
            return 'L_INSTRUCTION'
        else:
            return 'C_INSTRUCTION'

    def symbol(self):
        if self.instruction_type() == 'A_INSTRUCTION':
            return self.current_command[1:]
        elif self.instruction_type() == 'L_INSTRUCTION':
            return self.current_command[1:-1]
        return None

    def dest(self):
        if self.instruction_type() == 'C_INSTRUCTION' and '=' in self.current_command:
            return self.current_command.split('=')[0].strip()
        return 'null'

    def comp(self):
        if self.instruction_type() == 'C_INSTRUCTION':
            temp = self.current_command
            if '=' in temp:
                temp = temp.split('=')[1]
            if ';' in temp:
                temp = temp.split(';')[0]
            return temp.strip()
        return None

    def jump(self):
        if self.instruction_type() == 'C_INSTRUCTION' and ';' in self.current_command:
            return self.current_command.split(';')[1].strip()
        return 'null'
