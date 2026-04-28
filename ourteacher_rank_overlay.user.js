// ==UserScript==
// @name         OurTeacher 学生序号自动显示
// @namespace    xiaolv-local
// @version      1.0.0
// @description  在学生名单姓名前自动显示与打卡一致的序号（仅页面显示，不改后台数据）
// @match        https://www.ourteacher.cc/*
// @grant        none
// ==/UserScript==

(function () {
  "use strict";

  const NAME_TO_RANK = {
    "李鸿宇": 1, "成昊飞": 2, "王向天": 3, "陶梦妍": 4, "曾琝喆": 5, "刘辰熙": 6, "黄明暄": 7, "黄锦馨": 8,
    "夏心研": 9, "陈万希": 10, "曾心悦": 11, "符怀心": 12, "何诗妍": 13, "姜陈一": 14, "董馨月": 15, "刘梦萱": 16,
    "汤雨涵": 17, "陈语萌": 18, "何治成": 19, "刘昱彤": 20, "李博文": 21, "孙博睿": 22, "何宇榛": 23, "张光辰": 24,
    "罗悦琪": 25, "徐梦莹": 26, "高学成": 27, "俞梓熙": 28, "姜楚涵": 29, "朱诗语": 30, "李闽朗": 31, "章宇晨": 32,
    "李婉宁": 33, "林越": 34, "孙紫涵": 35, "段若彤": 36, "王彦骁": 37, "刘子骁": 38, "贾钰辰": 39, "帅景瑜": 40,
    "周宣志": 41, "丁晨杰": 42, "聂子韵": 43, "范钧澔": 44, "董怡涵": 45, "章忆恩": 46, "张欣彤": 47, "吴倩雯": 48,
    "杜颢宇": 49, "杨宇童": 50, "江天翊": 51, "谢泓达": 52
  };

  function pad2(n) {
    return String(n).padStart(2, "0");
  }

  function makeBadge(rank) {
    const badge = document.createElement("span");
    badge.className = "rank-badge-auto";
    badge.textContent = `${pad2(rank)} `;
    badge.style.cssText = "color:#2563eb;font-weight:700;margin-right:2px;";
    return badge;
  }

  function injectStyle() {
    if (document.getElementById("rank-overlay-style")) return;
    const style = document.createElement("style");
    style.id = "rank-overlay-style";
    style.textContent = `
      .rank-badge-auto { display:inline-block; white-space:pre; }
    `;
    document.head.appendChild(style);
  }

  function tryDecorateElement(el) {
    if (!el || el.nodeType !== 1) return;
    if (el.querySelector(".rank-badge-auto")) return;
    const txt = (el.textContent || "").trim();
    const rank = NAME_TO_RANK[txt];
    if (!rank) return;
    if (el.children.length > 0) return;
    el.prepend(makeBadge(rank));
  }

  function scanAndDecorate(root = document) {
    // 常见名字节点：纯文本、较短、没有子节点
    const all = root.querySelectorAll("span,div,p");
    all.forEach((el) => {
      const text = (el.textContent || "").trim();
      if (!text) return;
      if (text.length > 6) return;
      if (!(text in NAME_TO_RANK)) return;
      tryDecorateElement(el);
    });
  }

  injectStyle();
  scanAndDecorate();

  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      m.addedNodes.forEach((n) => {
        if (n.nodeType === 1) {
          scanAndDecorate(n);
        }
      });
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();

