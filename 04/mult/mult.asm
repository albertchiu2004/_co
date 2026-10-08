

    @R2
    M=0         // R2 = 0 (初始化結果為 0)

    @R0
    D=M
    @END
    D;JEQ       // 如果 R0 == 0，直接結束

    @R1
    D=M
    @END
    D;JEQ       // 如果 R1 == 0，直接結束

    @i
    M=0         // i = 0 (計數器初始化)

(LOOP)
    @i
    D=M
    @R1
    D=D-M
    @END
    D;JGE       // 如果 i >= R1，跳出迴圈

    @R0
    D=M
    @R2
    M=M+D       // R2 = R2 + R0

    @i
    M=M+1       // i = i + 1
    @LOOP
    0;JMP       // 重複迴圈

(END)
    @END
    0;JMP       // 無限迴圈停止程式