import re
import matplotlib.pyplot as plt
import sys
import os

def verify_formulas(markdown_file):
    if not os.path.exists(markdown_file):
        print(f"Error: File {markdown_file} not found.")
        return False

    with open(markdown_file, 'r') as f:
        content = f.read()

    # Regex for block math $$...$$
    block_math_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    # Regex for inline math $...$ (simplified, might match non-math $ if not careful)
    # Avoiding matches like $100
    inline_math_pattern = re.compile(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)')

    block_matches = block_math_pattern.findall(content)
    inline_matches = inline_math_pattern.findall(content)

    all_formulas = block_matches + inline_matches
    
    print(f"Found {len(all_formulas)} formulas in {markdown_file}")
    
    failures = 0
    
    # Create a hidden figure for rendering
    fig = plt.figure()
    
    for i, formula in enumerate(all_formulas):
        formula = formula.strip()
        if not formula:
            continue
            
        try:
            # Try to render the formula
            # We wrap it in $...$ for matplotlib if it's not already
            # But matplotlib text expects the string to *contain* math, or be math.
            # Usually we can just render it.
            
            # Clean up newlines for block math
            clean_formula = formula.replace('\n', ' ')
            
            # Matplotlib requires $ for math mode usually
            render_str = f"${clean_formula}$"
            
            fig.text(0.5, 0.5, render_str)
            # We need to draw to trigger the renderer
            fig.canvas.draw()
            fig.clear() # Clear for next
            # print(f"[OK] Formula {i+1}")
        except Exception as e:
            print(f"[ERROR] Formula {i+1} failed to render:")
            print(f"Source: {formula}")
            print(f"Error: {e}")
            failures += 1
            
    plt.close(fig)
    
    print("-" * 30)
    print(f"Summary: {len(all_formulas) - failures} passed, {failures} failed.")
    
    return failures == 0

if __name__ == "__main__":
    md_file = "technical_roadmap_report.md"
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
        
    success = verify_formulas(md_file)
    sys.exit(0 if success else 1)
