import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'KohakuTerrarium',
  description: 'A framework for building real agents, not just LLM wrappers',
  
  // Base URL for GitHub Pages project site
  base: '/KohakuTerrarium/',
  
  // Theme config
  themeConfig: {
    logo: '/logo.svg',
    siteTitle: 'KT Docs',
    
    // Navigation - 指向官方仓库
    nav: [
      { text: 'Home', link: '/' },
      { text: '中文', link: '/zh/' },
      { text: 'Guides', link: '/guides/' },
      { text: 'Reference', link: '/reference/' },
      { text: '官方仓库', link: 'https://github.com/Kohaku-Lab/KohakuTerrarium' }
    ],
    
    // Sidebar - organized by sections
    sidebar: {
      '/zh/': [
        {
          text: '入门',
          collapsed: false,
          items: [
            { text: '目录', link: '/zh/README' },
            { text: '安装与快速开始', link: '/zh/quickstart' },
            { text: '模型与预设配置', link: '/zh/llm-profiles' },
            { text: 'CLI 与 WebUI 使用', link: '/zh/cli-webui' },
            { text: '配置文件写法', link: '/zh/configuration' },
            { text: '会话、审计与排错', link: '/zh/audit-and-sessions' },
            { text: '定制 SWE 智能体', link: '/zh/swe-bio-agent' }
          ]
        },
        {
          text: '教程',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/tutorials/README' },
            { text: '第一个 Creature', link: '/zh/tutorials/first-creature' },
            { text: '第一个 Terrarium', link: '/zh/tutorials/first-terrarium' },
            { text: '第一个 Python 嵌入示例', link: '/zh/tutorials/first-python-embedding' },
            { text: '第一个自定义 Tool', link: '/zh/tutorials/first-custom-tool' },
            { text: '第一个 Plugin', link: '/zh/tutorials/first-plugin' }
          ]
        },
        {
          text: '指南',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/guides/README' },
            { text: '快速上手', link: '/zh/guides/getting-started' },
            { text: 'Creatures', link: '/zh/guides/creatures' },
            { text: 'Sessions', link: '/zh/guides/sessions' },
            { text: 'Configuration', link: '/zh/guides/configuration' },
            { text: 'Plugins', link: '/zh/guides/plugins' },
            { text: 'MCP', link: '/zh/guides/mcp' },
            { text: 'Packages', link: '/zh/guides/packages' },
            { text: 'Custom Modules', link: '/zh/guides/custom-modules' },
            { text: 'Serving', link: '/zh/guides/serving' },
            { text: 'Memory', link: '/zh/guides/memory' },
            { text: 'Composition', link: '/zh/guides/composition' },
            { text: 'Terrariums', link: '/zh/guides/terrariums' },
            { text: 'Programmatic Usage', link: '/zh/guides/programmatic-usage' },
            { text: 'Frontend Layout', link: '/zh/guides/frontend-layout' },
            { text: 'Examples', link: '/zh/guides/examples' }
          ]
        },
        {
          text: '概念',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/concepts/README' },
            { text: 'Boundaries', link: '/zh/concepts/boundaries' },
            { text: 'Glossary', link: '/zh/concepts/glossary' },
            { text: 'Patterns', link: '/zh/concepts/patterns' },
            { text: 'What is an Agent', link: '/zh/concepts/foundations/what-is-an-agent' },
            { text: 'Why KohakuTerrarium', link: '/zh/concepts/foundations/why-kohakuterrarium' },
            { text: 'Composing an Agent', link: '/zh/concepts/foundations/composing-an-agent' },
            { text: 'Modules', link: '/zh/concepts/modules/README' },
            { text: 'Controller', link: '/zh/concepts/modules/controller' },
            { text: 'Tool', link: '/zh/concepts/modules/tool' },
            { text: 'Sub-Agent', link: '/zh/concepts/modules/sub-agent' },
            { text: 'Channel', link: '/zh/concepts/modules/channel' },
            { text: 'Trigger', link: '/zh/concepts/modules/trigger' },
            { text: 'Plugin', link: '/zh/concepts/modules/plugin' },
            { text: 'Session and Environment', link: '/zh/concepts/modules/session-and-environment' },
            { text: 'Memory and Compaction', link: '/zh/concepts/modules/memory-and-compaction' },
            { text: 'Input', link: '/zh/concepts/modules/input' },
            { text: 'Output', link: '/zh/concepts/modules/output' },
            { text: 'Multi-Agent', link: '/zh/concepts/multi-agent/README' },
            { text: 'Terrarium', link: '/zh/concepts/multi-agent/terrarium' },
            { text: 'Root Agent', link: '/zh/concepts/multi-agent/root-agent' },
            { text: 'Python Native', link: '/zh/concepts/python-native/README' },
            { text: 'Agent as Python Object', link: '/zh/concepts/python-native/agent-as-python-object' },
            { text: 'Composition Algebra', link: '/zh/concepts/python-native/composition-algebra' },
            { text: '实现说明', link: '/zh/concepts/impl-notes/README' },
            { text: 'Prompt Aggregation', link: '/zh/concepts/impl-notes/prompt-aggregation' },
            { text: 'Session Persistence', link: '/zh/concepts/impl-notes/session-persistence' },
            { text: 'Non-Blocking Compaction', link: '/zh/concepts/impl-notes/non-blocking-compaction' },
            { text: 'Stream Parser', link: '/zh/concepts/impl-notes/stream-parser' }
          ]
        },
        {
          text: '参考',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/reference/README' },
            { text: 'CLI', link: '/zh/reference/cli' },
            { text: 'Builtins', link: '/zh/reference/builtins' },
            { text: 'Configuration', link: '/zh/reference/configuration' },
            { text: 'Python API', link: '/zh/reference/python' },
            { text: 'HTTP API', link: '/zh/reference/http' },
            { text: 'Plugin Hooks', link: '/zh/reference/plugin-hooks' }
          ]
        },
        {
          text: '开发',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/dev/README' },
            { text: 'Internals', link: '/zh/dev/internals' },
            { text: 'Testing', link: '/zh/dev/testing' },
            { text: 'Dependency Graph', link: '/zh/dev/dependency-graph' },
            { text: 'Frontend', link: '/zh/dev/frontend' }
          ]
        },
        {
          text: '进阶专题',
          collapsed: true,
          items: [
            { text: 'MCP 进阶', link: '/zh/mcp-advanced' },
            { text: 'kt install 与 package 进阶', link: '/zh/packages-and-install-advanced' },
            { text: 'skills、info 与 skill_mode 进阶', link: '/zh/skills-and-skill-mode-advanced' }
          ]
        }
      ],
      '/': [
        {
          text: 'Getting Started',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/' },
            { text: 'Getting Started', link: '/guides/getting-started' }
          ]
        },
        {
          text: 'Tutorials',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/tutorials/' },
            { text: 'First Creature', link: '/tutorials/first-creature' },
            { text: 'First Terrarium', link: '/tutorials/first-terrarium' },
            { text: 'First Python Embedding', link: '/tutorials/first-python-embedding' }
          ]
        },
        {
          text: 'Guides',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/guides/' },
            { text: 'Creatures', link: '/guides/creatures' },
            { text: 'Sessions', link: '/guides/sessions' },
            { text: 'Configuration', link: '/guides/configuration' },
            { text: 'Plugins', link: '/guides/plugins' },
            { text: 'Custom Modules', link: '/guides/custom-modules' },
            { text: 'Terrariums', link: '/guides/terrariums' },
            { text: 'Programmatic Usage', link: '/guides/programmatic-usage' },
            { text: 'Frontend Layout', link: '/guides/frontend-layout' },
            { text: 'Examples', link: '/guides/examples' }
          ]
        },
        {
          text: 'Concepts',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/concepts/' },
            { text: 'Boundaries', link: '/concepts/boundaries' },
            { text: 'Glossary', link: '/concepts/glossary' },
            { text: 'Patterns', link: '/concepts/patterns' },
            { text: 'Foundations', link: '/concepts/foundations/' },
            { text: 'Modules', link: '/concepts/modules/' },
            { text: 'Multi-Agent', link: '/concepts/multi-agent/' },
            { text: 'Python Native', link: '/concepts/python-native/' }
          ]
        },
        {
          text: 'Reference',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/reference/' },
            { text: 'CLI Reference', link: '/reference/cli' },
            { text: 'HTTP API', link: '/reference/http' },
            { text: 'Python API', link: '/reference/python' }
          ]
        },
        {
          text: 'Development',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/dev/' },
            { text: 'Testing', link: '/dev/testing' },
            { text: 'Framework Internals', link: '/dev/internals' },
            { text: 'Frontend Architecture', link: '/dev/frontend' }
          ]
        }
      ]
    },
    
    // Social links - 指向官方仓库
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Kohaku-Lab/KohakuTerrarium' }
    ],
    
    // Search - local search
    search: {
      provider: 'local'
    },
    
    // Footer - 正确声明版权
    footer: {
      message: 'This is a community-maintained documentation site. The framework belongs to Kohaku Lab. If anything here conflicts with upstream docs or source code, follow the official repository.',
      copyright: 'Framework © Kohaku Lab | Community docs © FHfanshu'
    },
    
    // Edit link - 中文文档编辑指向你的 fork
    editLink: {
      pattern: 'https://github.com/FHfanshu/KohakuTerrarium/edit/main/docs/:path',
      text: '编辑此页 (中文文档)'
    }
  },
  
  // Markdown config
  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    },
    lineNumbers: false
  },
  
  // Locales for i18n
  locales: {
    root: {
      label: 'English',
      lang: 'en'
    },
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/',
      themeConfig: {
        nav: [
          { text: '首页', link: '/zh/' },
          { text: '英文', link: '/' },
          { text: '指南', link: '/zh/quickstart' },
          { text: '官方仓库', link: 'https://github.com/Kohaku-Lab/KohakuTerrarium' },
          { text: '第三方文档源码', link: 'https://github.com/FHfanshu/KohakuTerrarium' }
        ],
        editLink: {
          pattern: 'https://github.com/FHfanshu/KohakuTerrarium/edit/main/docs/:path',
          text: '编辑此页'
        },
        footer: {
          message: '本站为第三方维护的社区中文文档，不代表官方立场。如与官方英文文档或源码行为不一致，请以官方仓库为准。',
          copyright: '框架 © Kohaku Lab | 中文文档 © FHfanshu'
        },
        docFooter: {
          prev: '上一页',
          next: '下一页'
        },
        outline: {
          label: '页面导航'
        },
        lastUpdated: {
          text: '最后更新于',
          formatOptions: {
            dateStyle: 'short',
            timeStyle: 'medium'
          }
        }
      }
    }
  },
  
  // Build options
  cleanUrls: true,
  ignoreDeadLinks: true,
  
  // Head elements
  head: [
    ['link', { rel: 'icon', href: '/banner.png', type: 'image/png' }],
    ['meta', { name: 'theme-color', content: '#42b983' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'KohakuTerrarium Community Docs' }],
    ['meta', { property: 'og:description', content: 'Community-maintained Chinese docs for KohakuTerrarium. Non-official.' }]
  ]
})