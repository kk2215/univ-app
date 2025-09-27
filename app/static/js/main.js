// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
  // アニメーションさせたい要素を全て取得
  const animatedElements = document.querySelectorAll('.animate-on-scroll');

  // Intersection Observer の設定
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      // 要素が画面内に入ったら is-visible クラスを追加
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
      }
    });
  }, {
    threshold: 0.1 // 要素が10%見えたらトリガー
  });

  // 各要素の監視を開始
  animatedElements.forEach(el => {
    observer.observe(el);
  });
});