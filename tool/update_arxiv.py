from datetime import datetime
from pathlib import Path
from turtle import color

import arxiv
import jsonlines
import matplotlib.pyplot as plt


# read from cache if it exists
arxiv_cache = Path("arxiv_visual_reasoning.jsonl")
papers = {}
if arxiv_cache.exists():
    try:
        with jsonlines.open(arxiv_cache) as reader:
            for paper in reader:
                papers[paper["entry_id"]] = paper
    except:
        pass


# search for papers
client = arxiv.Client(page_size=1000, delay_seconds=3, num_retries=3)
updated_papers = []
for paper in client.results(
    arxiv.Search(
        query=(
            "all:%22visual reasoning%22"
            " OR all:%22visual abductive reasoning%22"
            " OR all:%22visual abstract reasoning%22"
            " OR all:%22visual commonsense reasoning%22"
            " OR all:%22visual spatial reasoning%22"
        ),
        sort_by=arxiv.SortCriterion.LastUpdatedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
):
    entry_id = paper.entry_id.split("/")[-1].split("v")[0]
    updated = datetime.strftime(paper.updated, "%Y-%m-%d %H:%M:%S")
    if entry_id in papers and updated == papers[entry_id]["updated"]:
        continue
    else:
        papers[entry_id] = paper.__dict__
        papers[entry_id] = {
            "entry_id": entry_id,
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "published": datetime.strftime(
                paper.published, "%Y-%m-%d %H:%M:%S"
            ),
            "updated": updated,
            "summary": paper.summary,
            "comment": paper.comment,
            "links": [
                link.href for link in paper.links if "arxiv" not in link.href
            ],
        }
        updated_papers.append(entry_id)


# save paper to cache
paper_list = sorted(
    list(papers.values()), key=lambda x: x["updated"], reverse=True
)
with jsonlines.open(arxiv_cache, "w") as writer:
    writer.write_all(paper_list)
print(
    f"Found {len(updated_papers)} new papers. Total papers: {len(paper_list)}"
)

# drawing the trends in the number of papers over time
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["savefig.pad_inches"] = 0.1
plt.rcParams["font.family"] = "Helvetica"
plt.rcParams['font.size'] = 14
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 14
plt.rcParams['figure.titlesize'] = 16


years_count = {}
for paper in paper_list:
    year = paper["published"].split("-")[0]
    if year in years_count:
        years_count[year] += 1
    else:
        years_count[year] = 1
sorted_years_count = sorted(years_count.items(), key=lambda x: x[0])
years, count = zip(*sorted_years_count)
plt.plot(years, count, marker="^", color="black")
# plt.title(
#     "Visual reasoning papers on arXiv over time"
# )
plt.xlabel("Year")
plt.ylabel("#papers")
plt.savefig("arxiv_trends_year.png")


# render to markdown
with open("arxiv_visual_reasoning.md", "w") as f:
    f.write(
        f"""
# Visual Reasoning Papers on Arxiv

This is a list of papers in the field of visual reasoning
and is automatically generated by [update_arxiv.py](./tool/update_arxiv.py).


<img src="./arxiv_trends_year.png" width="480" />


Last update: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

___

"""
    )
    for paper in paper_list:
        f.write(
            f"## [{paper['title']}](https://arxiv.org/pdf/{paper['entry_id']})"
        )
        if paper["entry_id"] in updated_papers:
            f.write(" [New]")
        f.write(f"\n\n")
        f.write(f"*{', '.join(paper['authors'])}*\n\n")
        f.write(f"**Abstract:** {paper['summary']}\n\n")
        if paper["comment"]:
            f.write(f"**comment:** *{paper['comment']}*\n\n")
        if len(paper["links"]) > 0:
            f.write(f"**links:** {', '.join(paper['links'])}\n\n")
        f.write(
            f"**published:** *{paper['published']}*, **updated:** *{paper['updated']}*\n\n"
        )
        f.write("<br>\n\n")
