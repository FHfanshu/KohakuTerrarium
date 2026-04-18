import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'KohakuTerrarium',
  description: 'A framework for building real agents, not just LLM wrappers',
  
  // Base URL for deployment
  base: '/',
  
  // Theme config
  themeConfig: {
    logo: '/banner.png',
    siteTitle: 'KohakuTerrarium 中文文档',
    
    // Navigation
    nav: [
      { text: 'Home', link: '/' },
      { text: '中文', link: '/zh/' },
      { text: 'Guides', link: '/guides/' },
      { text: 'Reference', link: '/reference/' },
      { text: 'GitHub', link: 'https://github.com/FHfanshu/KohakuTerrarium' }
    ],
    
    // Sidebar - organized by sections
    sidebar: {
      '/zh/': [
        {
          text: '入门指南',
          collapsed: false,
          items: [
            { text: '目录', link: '/zh/' },
            { text: '安装与快速开始', link: '/zh/quickstart' },
            { text: 'CLI 与 WebUI', link: '/zh/cli-webui' },
            { text: '配置文件写法', link: '/zh/configuration' },
            { text: '定制 SWE 智能体', link: '/zh/swe-bio-agent' },
            { text: '会话、审计与排错', link: '/zh/audit-and-sessions' },
            { text: '模型与预设配置', link: '/zh/llm-profiles' }
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
            { text: 'Agents', link: '/concepts/agents' },
            { text: 'Terrariums', link: '/concepts/terrariums' },
            { text: 'Channels', link: '/concepts/channels' },
            { text: 'Execution Model', link: '/concepts/execution' },
            { text: 'Prompt System', link: '/concepts/prompts' },
            { text: 'Plugins', link: '/concepts/plugins' },
            { text: 'Composition Algebra', link: '/concepts/composition-algebra' },
            { text: 'Serving Layer', link: '/concepts/serving' },
            { text: 'Environment & Session', link: '/concepts/environment' },
            { text: 'Tool Formats', link: '/concepts/tool-formats' }
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
    
    // Social links
    socialLinks: [
      { icon: 'github', link: 'https://github.com/FHfanshu/KohakuTerrarium' }
    ],
    
    // Search - local search
    search: {
      provider: 'local'
    },
    
    // Footer
    footer: {
      message: '中文文档由第三方维护者 FHfanshu 编写，非官方文档。',
      copyright: 'Copyright © 2024-present FHfanshu'
    },
    
    // Edit link
    editLink: {
      pattern: 'https://github.com/FHfanshu/KohakuTerrarium/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
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
          { text: 'GitHub', link: 'https://github.com/FHfanshu/KohakuTerrarium' }
        ],
        editLink: {
          pattern: 'https://github.com/FHfanshu/KohakuTerrarium/edit/main/docs/:path',
          text: '在 GitHub 上编辑此页'
        },
        footer: {
          message: '中文文档由第三方维护者编写，非官方文档',
          copyright: '版权所有 © 2024至今 FHfanshu'
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
  
  // Head elements
  head: [
    ['link', { rel: 'icon', href: '/banner.png', type: 'image/png' }],
    ['meta', { name: 'theme-color', content: '#42b983' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'KohakuTerrarium | Build Real Agents' }],
    ['meta', { property: 'og:description', content: 'A framework for building real agents, not just LLM wrappers' }]
  ]
})