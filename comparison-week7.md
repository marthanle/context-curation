# Week 7: Comparison of Approaches

## What I noticed

**The VectorDB alone only saw 3 of my 8 notes.** Gemini was overloaded so the Level 2 answer failed, but the retrieval still printed. It grabbed Weeks 1, 4, and 5 and completely missed the Pantry Pal notes, the AI note, and the guest speaker. Any answer built on that would have left out the whole project.

**The graph fixed that gap.** Level 3 was the first approach that connected people across files. It knew Jordan led research, Priya led prototyping, and that Jordan's findings changed Priya's home screen. That link lives across two different notes, which is exactly what a graph is good at. It was also fast and every citation was right.

**But the graph has blind spots.** With only 10 relationships, it skipped the entire AI theme (Week 3, plus the AI layouts testing poorly in Week 8). It also kept Professor Lin's "rough for users, refined for stakeholders" answer but dropped the guest speaker's argument, so the disagreement disappeared. The graph can only answer with what got extracted, and extraction is lossy.

**Hybrid gave more but got sloppier.** Level 4 had both the vector chunks and the graph, and it did produce the most detailed answer of the scripted runs. But it mis-cited several claims. It credited the Pantry Pal details and the "rough for users" quote to `notes1.md`, when they actually come from notes 6, 7, and 8. More context made the answer longer, not more accurate. It was also the slowest at almost 98 seconds.

**Claude through MCP was the best by a lot.** Instead of one fixed retrieval, it checked the corpus status, listed sources, pulled the graph, and ran two different searches. It covered all 5 themes, cited everything correctly, and was the only approach that caught the polish contradiction between Week 2 and Week 7. It even checked the graph's 10 claims against the source text and pointed out that the graph was missing the AI theme and the guest speaker's side. That's the kind of self-checking I'd want from a personal assistant.
