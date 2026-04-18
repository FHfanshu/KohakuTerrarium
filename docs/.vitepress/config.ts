import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'KohakuTerrarium',
  description: 'A framework for building real agents, not just LLM wrappers',
  
  base: '/KohakuTerrarium/',
  
  themeConfig: {
    logo: '/logo.svg',
    siteTitle: 'KT Docs',
    
    nav: [
      { text: 'Home', link: '/' },
      { text: '中文', link: '/zh/' },
      { text: 'Guides', link: '/guides/' },
      { text: 'Reference', link: '/reference/' },
      { text: '官方仓库', link: 'https://github.com/Kohaku-Lab/KohakuTerrarium' }
    ],
    
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
          text: '官方文档教程（机翻）',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/tutorials/README' },
            { text: '第一个 Creature（智能体）', link: '/zh/tutorials/first-creature' },
            { text: '第一个 Terrarium（容器）', link: '/zh/tutorials/first-terrarium' },
            { text: '第一个 Python 嵌入示例', link: '/zh/tutorials/first-python-embedding' },
            { text: '第一个自定义工具', link: '/zh/tutorials/first-custom-tool' },
            { text: '第一个插件', link: '/zh/tutorials/first-plugin' }
          ]
        },
        {
          text: '指南',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/guides/README' },
            { text: '快速上手', link: '/zh/guides/getting-started' },
            { text: '智能体', link: '/zh/guides/creatures' },
            { text: '会话', link: '/zh/guides/sessions' },
            { text: '配置', link: '/zh/guides/configuration' },
            { text: '插件', link: '/zh/guides/plugins' },
            { text: 'MCP', link: '/zh/guides/mcp' },
            { text: '包', link: '/zh/guides/packages' },
            { text: '自定义模块', link: '/zh/guides/custom-modules' },
            { text: '服务部署', link: '/zh/guides/serving' },
            { text: '记忆', link: '/zh/guides/memory' },
            { text: '组合', link: '/zh/guides/composition' },
            { text: '容器', link: '/zh/guides/terrariums' },
            { text: '以代码方式使用', link: '/zh/guides/programmatic-usage' },
            { text: '前端布局', link: '/zh/guides/frontend-layout' },
            { text: '示例', link: '/zh/guides/examples' }
          ]
        },
        {
          text: '概念',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/concepts/README' },
            { text: '边界', link: '/zh/concepts/boundaries' },
            { text: '术语表', link: '/zh/concepts/glossary' },
            { text: '模式', link: '/zh/concepts/patterns' },
            { text: '什么是智能体', link: '/zh/concepts/foundations/what-is-an-agent' },
            { text: '为什么会有 KohakuTerrarium', link: '/zh/concepts/foundations/why-kohakuterrarium' },
            { text: '组合智能体', link: '/zh/concepts/foundations/composing-an-agent' },
            { text: '模块', link: '/zh/concepts/modules/README' },
            { text: '控制器', link: '/zh/concepts/modules/controller' },
            { text: '工具', link: '/zh/concepts/modules/tool' },
            { text: '子智能体', link: '/zh/concepts/modules/sub-agent' },
            { text: '通道', link: '/zh/concepts/modules/channel' },
            { text: '触发器', link: '/zh/concepts/modules/trigger' },
            { text: '插件', link: '/zh/concepts/modules/plugin' },
            { text: '会话与环境', link: '/zh/concepts/modules/session-and-environment' },
            { text: '记忆与压缩', link: '/zh/concepts/modules/memory-and-compaction' },
            { text: '输入', link: '/zh/concepts/modules/input' },
            { text: '输出', link: '/zh/concepts/modules/output' },
            { text: '多智能体', link: '/zh/concepts/multi-agent/README' },
            { text: 'Terrarium（容器环境）', link: '/zh/concepts/multi-agent/terrarium' },
            { text: 'Root Agent（根智能体）', link: '/zh/concepts/multi-agent/root-agent' },
            { text: 'Python 原生', link: '/zh/concepts/python-native/README' },
            { text: '智能体作为 Python 对象', link: '/zh/concepts/python-native/agent-as-python-object' },
            { text: '组合代数', link: '/zh/concepts/python-native/composition-algebra' },
            { text: '实现说明', link: '/zh/concepts/impl-notes/README' },
            { text: 'Prompt 聚合', link: '/zh/concepts/impl-notes/prompt-aggregation' },
            { text: '会话持久化', link: '/zh/concepts/impl-notes/session-persistence' },
            { text: '非阻塞压缩', link: '/zh/concepts/impl-notes/non-blocking-compaction' },
            { text: '流解析器', link: '/zh/concepts/impl-notes/stream-parser' }
          ]
        },
        {
          text: '参考',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/reference/README' },
            { text: 'CLI', link: '/zh/reference/cli' },
            { text: '内建项', link: '/zh/reference/builtins' },
            { text: '配置', link: '/zh/reference/configuration' },
            { text: 'Python API', link: '/zh/reference/python' },
            { text: 'HTTP API', link: '/zh/reference/http' },
            { text: '插件钩子', link: '/zh/reference/plugin-hooks' }
          ]
        },
        {
          text: '开发',
          collapsed: true,
          items: [
            { text: '总览', link: '/zh/dev/README' },
            { text: '框架内部结构', link: '/zh/dev/internals' },
            { text: '测试', link: '/zh/dev/testing' },
            { text: '依赖图', link: '/zh/dev/dependency-graph' },
            { text: '前端', link: '/zh/dev/frontend' }
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
    
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Kohaku-Lab/KohakuTerrarium' }
    ],
    
    search: {
      provider: 'local'
    },
    
    footer: {
      message: 'This is a community-maintained documentation site. The framework belongs to Kohaku Lab. If anything here conflicts with upstream docs or source code, follow the official repository.',
      copyright: 'Framework © Kohaku Lab | Community docs © FHfanshu'
    },
    
    editLink: {
      pattern: 'https://github.com/FHfanshu/KohakuTerrarium/edit/main/docs/:path',
      text: 'Edit this page'
    }
  },
  
  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    },
    lineNumbers: false
  },
  
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
  
  cleanUrls: true,
  ignoreDeadLinks: true,
  
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#42b983' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'KohakuTerrarium Community Docs' }],
    ['meta', { property: 'og:description', content: 'Community-maintained Chinese docs for KohakuTerrarium. Non-official.' }]
  ]
})