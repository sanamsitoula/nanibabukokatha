# Graph Report - C:\claude_projects\nanibabukokatha  (2026-09-14)

## Corpus Check
- Large corpus: 28 files · ~1,092,602 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 15 nodes · 14 edges · 4 communities (3 shown, 1 thin omitted)
- Extraction: 86% EXTRACTED · 7% INFERRED · 7% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Nepali Story Ideas
- Prompt3 Character
- Nepali Story Ideas

## God Nodes (most connected - your core abstractions)
1. `दूधमा पानी, मनमा ढुङ्गा (Water in the Milk)` - 4 edges
2. `Category: गाउँले जीवन (Village Life) - 20 stories` - 2 edges
3. `Root .docx drafts (prompt1-4)` - 1 edges
4. `Category: बालबालिका नैतिक कथा (Children's Moral) - 13 stories` - 1 edges
5. `Category: जनावर कथा (Animal Stories) - 10 stories` - 1 edges
6. `Category: पारिवारिक भावनात्मक कथा (Family/Emotional) - 5 stories` - 1 edges
7. `Category: जादुई नैतिक कथा (Magical Moral) - 2 stories` - 1 edges
8. `Character reference art (character/ folder)` - 1 edges
9. `Test video clips (introduce.mp4, Last_Scene.mp4)` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Hyperedges (group relationships)
- **Five story categories (50 ideas)** — category_village_life, category_childrens_moral, category_animal, category_family_emotional, category_magical_moral [EXTRACTED]

## Communities (4 total, 1 thin omitted)

### Community 0 - "Nepali Story Ideas"
Cohesion: 0.40
Nodes (4): Category: जनावर कथा (Animal Stories) - 10 stories, Category: बालबालिका नैतिक कथा (Children's Moral) - 13 stories, Category: पारिवारिक भावनात्मक कथा (Family/Emotional) - 5 stories, Category: जादुई नैतिक कथा (Magical Moral) - 2 stories

### Community 1 - "Prompt3 Character"
Cohesion: 0.40
Nodes (3): Root .docx drafts (prompt1-4), Character reference art (character/ folder), Test video clips (introduce.mp4, Last_Scene.mp4)

## Ambiguous Edges - Review These
- `prompt4.md` → `prompt4 copy.md`  [AMBIGUOUS]
  1.1 दूधमा पानी, मनमा ढुङ्गा/prompt4 copy.md · relation: semantically_similar_to

## Knowledge Gaps
- **7 isolated node(s):** `Root .docx drafts (prompt1-4)`, `Category: बालबालिका नैतिक कथा (Children's Moral) - 13 stories`, `Category: जनावर कथा (Animal Stories) - 10 stories`, `Category: पारिवारिक भावनात्मक कथा (Family/Emotional) - 5 stories`, `Category: जादुई नैतिक कथा (Magical Moral) - 2 stories` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `prompt4.md` and `prompt4 copy.md`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `दूधमा पानी, मनमा ढुङ्गा (Water in the Milk)` connect `Nepali Story Ideas` to `Nepali Story Ideas`, `Prompt3 Character`?**
  _High betweenness centrality (0.451) - this node is a cross-community bridge._
- **What connects `Root .docx drafts (prompt1-4)`, `Category: बालबालिका नैतिक कथा (Children's Moral) - 13 stories`, `Category: जनावर कथा (Animal Stories) - 10 stories` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._