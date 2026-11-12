這是一個使用 **Python 3** 實作的 **Hack 組譯器（Hack Assembler）**，用於將 Nand2Tetris 課程中的 Hack 組合語言（`.asm` 檔案）翻譯為 Hack 硬體平台可執行的 16 位元二進位機器碼（`.hack` 檔案）。

---

##  專案檔案結構
將核心功能拆分為以下 4 個 Python 檔案：
* **`HackAssembler.py`**：主程式。負責處理命令列參數、檔案讀寫，並驅動兩次掃描（Two-pass）組譯流程。
* **`Parser.py`**：指令解析器。負責讀取 `.asm` 檔案、過濾註解（`//`）與多餘空白，並將指令拆解為 `A_INSTRUCTION`、`C_INSTRUCTION` 或 `L_INSTRUCTION` 的基本欄位（`symbol`、`dest`、`comp`、`jump`）。
* **`Code.py`**：二進位編碼器。透過查表方式將解析後的組合語言助記符（Mnemonics）轉換為對應的二進位位元字串。
* **`SymbolTable.py`**：符號表管理器。負責維護預定義符號（如 `R0`–`R15`、`SP`、`SCREEN`、`KBD` 等）、標籤（Label）的 ROM 位址，以及自訂變數（Variable）的 RAM 位址（從位址 `16` 開始配置）。

---

## 執行環境需求

* **Python 3.x**（本專案於 Python 3.12 環境下測試通過）
* 無需安裝任何第三方套件（僅使用 Python 內建的 `sys` 與 `os` 模組）

---

## 使用方式

請開啟終端機（Terminal / PowerShell / CMD），切換至本專案所在目錄（例如 `week10`），並透過命令列傳入目標 `.asm` 檔案的路徑：

```bash
python HackAssembler.py <目標檔案路徑.asm>
```

### 執行範例

* **翻譯同資料夾內的檔案**：
  ```bash
  python HackAssembler.py Add.asm
  ```

* **使用相對路徑翻譯其他資料夾的官方測試檔**：
  ```bash
  python HackAssembler.py ..\06\add\Add.asm
  python HackAssembler.py ..\06\max\Max.\asm
  python HackAssembler.py ..\06\rect\Rect.asm
  python HackAssembler.py ..\06\pong\Pong.asm
  ```

### 輸出說明
程式執行完成後，會在**輸入檔案的同一個資料夾**下自動產生同名但副檔名為 `.hack` 的純文字檔（例如 `..\06\add\Add.hack`），每行皆為 16 位元的 `0` 與 `1` 機器碼。

---

## 測試驗證

本組譯器已通過 Nand2Tetris Project 06 全部官方測試程式驗證（包含無符號與含符號版本）：
* `Add.asm`
* `Max.asm`
* `Rect.asm`
* `Pong.asm`