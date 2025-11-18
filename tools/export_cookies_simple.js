/**
 * DeviantArt Cookie 超简单导出工具
 * 直接复制Cookie到剪贴板，无UI
 */

// 方式1: 一行版本（推荐）
// 复制粘贴到控制台：
copy(document.cookie);console.log('%c✓ Cookie已复制！','color:#4ade80;font-size:16px;font-weight:bold');console.log('%c下一步运行: devart-dl login interactive','color:#666;font-size:14px');

// 方式2: 带提示版本
// 复制粘贴到控制台：
(function(){let c=document.cookie;if(!c){alert('❌ 未检测到Cookie，请先登录！');return}navigator.clipboard.writeText(c).then(()=>{console.log('%c✓ Cookie已复制到剪贴板！','color:#4ade80;font-size:16px;font-weight:bold');console.log('%cCookie内容:','color:#667eea;font-weight:bold');console.log(c);console.log('%c\n下一步：','color:#666;font-weight:bold');console.log('1. 运行: devart-dl login interactive');console.log('2. 粘贴上面的Cookie');alert('✓ Cookie已复制！\n\n长度: '+c.length+' 字符\n\n下一步:\n1. 运行: devart-dl login interactive\n2. 粘贴Cookie')}).catch(e=>{console.error('复制失败:',e);alert('请手动复制控制台中的Cookie')})})();

// 方式3: 超极简版本（仅复制）
copy(document.cookie);

// 方式4: 显示并复制
console.log(document.cookie);copy(document.cookie);

// 方式5: 保存为变量
var myCookie = document.cookie; copy(myCookie); console.log('Cookie已保存到变量 myCookie 并复制到剪贴板');
