import sys
import os
from Parser import Parser
from Code import Code
from SymbolTable import SymbolTable

def main():
    if len(sys.argv) != 2:
        print("使用方式: python HackAssembler.py <檔案路徑.asm>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = os.path.splitext(input_path)[0] + '.hack'

    parser = Parser(input_path)
    code = Code()
    symbol_table = SymbolTable()

    # 第一次掃描 (First Pass): 記錄所有標籤 (L_INSTRUCTION) 的 ROM 位址
    rom_address = 0
    while parser.has_more_lines():
        parser.advance()
        inst_type = parser.instruction_type()
        if inst_type == 'L_INSTRUCTION':
            symbol_table.add_entry(parser.symbol(), rom_address)
        else:
            rom_address += 1

    # 重置讀取指標，準備第二次掃描
    parser.reset()
    ram_address = 16
    output_lines = []

    # 第二次掃描 (Second Pass): 翻譯 A-指令與 C-指令
    while parser.has_more_lines():
        parser.advance()
        inst_type = parser.instruction_type()

        if inst_type == 'A_INSTRUCTION':
            symbol = parser.symbol()
            if symbol.isdigit():
                address = int(symbol)
            else:
                if not symbol_table.contains(symbol):
                    symbol_table.add_entry(symbol, ram_address)
                    ram_address += 1
                address = symbol_table.get_address(symbol)
            binary_code = f"0{address:015b}"
            output_lines.append(binary_code)

        elif inst_type == 'C_INSTRUCTION':
            d_bits = code.dest(parser.dest())
            c_bits = code.comp(parser.comp())
            j_bits = code.jump(parser.jump())
            binary_code = f"111{c_bits}{d_bits}{j_bits}"
            output_lines.append(binary_code)

    # 寫入 .hack 檔案
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')

    print(f"組譯完成！輸出檔案：{output_path}")

if __name__ == '__main__':
    main()
