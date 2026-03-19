# Overview

AI Form Filler is a lightweight tool that fills web forms using a local LLM (Ollama) and browser automation (Playwright). It is designed to work with **your own browser**—either by connecting to an already-running Chrome via CDP or by launching Chrome with your user profile—so that most forms (including those behind login) can be filled without a separate headless or dev browser.

## Goals

- Work with **most forms**: standard inputs, textareas, selects, checkboxes, radios.
- Use **your browser**: existing session (CDP) or your Chrome profile (persistent context).
- **Lightweight**: minimal dependencies, no heavy framework; similar idea to OpenClaw-style browser automation but focused on form filling only.
- **Local-first**: Ollama (or compatible) for mapping data to fields; no required cloud APIs.

## High-level flow

1. **Connect**: CDP to your Chrome, Playwright persistent profile, or optional **undetected-chromedriver** (Selenium) for a stealthier launch.
2. **Navigate (optional LLM)**: Either open a URL you provide, or ask the local LLM for a **navigation intent** (`url` + `reason`) from a natural-language **goal** and optional **hints**.
3. **Extract**: Run shared JS in the page to collect fillable form fields (key, tag, type, name, id, placeholder, label, options).
4. **Plan (fill)**: Send the form schema and the user’s data (JSON) to Ollama; the LLM returns a mapping from field keys to values (fill plan).
5. **Fill**: Apply the plan via Playwright locators or Selenium element APIs.
6. **Optional**: Click submit.

## AI module

Applications can embed **`AIFormModule`** (`from ai_form_filler import AIFormModule`) instead of shelling out to the CLI.

## Out of scope

- Captcha or strong bot protection.
- Multi-step wizards (single page only per run).
- Non-form interactions (e.g. complex app flows). The tool is form-filler focused.
