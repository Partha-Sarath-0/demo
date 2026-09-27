# V1: first-pass prior-art search, GRAIL collector

**Date:** 25 Sep 2026.

**Type:** engineering first pass, done by web search of Google Patents, Justia and OSTI plus the
technical literature.

**What this is not:**
- not a professional patentability search;
- not a freedom-to-operate opinion;
- not legal advice.

Espacenet, WIPO Patentscope and the Indian Patent Office (InPASS) were **not** searched directly,
and Chinese utility models are only partly covered by web search. A registered patent agent must
repeat the search on those databases before any filing decision.

## 1. GRAIL features searched

| # | Feature |
|---|---|
| F1 | Aluminium roll-bond absorber (channels formed inside the plate) |
| F2 | Channels whose cross-section **converges along the flow** by a grading law, D_h(ξ) = D_in[1 − (1 − G) ξ^λ], with G ≈ 0.54 and λ ≈ 1 |
| F3 | **Alternating (counter-current) flow** in neighbouring channels |
| F4 | Transparent-insulation (honeycomb) cover under glass |
| F5 | Phase-change material behind the absorber |
| F6 | Vacuum insulation panel (VIP) as rear insulation |

## 2. Closest documents found

| Document | Status | Features it discloses | Notes |
|---|---|---|---|
| [EP2313705A1](https://patents.google.com/patent/EP2313705A1/en), Roll-bond absorber, Türk Demir Döküm, priority 2008 | Withdrawn 2014 | F1 | Parallel "harp" channels of uniform section; no tapering, no alternating flow |
| [WO2010064078A1](https://patents.google.com/patent/WO2010064078A1/en), Roll-bond absorber, same applicant | Ceased | F1 | Same family; uniform parallel channels |
| [EP1916486A2](https://patents.google.com/patent/EP1916486A2/en), Solar collector system, Wagner & Co, priority 2006 | Withdrawn | F1; channels of **different** sections (a larger integrated return pipe) | Different sizes between channels, **not** a taper along each channel |
| [CN103557603A](https://patents.google.com/patent/CN103557603A/en), Novel flat-plate collector, Tongji University, 2013 | Rejected 2016 | F1-like (two laser-welded plates inflated into channels) | Fixed elliptical section; no F2–F6 |
| [DE10344084A1](https://patents.google.com/patent/DE10344084A1/en), Solar absorber, 2003 | Expired 2013 | Adapted flow resistance so that all channels carry equal flow | No taper along the flow, no alternating flow |
| [US4309987A](https://patents.google.com/patent/US4309987), Fluid flow assembly, 1980 | Expired | Flow distribution by staggered tube insertion into headers | Uniform tubes; no taper |
| [US4426999](https://patents.justia.com/patent/4426999), Solar energy collector, 1984 | Expired | Channelled plastic glazing + fluid panel | No F2–F6 |
| [EP2522927A2](https://patents.google.com/patent/EP2522927A2/en), Solar thermal collector with transparent insulation, Termo Fluids, priority 2011 | **Granted** (status shown as active) | F4: multilayer TIM of **silica aerogel** + honeycomb, optional air/vacuum chambers, between absorber and cover | Relevant to freedom to operate **if** GRAIL used an aerogel layer. GRAIL uses a honeycomb TIM; the claim requires the aerogel layer. A patent agent must check current status and claims |
| [DE10037088C2](https://patents.google.com/patent/DE10037088C2/en), Foil collector with transparent insulation | Check status | F4 | Foil collector |
| [WO2001023813A1](https://patents.google.com/patent/WO2001023813A1) / [CA2283890C](https://patents.google.com/patent/CA2283890C/en), Honeycomb TIM with improved insulation | Old | F4 (the TIM material itself) | Material-level |
| [US20150040888A1](https://patents.google.com/patent/US20150040888A1/en), PCM inside evacuated-tube collector | Application | F5 (in evacuated tubes) | Different collector type |
| Fraunhofer FracTherm® ([licence note](https://www.ise.fraunhofer.de/en/press-media/press-releases/2013/fraunhofer-ise-and-cga-technologies-spa-conlude-licensing-contract.html)) | Licensed technology | F1 + branched (fractal) channel networks | Branching networks, a different concept from graded single channels; the patent documents themselves were not located |

**Non-patent literature that counts as prior art:**
- **Tapered or variable-width channels for uniformity:** Li et al. 2024 (tapered manifold +
  variable-section microchannels, NSGA-II); Ding et al. 2025 (varying channel width, experiment).
  Both are heat sinks.
- **Absorber-plate thickness varying along x:** the variable cross-section solar collector study,
  Santiniketan ([J. Eng. Appl. Sci. 2025](https://link.springer.com/article/10.1186/s44147-025-00629-5)).
  It varies plate thickness, not the channels.
- **Roll-bond and minichannel collectors:** Del Col 2013, Mansour 2013, Zareie 2024.
- **Collectors with TIM, PCM or aerogel covers:** Zheng 2024, Parthiban 2025, Bharathiraja 2024.

## 3. Feature map

| | F1 roll-bond | F2 converging channel | F3 alternating flow | F4 TIM | F5 PCM | F6 VIP |
|---|---|---|---|---|---|---|
| Found in patents | Yes (several) | **Not found** | **Not found** (for collectors) | Yes | Yes (evacuated tube) | Not found (as a collector feature) |
| Found in literature | Yes | Yes (heat sinks; plate thickness) | Counter-flow is textbook for heat exchangers | Yes | Yes | VIP is common in buildings |
| Found combined | — | **No document found combining F1 + F2**, nor F1 + F2 + F4 + F5 + F6 | | | | |

## 4. Engineering assessment

- **Novelty.** Within this first pass, no single document shows a roll-bond absorber with channels
  converging along the flow by a grading law, nor that combined with the TIM / PCM / VIP stack. On
  this search the combination appears **new**.
- **Inventive step (the hard part).** An examiner can combine a roll-bond absorber (EP2313705) with
  tapered channels from heat-sink work (Li 2024, Ding 2025) and a TIM cover (EP2522927). The
  applicant must then show a technical effect that is **not expected** from those parts. Our own
  data:
  - **Alternating flow (F3):** no efficiency or R4 benefit at matched plate temperature (V7). Do
    **not** claim it as the invention; at most keep it as a dependent option.
  - **Converging channel (F2):** it helps plate uniformity at high flow, but the NSGA-II optimum
    moves towards G → 1 (little convergence). This weakens an efficiency-based argument. A claim
    would have to rest on uniformity, or on a specific G/λ window with a measured benefit.
  - **Stack (F4 + F5 + F6):** gives a1 ≈ 2 W/m²K, less than half that of tested roll-bond
    collectors. This is the strongest effect, but it mostly comes from known layers.
- **Overall.** Novelty looks possible; inventive step looks **weak to moderate** on current
  evidence. A prototype test showing a clear, quantified benefit of the converging roll-bond channel
  would strengthen it considerably.
- **Freedom to operate.** Using a silica-aerogel TIM layer could touch EP2522927A2 (granted) in
  countries where it is in force. Check its status and territory. A honeycomb-only TIM, as in
  GRAIL, appears outside its claim 1. The expired and withdrawn roll-bond patents do not block use.

## 5. If you want to pursue a patent

1. **Do not publish** (paper, conference, public thesis, online) before filing.
2. Take this report to the college IPR cell or a registered patent agent. Ask for a professional
   search on Espacenet, WIPO Patentscope, InPASS and CNIPA.
3. If they see room, file an **Indian provisional application**. It fixes the priority date; you
   then have 12 months for the complete specification and can publish the paper after filing.
4. **Candidate main claim** (for the agent to shape): a roll-bond solar absorber whose integral
   channels each have a hydraulic diameter decreasing monotonically from inlet to outlet (outlet /
   inlet ratio G in a stated range, e.g. 0.4–0.7), in a collector with a transparent-insulation
   cover.
   - **Dependent claims:** grading exponent λ; PCM rear layer; VIP rear insulation; alternating
     flow; bridge width.
5. Before the complete application, measure the uniformity and efficiency benefit on a prototype.

**If you do not pursue a patent:** publish the paper and thesis as they are; they already describe
the design honestly.

Roadmap status: **V1 = first pass done; professional search pending** (only if a filing is
planned). **V10** (patent-agent review) stays open.
