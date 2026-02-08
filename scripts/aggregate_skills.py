import glob
import os
import re


def parse_skill_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if frontmatter_match:
        yaml_text = frontmatter_match.group(1)
        body = frontmatter_match.group(2)

        # Simple yaml parse (avoiding pyyaml dependency if not installed, though it likely is)
        name_match = re.search(r'name:\s*["\']?([\w_]+)["\']?', yaml_text)
        desc_match = re.search(r'description:\s*["\']?(.*?)["\']?\s*$', yaml_text, re.MULTILINE | re.DOTALL)

        name = name_match.group(1) if name_match else "Unknown"
        # Clean up description (remove newlines if it was multiline in yaml)
        description = desc_match.group(1).replace("\n", " ").strip() if desc_match else "No description"

        return {"name": name, "description": description, "body": body, "path": filepath}
    return None


def generate_mermaid(skills):
    # This is a heuristic generation. A real one would require analyzing the code or explicit dependencies.
    # We will group them by domain and link Runbooks to Specs.

    lines = ["graph TD"]

    # Define Subgraphs
    domains = {
        "Overall": ["overall", "design_loop", "stage2_7"],
        "Aerodynamics": ["aero"],
        "Weights": ["weights"],
        "Propulsion": ["propulsion"],
        "Performance": ["performance", "constraints"],
        "Geometry": ["shape"],
        "Stability": ["stability"],
        "Structures": ["structures"],
    }

    # Helper to find domain
    def get_domain(skill_name):
        for d, keywords in domains.items():
            for k in keywords:
                if k in skill_name:
                    return d
        return "Other"

    # Group skills
    domain_groups = {}
    for skill in skills:
        d = get_domain(skill["name"])
        if d not in domain_groups:
            domain_groups[d] = []
        domain_groups[d].append(skill["name"])

    # Draw subgraphs
    for domain, skill_names in domain_groups.items():
        lines.append(f"    subgraph {domain}")
        for name in skill_names:
            # Shorten name for display
            display_name = name.replace("fixed_wing_", "")
            lines.append(f'        {name}["{display_name}"]')
        lines.append("    end")

    # Add inferred connections
    # Overall -> Design Loop
    lines.append("    fixed_wing_overall_sizing_runbook --> fixed_wing_design_loop_runbook")
    lines.append("    fixed_wing_overall_sizing_spec -.-> fixed_wing_overall_sizing_runbook")

    # Design Loop -> Submodules
    submodules = ["weights", "aero", "propulsion", "performance", "stability", "structures"]
    for sub in submodules:
        # Find runbooks for these
        runbook = f"fixed_wing_{sub}_runbook"
        if any(s["name"] == runbook for s in skills):
            lines.append(f"    fixed_wing_design_loop_runbook --> {runbook}")

    # Spec -> Runbook links
    for skill in skills:
        if "runbook" in skill["name"]:
            spec_name = skill["name"].replace("runbook", "spec")
            if any(s["name"] == spec_name for s in skills):
                lines.append(f"    {spec_name} -.-> {skill['name']}")

    # Constraints -> Overall
    lines.append("    fixed_wing_constraints_runbook --> fixed_wing_overall_sizing_runbook")

    return "\n".join(lines)


def main():
    skill_files = glob.glob(".trae/skills/**/SKILL.md", recursive=True)
    skills = []

    for f in skill_files:
        data = parse_skill_md(f)
        if data:
            skills.append(data)

    # Sort by name
    skills.sort(key=lambda x: x["name"])

    output_content = "# Aircraft Design Skill Landscape Analysis\n\n"

    output_content += "## 1. Skill Summary\n\n"
    output_content += "| Skill Name | Description |\n"
    output_content += "| :--- | :--- |\n"
    for s in skills:
        # Escape pipes in description
        desc = s["description"].replace("|", "\\|")
        output_content += f"| `{s['name']}` | {desc} |\n"

    output_content += "\n## 2. Functional Map (Mermaid)\n\n"
    output_content += "```mermaid\n"
    output_content += generate_mermaid(skills)
    output_content += "\n```\n\n"

    output_content += "## 3. Detailed Skill Contents\n\n"
    for s in skills:
        output_content += f"### {s['name']}\n\n"
        output_content += f"> **Path**: `{s['path']}`\n\n"
        output_content += s["body"] + "\n\n---\n\n"

    output_path = "docs/skill_landscape_analysis.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_content)

    print(f"Successfully aggregated {len(skills)} skills into {output_path}")


if __name__ == "__main__":
    main()
