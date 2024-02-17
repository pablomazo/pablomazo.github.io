import json
import os
import re

import yaml
from jinja2 import Environment, FileSystemLoader


def finalize_tex(x):
    if type(x) is str:
        x = re.sub(r"\<sup>(.+?)\<\/sup>", r"$^{\1}$", x)
        x = re.sub(r"\<sub>(.+?)\<\/sub>", r"$_{\1}$", x)
        x = re.sub(r"\*\*(.+?)\*\*", r"{\\bf \1}", x)
        x = re.sub(r"\*(.+?)\*", r"{\\it \1}", x)
        x = re.sub(r"\[(.+?)\]\((.+?)\)", r"\\href{\2}{\1}", x)
        x = x.replace("\\rightarrow", "$\\rightarrow$")
        x = x.replace("-", "--")
    return x


def finalize_html(x):
    if type(x) is str:
        x = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", x)
        x = re.sub(r"\*(.+?)\*", r"<i>\1</i>", x)
        x = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', x)
        x = x.replace("\\rightarrow", "→")
    return x


def process_congress(data):
    c = data["congress"]
    for key in ["poster", "communication", "invited"]:
        c[key] = sorted(c[key], key=lambda x: x["year"], reverse=True)
    data["congress"] = c
    return data


def get_publications(raw_publications):
    publications = []

    def get_authors(authors, max_authors=7):
        author_list = [
            " ".join(
                [
                    *(f"{name[0]}." for name in auth["given"].split()),
                    *(
                        (f"{auth['non-dropping-particle']}",)
                        if "non-dropping-particle" in auth.keys()
                        else ()
                    ),
                    f"{auth['family']}",
                ]
            )
            for auth in authors
        ]

        author_list = [
            "**PMS**" if (a == "P. del Mazo-Sevillano" or a == "P. del Mazo") else a
            for a in author_list
        ]
        return (
            ", ".join(author for author in author_list)
            if len(author_list) < max_authors
            else f"{author_list[0]} et al."
        )

    for paper in raw_publications:
        authors = get_authors(paper["author"])
        title = paper["title"]
        url = "https://doi.org/" + paper["DOI"]
        ref = (
            "["
            + f"*{paper['container-title']}* "
            + f"**{(paper['volume'] if 'volume' in paper.keys() else ' ')}**"
            + f", {(paper['page'] if 'page' in paper.keys() else '')}"
            + f"]({url})"
            f" ({paper['issued']['date-parts'][0][0]})"
        )
        publications.append(f"{title}: {authors}, {ref}")
    return publications


def main():
    for fmt in ["tex", "html"]:
        if fmt == "tex":
            finalize = finalize_tex
            template_file = "cv.tex.in"
            output_file = "./build/cv.tex"
        elif fmt == "html":
            finalize = finalize_html
            template_file = "cv.html.in"
            output_file = "./build/index.html"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        # Load the template environment
        env = Environment(loader=FileSystemLoader("./data"), finalize=finalize)

        # Load the template file
        template = env.get_template(template_file)

        # Define data to be passed to the template
        with open("./data/cv.yaml", "r") as f:
            data = yaml.safe_load(f)

        data = process_congress(data)

        with open("./data/references.json", "r") as f:
            publications = json.load(f)

        data["publications"] = get_publications(publications)
        # data = process_positions_tex(data)
        # Render the template with the data
        rendered = template.render(data)

        # Save the rendered tex to a file
        with open(output_file, "w") as f:
            f.write(rendered)


if __name__ == "__main__":
    print(os.getcwd())
    main()
