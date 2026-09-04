# lap-git — Micro-Core for commits

**Experimental LAP binding.** An agent passport for commits, an envelope of permitted paths enforced *before* the commit exists, and a signature over the resulting tree that anyone can verify from the commit alone. It applies the protocol's mechanisms to the most common thing AI agents do today: write code.

```bash
node lap-git/lap-git.mjs init --agent claude-maintainer --scope src/** --scope docs/**
node lap-git/lap-git.mjs commit -m "feat: …"      # refuses out-of-scope paths; signs the tree
node lap-git/lap-git.mjs verify                    # every commit: passport, scope, signature
node lap-git/lap-git.mjs selftest                  # a full demonstration in a temp repo
```

## What it adds — and what already exists

Commit signing is not new, and this does not replace it. **Sigstore gitsign** signs commits with a keyless OIDC identity; **GPG/SSH** commit signing and GitHub's *Verified* badge prove a key holder authored a commit; **in-toto** attestations and **SLSA** provenance describe how an artifact was built; the `Co-authored-by` convention and newer agent-attribution features *label* AI involvement.

All of those answer *who signed*. `lap-git` answers a different question: **which agent, authorized by which principal, within what scope** — and it refuses the commit when the answer is "outside scope." Concretely, the commit carries three trailers:

| Trailer | What it is | Mechanism |
|---|---|---|
| `LAP-Agent` | the agent's `did:key` | identity (LIP-1) |
| `LAP-Passport` | a principal-signed JWT: `iss` = principal, `sub` = agent, `aud` = this repository, plus an **envelope** `{act: ["data:write"], res: ["git://<repo>/src/**", …]}` | principal binding + bounded authority (LIP-4 Micro-Core, LIP-3 Scope Algebra) |
| `LAP-Signature` | the agent's Ed25519 signature over `@tree`, `@parent`, the passport hash, and the sorted changed paths | non-repudiable, verifiable from the commit alone |

`verify` re-derives everything from git itself — tree hash, first parent, changed paths — so a verifier needs nothing but the repository. Unsigned commits are reported as "human, or an unattributed agent"; a tampered signature or an out-of-scope path fails loudly with a `LAP_ERR_*` reason.

## Honest limits

- **Experimental.** A binding sketch to demonstrate the fit, not a hardened tool. Use alongside gitsign/GPG, not instead of them.
- **Self-asserted principal.** The principal key is generated locally; nothing yet binds it to a legal person (see LIP-1 proof classes). It proves *consistency* of authority across commits, not identity in the legal sense.
- **Signs against the first parent** on merges; rename detection is off on both sides so paths match exactly.
- **Private keys** live in `.lap-git/keys.json`, which `init` adds to `.gitignore`. The passport (public) is embedded in each commit; a local hash-chained receipt log is kept in `.lap-git/recorder.jsonl`.

Why it exists: see [`CASE-STUDY.md`](../CASE-STUDY.md) — this repository experienced exactly the failure this prevents.
