/**
 * ==============================================================================
 * Google Apps Script (GAS) - 보이어-무어(Boyer-Moore) 알고리즘 시각화 백엔드
 * 파일명: Code.gs
 * ==============================================================================
 */

/**
 * 웹 앱 URL 접속 시 index.html 화면 렌더링
 * @param {Object} e HTTP GET 이벤트 객체
 * @return {HtmlOutput} 렌더링된 HTML 웹페이지
 */
function doGet(e) {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle('보이어-무어 알고리즘 시각화 도구 | BM-Visualizer')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * HTML 내 모듈 포함 헬퍼 함수
 * @param {string} filename 불러올 파일명
 * @return {string} 파일 내용
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * [GAS 프록시 함수] Google Cloud Run 백엔드 헬스체크
 * @param {string} serverUrl 백엔드 서버 URL
 * @return {Object} 서버 상태 객체
 */
function checkServerHealthFromGAS(serverUrl) {
  try {
    if (!serverUrl || typeof serverUrl !== 'string') {
      return { online: false, error: '유효한 서버 URL이 전달되지 않았습니다.' };
    }

    var cleanUrl = serverUrl.replace(/\/+$/, '');
    var healthUrl = cleanUrl + '/health';

    var options = {
      method: 'get',
      muteHttpExceptions: true,
      headers: { 'Accept': 'application/json' }
    };

    var response = UrlFetchApp.fetch(healthUrl, options);
    var statusCode = response.getResponseCode();
    var responseText = response.getContentText();

    if (statusCode >= 200 && statusCode < 300) {
      return { online: true, statusCode: statusCode, data: JSON.parse(responseText) };
    } else {
      return { online: false, error: '서버 응답 오류 (코드: ' + statusCode + ')' };
    }
  } catch (err) {
    return { online: false, error: err.message || String(err) };
  }
}

/**
 * [GAS 프록시 함수] Google Cloud Run 백엔드에 보이어-무어 시뮬레이션 요청
 * @param {string} serverUrl 백엔드 서버 URL
 * @param {string} text 검색 대상 텍스트
 * @param {string} pattern 검색할 패턴
 * @return {Object} 시뮬레이션 단계 데이터
 */
function requestBoyerMooreFromServer(serverUrl, text, pattern) {
  try {
    if (!serverUrl || typeof serverUrl !== 'string') {
      return simulateBoyerMooreLocally(text, pattern);
    }

    var cleanUrl = serverUrl.replace(/\/+$/, '');
    var targetUrl = cleanUrl + '/boyer-moore';

    var payload = {
      text: text || "BABBABABAC",
      pattern: pattern || "BABACB"
    };

    var options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
      headers: { 'Accept': 'application/json' }
    };

    var response = UrlFetchApp.fetch(targetUrl, options);
    var statusCode = response.getResponseCode();
    var responseText = response.getContentText();

    if (statusCode >= 200 && statusCode < 300) {
      return JSON.parse(responseText);
    } else {
      var fallback = simulateBoyerMooreLocally(text, pattern);
      fallback.warning = '서버 응답 오류(코드: ' + statusCode + ')로 인해 GAS 자체 엔진으로 연산되었습니다.';
      return fallback;
    }
  } catch (err) {
    var fallbackData = simulateBoyerMooreLocally(text, pattern);
    fallbackData.warning = '백엔드 연결 실패(' + (err.message || String(err)) + ')로 인해 GAS 자체 엔진으로 연산되었습니다.';
    return fallbackData;
  }
}

/**
 * [GAS 자체 내장 연산 엔진] 단계별 히스토그램 스냅샷 및 시간 복잡도 메타데이터 생성
 * @param {string} text 검색 대상 텍스트
 * @param {string} pattern 검색 패턴
 * @return {Object} 보이어-무어 단계별 연산 결과
 */
function simulateBoyerMooreLocally(text, pattern) {
  var t = (text || "BABBABABAC").toUpperCase();
  var p = (pattern || "BABACB").toUpperCase();
  var n = t.length;
  var m = p.length;

  var startTime = new Date().getTime();

  // 1. 나쁜 문자 테이블 생성
  var badChar = {};
  for (var i = 0; i < m; i++) {
    badChar[p.charAt(i)] = i;
  }

  // 2. 착한 접미부 테이블 생성
  var suff = new Array(m).fill(0);
  suff[m - 1] = m;
  var g = m - 1;
  var f = m - 1;

  for (var i = m - 2; i >= 0; --i) {
    if (i > g && suff[i + m - 1 - f] < i - g) {
      suff[i] = suff[i + m - 1 - f];
    } else {
      if (i < g) g = i;
      f = i;
      while (g >= 0 && p.charAt(g) === p.charAt(g + m - 1 - f)) {
        --g;
      }
      suff[i] = f - g;
    }
  }

  var goodSuffix = new Array(m + 1).fill(m);
  var jdx = 0;
  for (var i = m - 1; i >= -1; --i) {
    if (i === -1 || suff[i] === i + 1) {
      for (; jdx < m - 1 - i; ++jdx) {
        if (goodSuffix[jdx] === m) {
          goodSuffix[jdx] = m - 1 - i;
        }
      }
    }
  }
  for (var i = 0; i <= m - 2; ++i) {
    goodSuffix[m - 1 - suff[i]] = m - 1 - i;
  }

  // 3. 단계별 시뮬레이션 및 히스토그램 스냅샷 기록
  var steps = [];
  var matches = [];
  var totalComps = 0;
  var k = 0;
  var maxK = Math.max(n - m, 1);
  var bcCounts = {};
  var gsCounts = {};

  while (k <= n - m) {
    var j = m - 1;
    var matchedSub = [];
    var isMismatch = false;

    while (j >= 0) {
      totalComps++;
      var ct = t.charAt(k + j);
      var cp = p.charAt(j);

      bcCounts[k] = (bcCounts[k] || 0) + 1;
      gsCounts[k] = (gsCounts[k] || 0) + 1;

      var progressPct = Math.min(100.0, Math.round(((k + (m - 1 - j) / m) / (maxK + 1)) * 100 * 10) / 10);
      var currentElapsedMs = new Date().getTime() - startTime;

      var bcBars = [];
      var gsBars = [];
      for (var offset = 0; offset <= n - m; offset++) {
        bcBars.push({
          k: offset,
          label: "k=" + offset,
          comparisons: bcCounts[offset] || 0,
          is_active: (offset === k)
        });
        gsBars.push({
          k: offset,
          label: "k=" + offset,
          comparisons: gsCounts[offset] || 0,
          is_active: (offset === k)
        });
      }

      if (ct === cp) {
        matchedSub.push(cp);
        steps.push({
          step_index: steps.length + 1,
          k: k,
          j: j,
          text_index: k + j,
          char_text: ct,
          char_pattern: cp,
          type: "MATCH",
          matched_suffix: matchedSub.slice().reverse().join(''),
          shift_bad_char: 0,
          shift_good_suffix: 0,
          final_shift: 0,
          next_k: k,
          time_ms: currentElapsedMs,
          complexity_progress_pct: progressPct,
          histogram: {
            bad_char_bars: bcBars,
            good_suffix_bars: gsBars
          },
          explanation: "P[" + j + "]('" + cp + "') == T[" + (k + j) + "]('" + ct + "') 일치"
        });
        j--;
      } else {
        isMismatch = true;
        var bcPos = (badChar[ct] !== undefined) ? badChar[ct] : -1;
        var bcShift = Math.max(1, j - bcPos);
        var gsShift = (j + 1 < goodSuffix.length) ? goodSuffix[j + 1] : 1;
        var finalShift = Math.max(bcShift, gsShift);
        var nextK = k + finalShift;
        var ruleAdopted = (gsShift >= bcShift) ? "Good Suffix(Δ₂)" : "Bad Character(Δ₁)";

        steps.push({
          step_index: steps.length + 1,
          k: k,
          j: j,
          text_index: k + j,
          char_text: ct,
          char_pattern: cp,
          type: "MISMATCH",
          matched_suffix: matchedSub.slice().reverse().join(''),
          shift_bad_char: bcShift,
          shift_good_suffix: gsShift,
          final_shift: finalShift,
          next_k: nextK,
          rule_adopted: ruleAdopted,
          time_ms: currentElapsedMs,
          complexity_progress_pct: progressPct,
          histogram: {
            bad_char_bars: bcBars,
            good_suffix_bars: gsBars
          },
          explanation: "P[" + j + "] != T[" + (k + j) + "] 불일치 -> " + ruleAdopted + " 적용 (" + finalShift + "칸 도약)"
        });
        k = nextK;
        break;
      }
    }

    if (!isMismatch) {
      matches.push(k);
      var fs = goodSuffix[0] || 1;
      steps.push({
        step_index: steps.length + 1,
        k: k,
        j: 0,
        text_index: k,
        char_text: t.charAt(k),
        char_pattern: p.charAt(0),
        type: "FULL_MATCH",
        matched_suffix: p,
        shift_bad_char: 0,
        shift_good_suffix: fs,
        final_shift: fs,
        next_k: k + fs,
        rule_adopted: "Match Found",
        time_ms: new Date().getTime() - startTime,
        complexity_progress_pct: 100.0,
        histogram: {
          bad_char_bars: bcBars,
          good_suffix_bars: gsBars
        },
        explanation: "패턴 일치 발견! (위치: " + k + ")"
      });
      k += fs;
    }
  }

  var elapsedMs = new Date().getTime() - startTime;

  return {
    text: t,
    pattern: p,
    bad_character_table: badChar,
    good_suffix_table: goodSuffix,
    steps: steps,
    matches: matches,
    total_comparisons: totalComps,
    brute_force_comparisons: (n - m + 1) * 2,
    efficiency_gain_pct: Math.round(((n - m + 1) * 2 - totalComps) / ((n - m + 1) * 2) * 100),
    elapsed_ms: elapsedMs,
    engine: "Google Apps Script V8 Engine"
  };
}
