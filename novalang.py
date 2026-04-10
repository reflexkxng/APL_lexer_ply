import sys
import argparse
from APL_semantic_ply_ import compile_novalang

def process_source(source_code, show_details=True, wait_phases=True):
    """Run lexical, syntactic, and semantic phases on the source code."""
    try:
        # compile_novalang runs the pipeline and handles its own printing
        compile_novalang(
            source=source_code, 
            print_tokens=show_details, 
            print_ast=show_details, 
            print_report=show_details,
            interactive_pause=wait_phases
        )
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Pipeline failed: {e}")

def run_repl():
    """Interactive console for NovaLang."""
    print("NovaLang Interactive Console (REPL)")
    print("Type 'exit' or 'quit' to close.")
    print("=" * 60)
    
    while True:
        try:
            line = input("\nnova> ")
            if line.strip().lower() in ['exit', 'quit']:
                break
            if not line.strip():
                continue
            
            process_source(line, show_details=True)
            
        except KeyboardInterrupt:
            print("\nExiting NovaLang REPL...")
            break
        except EOFError:
            break

def main():
    parser = argparse.ArgumentParser(description="NovaLang Compiler Pipeline")
    parser.add_argument(
        "file", 
        nargs="?", 
        help="Path to the NovaLang source file (.nova)"
    )
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true", 
        help="Only show final output (hide token/AST dumps)"
    )
    
    args = parser.parse_args()

    if args.file:
        # 1. Read from an input file
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            print(f"File: {args.file}")
            # Run the lexical, syntactic, and semantic phases
            process_source(source_code, show_details=not args.quiet)
            
        except FileNotFoundError:
            print(f"Error: Could not find file '{args.file}'")
            sys.exit(1)
    else:
        # 2. Entered into a console
        run_repl()

if __name__ == "__main__":
    main()
