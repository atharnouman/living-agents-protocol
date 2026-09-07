# Security policy

LAP is a security-relevant protocol: the reference implementations verify signatures, enforce authority envelopes, and bind requests to identities. Findings are welcome and taken seriously.

Start with [THREAT-MODEL.md](THREAT-MODEL.md): what is defended, where each defence is enforced and tested, and what is explicitly out of scope.

## Reporting a vulnerability

Email **atharnouman@gmail.com** with the subject `LAP security`. Please include a reproduction (the deterministic test vectors in `output/lip/test-vectors/` make minimal repros easy) and, where you can, which mechanism or LIP is affected.

- You will get an acknowledgement within **5 days** and a substantive response within **14 days**.
- Coordinated disclosure: please allow up to **90 days** before public disclosure; we will credit you in the fix commit and the improvements log unless you prefer otherwise.
- No bounty programme exists; this is an independent open-standard project.

## Scope

In scope: `lap-reference/` (Node), `lap-python/`, `lap-git/`, `lap-demo/`, and normative defects in the LIP drafts under `output/lip/` where the text would lead a correct implementation into an insecure state.

Out of scope, because they are already documented as open problems rather than defects: the items in the founding document's §22 (key custody, principal proofing, liveness-witness economics, recorder completeness, and the clone / single-writer problem). Reports that *advance* those are very welcome — file them as issues or through the review kit in `llm-collab/`.

## How this project has been reviewed so far

Every prior finding — merged, softened, or rejected, with reasons — is public in `llm-collab/IMPROVEMENTS-LOG.md`, including a purely hostile third-party security audit whose twelve findings were all verified by reproduction and fixed. That log is the best map of where to look next.
