# TrustFlow architecture

```mermaid
flowchart LR
  U[Vendor + agreement] --> S[SerpApi evidence collector]
  U --> N[Nutrient DWS structured extraction]
  S --> P[Deterministic policy engine]
  N --> P
  P --> G[Optional Gemini evidence synthesis]
  G --> H{Human approval}
  P --> H
  H -- rejected --> B[Blocked]
  H -- approved --> D[Doctavian approval packet]
  D --> F[Foxit eSign draft]
  F --> X[Human signing UX]
  S --> XA[(Xano workflow + audit store)]
  N --> XA
  P --> XA
  H --> XA
  D --> XA
  F --> XA
```

## Safety invariant

No model, search result, extracted document field, or workflow automation is permitted to authorize a signature. The application requires an explicit reviewer approval **and** a second explicit human intent flag before it will even create a Foxit eSign draft. The Foxit adapter hardcodes `sendNow=false`, so TrustFlow itself never emails a signer or dispatches a contract.
