/* 인스타그램 게시물에서 본문·날짜 뽑기
   브라우저에서 게시물 URL(https://www.instagram.com/p/XXXX/)을 연 뒤 이 코드를 실행.
   로그인 없이 공개 게시물이면 동작한다. 결과를 그대로 manual.csv 만들 때 쓴다. */
(function () {
  // "더 보기"를 눌러 본문 전체를 펼친다
  var more = Array.prototype.slice.call(
    document.querySelectorAll('button,span[role="button"],div[role="button"]')
  ).find(function (e) { return /더 보기|more/i.test(e.textContent) && e.textContent.length < 12; });
  if (more) more.click();

  return new Promise(function (resolve) {
    setTimeout(function () {
      var h1 = document.querySelector("h1");
      var t  = document.querySelector("time");
      var who = document.querySelector('header a[href^="/"]');
      resolve(JSON.stringify({
        url: location.href.split("?")[0],
        account: who ? who.getAttribute("href").replace(/\//g, "") : "",
        posted: t ? t.getAttribute("datetime") : "",
        caption: h1 ? h1.textContent : ""
      }));
    }, 700);
  });
})();
