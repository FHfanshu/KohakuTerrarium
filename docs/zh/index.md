---
layout: home

hero:
  name: KohakuTerrarium
  text: 非官方中文文档站
  tagline: 这是第三方维护的中文文档，不代表官方文档权威
  image:
    src: /logo.svg
    alt: KohakuTerrarium community docs
  actions:
    - theme: brand
      text: 快速开始
      link: /zh/quickstart
    - theme: alt
      text: 官方仓库
      link: https://github.com/Kohaku-Lab/KohakuTerrarium
    - theme: alt
      text: 第三方文档源码
      link: https://github.com/FHfanshu/KohakuTerrarium

features:
  - icon: 📌
    title: 先看这个说明
    details: 本站是社区维护的第三方中文文档。如果内容与官方英文文档或源码行为不一致，请以官方仓库最新内容为准。
  - icon: 🤖
    title: 以 Creature 为核心
    details: Creature 是独立运行的智能体，有自己的控制器、工具、子智能体、触发器、记忆和 I/O。既可以单独运行，也可以继承、打包和分享。
  - icon: 🔗
    title: 多智能体编排
    details: Terrarium 通过 channel 把多个智能体连接起来。拓扑用声明式配置，运行时也支持热插拔。
  - icon: 📦
    title: 包管理系统
    details: 一条命令就能从 git 仓库安装 creature 包，也方便分发自己的智能体、预设和插件。
  - icon: 🔍
    title: 会话与记忆
    details: 每次运行都会保存可搜索的 session，方便恢复、回放，以及用语义搜索查历史交互。
  - icon: 🛡️
    title: 插件与约束
    details: 可以拦截工具调用、强制执行规则、记录审计操作，用来构建更安全、也更符合项目约定的智能体。
---