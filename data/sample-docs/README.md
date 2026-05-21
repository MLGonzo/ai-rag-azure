# Sample Documents

This directory contains a tiny, original document set for testing grounded RAG
answers. The documents describe a fictional community workshop called Harbor
Hill Community Workshop.

The sample set is safe to publish because it does not include real customer
data, private business records, credentials, or personal information.

The upload script skips this `README.md` file and uploads the other files in
this directory to the configured Blob Storage container.

Useful test questions include:

- What days is Harbor Hill open?
- How long can members borrow a starter repair kit?
- What should someone do before using the soldering station?
- Which rainwater planter needs a valve inspection?

For the Part 3 retrieval lesson, the expected sources are:

| Question | Expected source |
| --- | --- |
| What days is Harbor Hill open? | `harbor-hill-overview.md` |
| What does the starter repair kit include? | `repair-kit-lending.md` |
| Which tote is reserved for first-time borrowers? | `repair-kit-lending.md` |
| Which rainwater planter needs a valve inspection? | `rainwater-planter-pilot.md` |
| What does "reset the bench" mean? | `safety-and-orientation.md` |

See `docs/03-retrieval.md` for expected chunks and mode-comparison commands.
