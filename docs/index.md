---
layout: home

hero:
  name: KohakuTerrarium
  text: Build Real Agents
  tagline: A framework for building real agents, not just LLM wrappers
  image:
    src: /logo.svg
    alt: KohakuTerrarium
  actions:
    - theme: brand
      text: Get Started
      link: /guides/getting-started
    - theme: alt
      text: 中文文档
      link: /zh/
    - theme: alt
      text: View on GitHub
      link: https://github.com/Kohaku-Lab/KohakuTerrarium

features:
  - icon: 🤖
    title: Creature-First Design
    details: A creature is a standalone agent with its own controller, tools, sub-agents, triggers, memory, and I/O. Run it alone, inherit from another, or package and share.
  - icon: 🔗
    title: Multi-Agent Composition
    details: Terrariums compose creatures through channels. Build complex agent teams with declarative topology wiring and hot-plug support.
  - icon: 📦
    title: Package System
    details: Install creature packages from git repos. Share your agents, presets, and plugins with a single command.
  - icon: 🔍
    title: Session & Memory
    details: Every run creates a searchable session. Resume, replay, or analyze past interactions with semantic search.
  - icon: 🛡️
    title: Plugins & Guardrails
    details: Intercept tool calls, enforce rules, and audit actions. Build safe agents that respect project conventions.
  - icon: 🎨
    title: Multiple Interfaces
    details: CLI, TUI, WebUI, and desktop app. Choose the interface that fits your workflow.
---