# 🌌 NovaLang

**NovaLang** is a custom-designed programming language built from the ground up using Python and the **PLY (Python Lex-Yacc)** framework. It features a robust compilation pipeline including lexical analysis, parsing, semantic verification, and an integrated development environment (IDE) with AI-powered code analysis.

---

## ✨ Key Features

- **Custom Syntax**: A clean, block-based syntax that replaces traditional braces with `end` keywords.
- **Full Compiler Pipeline**:
  - **Lexer**: Tokenizes source code with detailed error reporting.
  - **Parser**: Builds a Concrete Syntax Tree (CST) and handles operator precedence.
  - **Semantic Analyzer**: Ensures type safety and variable scope resolution.
- **Modern IDE**: A high-definition, borderless dark-mode IDE built with Tkinter.
- **AI Intelligence Engine**: Integrated with **Groq AI** to provide real-time code validation, logic summaries, and Python-equivalent comparisons.
- **REPL & CLI**: Support for interactive console sessions and direct file execution.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PLY library
- Groq library (for AI features)

```bash
pip install ply groq python-dotenv
```

### Running the IDE (GUI)
Launch the modern development environment:
```bash
python APL_ui_ply_.py
```

### Running the Compiler (CLI)
Execute a `.nova` file directly:
```bash
python novalang.py samples/your_file.nova
```
Or enter the interactive REPL:
```bash
python novalang.py
```

---

## 📝 Syntax at a Glance

NovaLang is designed to be readable and structured. Here is a simple example:

```nova
-- This is a NovaLang script
let string greeting = "Welcome to NovaLang"
display greeting

let int count = 10
if count > 5
    display "Count is high"
else
    display "Count is low"
end

func add(int a, int b)
    return a + b
end
```

---

## 📦 Project Structure

- `APL_lexer_ply_.py`: Lexical analysis configuration.
- `APL_parser_ply_.py`: Grammar rules and parsing logic.
- `APL_semantic_ply_.py`: Semantic checks and variable management.
- `APL_interpreter_ply_.py`: Core execution logic.
- `APL_ui_ply_.py`: Tkinter-based HD IDE.
- `novalang.py`: CLI entry point.

---

## 🛠 License
This project is licensed under the MIT License.