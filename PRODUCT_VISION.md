# Meta-Patch: Product Strategy & Vision

This document outlines the product-level strategy for establishing Meta-Patch as a universal standard for guitar tone documentation.

---

## 1. Historical Context: The "General MIDI" Analogy

To understand the path forward, we must look at **General MIDI (GM)**.

*   **The Problem (Pre-GM):** You wrote a song on a Roland synth. You sent the MIDI file to a friend with a Yamaha synth. Your "Piano" track played back as a "Tuba" because Program #1 meant different things on different hardware.
*   **The Solution (GM):** A standardized map. Program #1 is *always* Acoustic Grand Piano. Channel 10 is *always* Drums.
*   **The Result:** Explosion of file sharing. MIDI files became the "MP3" of the 90s.
*   **The "Flaw":** GM didn't standardize *timbre*. A generic "Piano" on a cheap Casio sounded worse than on a $2000 Korg. **But the musical intent was preserved.**

**Meta-Patch is "General MIDI for Guitar Tones."**
We are not trying to make a Line 6 Helix sound *identically* indistinguishable from a Fractal Axe-Fx. We are trying to preserve the **intent**: *"A Tube Screamer pushing a Plexi with delay."*

### Failed Attempts (The Graveyard)
*   **Open Sound Control (OSC):** Superior to MIDI technically, but failed to replace it because MIDI was "good enough" and deeply entrenched. **Lesson:** Don't over-engineer. Simplicity wins.
*   **Universal Patch Librarians (Midi Quest, SoundQuest):** These exist but are expensive, proprietary software suites. They failed to create a *standard format*; they just built a *translator tool*. **Lesson:** The format must be open-source and text-based (like Markdown), not a proprietary database.

---

## 2. Critical Success Factors (The "Must Haves")

For Meta-Patch to succeed where others stayed niche, it needs three pillars:

### A. The "Rosetta Stone" Database (Community-Driven Mappings)
The code (`adapters/`) is the engine, but the fuel is `mappings.yaml`.
*   **The Challenge:** There are thousands of pedals. "Green Drive" on Platform A has 3 knobs; "Screamer" on Platform B has 4 knobs.
*   **The Solution:** A massive, community-maintained database of these equivalencies.
    *   *Example:* `Tube Screamer (Tone: 50%)` -> `Helix (Tone: 6.5)` vs `Amplitube (Tone: 5.0)`.
    *   **Success Metric:** If a user types "Klon Centaur," does it work on 5 different platforms automatically?

### B. "Markdown for Tone" (The Format)
The YAML format must be treated like Markdown.
*   It must be readable *without* the software.
*   It must be diff-able in Git (version control for tone!).
*   **The "Killer Feature":** A guitarist should be able to look at a `texas-blues.yaml` on GitHub and mentally "hear" the tone just by reading the settings.

### C. The "Tone Wikipedia" (Central Repository)
You need a destination. **ToneHunt.org** (for NAM models) proved this demand exists.
*   Users need a place to upload "SRV - Pride and Joy.yaml".
*   The site automatically generates the download buttons: `[Download for Helix]`, `[Download for Bias]`, `[Download for Katana]`.
*   **This is the viral loop.**

---

## 3. Roadmap & Phases

### Phase 1: The "Hacker" Tool (Months 1-3)
*   **Target User:** Developers, tech-savvy guitarists, Redditors.
*   **Goal:** Perfect the Python script and the Schema.
*   **Deliverables:**
    1.  Robust CLI.
    2.  Coverage for the "Big 3" (Helix, Bias, Amplitube).
    3.  **Validation:** Users successfully porting patches and posting about it on Reddit/TheGearPage.

### Phase 2: The "Visualizer" & Web UI (Months 3-6)
*   **Target User:** The average guitarist who is scared of Python.
*   **Goal:** Lower the barrier to entry.
*   **Deliverables:**
    1.  **Web App:** Drag and drop a YAML file (or even a `.hlx` file!) and see a visual signal chain (icons of pedals).
    2.  **Two-Way Conversion:** We currently do Meta -> Platform. We need Platform -> Meta. This allows users to "backup" their proprietary patches into an open format.

### Phase 3: The "Ecosystem" (Year 1+)
*   **Target User:** Content Creators, Youtubers, Session Players.
*   **Goal:** Integration.
*   **Deliverables:**
    1.  **VST Wrapper:** A simple VST plugin that loads `.yaml` files and hosts open-source neural models (NAM/AIDA-X) to match the description.
    2.  **YouTube Integration:** YouTubers posting "meta-links" in descriptions instead of 5 different download links.

---

## 4. Pitfalls & Risks

1.  **IP & Trademark Law:**
    *   *Risk:* Using names like "Tube Screamer," "Marshall," or "Fender" in your repo/mappings.
    *   *Mitigation:* Use generic names in the default schema (e.g., `Overdrive (Green)`, `Amp (British Lead)`). Let the community mappings handle the specific brand translation (safely).

2.  **Subjectivity of "Knob Position":**
    *   *Risk:* 50% Gain on a Helix Plexi is much cleaner than 50% Gain on a Fractal Plexi.
    *   *Mitigation:* The "Rosetta Stone" database needs **Scaling Factors**.
    *   *Example mapping:* `Helix_Gain = Meta_Gain * 0.8`.

3.  **Complexity Creep:**
    *   *Risk:* Trying to support "Dual Amps," "Parallel Signal Paths," and complex MIDI routing.
    *   *Mitigation:** The 80/20 Rule.** Focus on the "Single Chain" (Pedals -> Amp -> Cab). That covers 90% of use cases. Don't let the edge cases kill the standard.

---

## 5. Funding & Revenue Models

1.  **Open Core (GitHub Sponsors/Patreon):**
    *   The schema and CLI are free.
    *   Support requested for maintaining the Mappings Database (which is labor-intensive).

2.  **SaaS (The "Tone Cloud"):**
    *   Free to convert 1 patch.
    *   $5/mo to sync your *entire* library, back it up to `.yaml`, and auto-generate exports for every platform.
    *   **Value Prop:** "Switching from Helix to Quad Cortex? We'll migrate your 100 presets in 5 seconds."

3.  **Content Creator Tools:**
    *   Sell a "Pro" tool to YouTubers that generates a branded landing page for their patches.
