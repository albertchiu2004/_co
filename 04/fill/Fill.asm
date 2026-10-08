
(START)
    @KBD
    D=M
    @SET_BLACK
    D;JNE       // 如果有按鍵被按下 (KBD != 0)，跳至設定黑色
    @SET_WHITE
    D;JEQ       // 如果沒有按鍵被按下 (KBD == 0)，跳至設定白色

(SET_BLACK)
    @color
    M=-1        // 將變數 color 設為 -1 (二進位全 1，代表全黑)
    @INIT_SCREEN
    0;JMP

(SET_WHITE)
    @color
    M=0         // 將變數 color 設為 0 (二進位全 0，代表全白)
    @INIT_SCREEN
    0;JMP

(INIT_SCREEN)
    @SCREEN
    D=A
    @addr
    M=D         // addr 指向螢幕記憶體起始位置 (16384)

    @8192
    D=A
    @count
    M=D         // count = 8192 (Hack 螢幕總共需要 8192 個 16-bit 字元來填滿)

(DRAW_LOOP)
    @count
    D=M
    @START
    D;JLE       // 若 count <= 0，代表螢幕已填滿，跳回主迴圈繼續監聽鍵盤

    @color
    D=M         // 取得剛才設定的顏色（0 或 -1）
    @addr
    A=M
    M=D         // 將顏色寫入目前的螢幕記憶體位置

    @addr
    M=M+1       // 將螢幕指標指向下一個字元
    @count
    M=M-1       // 計數器減 1

    @DRAW_LOOP
    0;JMP       // 繼續迴圈填滿下一個畫素區塊