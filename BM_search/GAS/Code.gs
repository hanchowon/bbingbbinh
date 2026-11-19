/**
 * ==============================================================================
 * Google Apps Script WebApp Backend Controller (Code.gs)
 * - 역할:
 *   1. 웹앱 진입점(doGet) 서빙
 *   2. Python FastAPI 백엔드(Cloud Run)와의 UrlFetchApp 프록시 통신
 *   3. Google Sheets 연동 벤치마크 로깅
 * ==============================================================================
 */

// Cloud Run 기본 배포 엔드포인트 (PropertiesService 설정 시 우선 적용)
var DEFAULT_BACKEND_URL = 'https://bbingbbinh-git-nqvypngzcq-uc.a.run.app';

/**
 * 웹앱 진입점 핸들러
 */
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('ALGO.VIZ // BFS vs DFS Maze Benchmark')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0');
}

/**
 * 백엔드 서버 URL 조회 (PropertiesService 활용)
 */
function getBackendUrl() {
  try {
    var userProps = PropertiesService.getScriptProperties();
    var customUrl = userProps.getProperty('BACKEND_URL');
    return customUrl ? customUrl.trim() : DEFAULT_BACKEND_URL;
  } catch (err) {
    Logger.log('PropertiesService 오류: ' + err.toString());
    return DEFAULT_BACKEND_URL;
  }
}

/**
 * Python FastAPI 백엔드로 미로 탐색 비교 요청
 * @param {Object} payload { maze, start, goal }
 * @return {Object} BFS & DFS 비교 시뮬레이션 결과 JSON
 */
function fetchAlgorithmComparison(payload) {
  var baseUrl = getBackendUrl();
  var endpoint = baseUrl.replace(/\/+$/, '') + '/api/maze/compare';

  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload || {}),
    muteHttpExceptions: true
  };

  try {
    var response = UrlFetchApp.fetch(endpoint, options);
    var statusCode = response.getResponseCode();
    var responseText = response.getContentText();

    if (statusCode >= 200 && statusCode < 300) {
      return {
        success: true,
        data: JSON.parse(responseText)
      };
    } else {
      Logger.log('API 서버 응답 에러 (HTTP ' + statusCode + '): ' + responseText);
      return {
        success: false,
        statusCode: statusCode,
        error: responseText
      };
    }
  } catch (e) {
    Logger.log('UrlFetchApp 호출 예외: ' + e.toString());
    return {
      success: false,
      error: e.toString()
    };
  }
}

/**
 * 미로 탐색 벤치마크 결과를 Google Sheets에 자동 기록
 * @param {Object} benchData { bfsPath, dfsPath, bfsVisited, dfsVisited, bfsTime, dfsTime, winner }
 */
function recordBenchmarkToSheet(benchData) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss) {
      return { success: false, message: '활성화된 스프레드시트가 없습니다.' };
    }

    var sheetName = 'Benchmark_Logs';
    var sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
      sheet.appendRow([
        '타임스탬프',
        'BFS 최단경로 길이',
        'DFS 경로 길이',
        'BFS 방문 노드',
        'DFS 방문 노드',
        'BFS 소요시간(ms)',
        'DFS 소요시간(ms)',
        '최적 승자'
      ]);
      sheet.getRange(1, 1, 1, 8).setFontWeight('bold').setBackground('#1e293b').setFontColor('#f8fafc');
    }

    sheet.appendRow([
      new Date(),
      benchData.bfsPath || 0,
      benchData.dfsPath || 0,
      benchData.bfsVisited || 0,
      benchData.dfsVisited || 0,
      benchData.bfsTime || 0,
      benchData.dfsTime || 0,
      benchData.winner || 'BFS'
    ]);

    return { success: true };
  } catch (err) {
    Logger.log('시트 로깅 오류: ' + err.toString());
    return { success: false, error: err.toString() };
  }
}
