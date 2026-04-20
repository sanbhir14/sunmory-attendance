const CONFIG = {
  rawSheetName: 'Form_Responses',
  sessionsSheetName: 'sessions',
  performanceSheetName: 'performance_log',
  playersSheetName: 'players_db',
  referralSheetName: 'referral_log',
  rewardSheetName: 'reward_status',
  webhookToken: '',
  rewards: [
    { stamps: 3, reward: 'Free drink/snack' },
    { stamps: 5, reward: 'Diskon session' },
    { stamps: 10, reward: 'Free 1 session' },
    { stamps: 15, reward: 'VIP / priority booking' },
  ],
};

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Sunmory')
    .addItem('Process Attendance', 'processAttendance')
    .addToUi();
}

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents || '{}');
    if (CONFIG.webhookToken && payload.token !== CONFIG.webhookToken) {
      return jsonResponse_({ ok: false, error: 'Unauthorized token' }, 401);
    }

    if (payload.action === 'append_session') {
      const record = payload.session || {};
      appendSession_(record);
      return jsonResponse_({ ok: true, session_id: record.session_id, session_code: record.session_code });
    }

    if (payload.action === 'append_performance') {
      const records = payload.records || [];
      appendPerformanceRecords_(records);
      return jsonResponse_({ ok: true, inserted: records.length });
    }

    return jsonResponse_({ ok: false, error: 'Unsupported action' }, 400);
  } catch (error) {
    return jsonResponse_({ ok: false, error: String(error.message || error) }, 500);
  }
}

function doGet(e) {
  try {
    const action = e.parameter.action || '';
    if (action === 'performance_summary') {
      return jsonResponse_({ ok: true, data: getPerformanceSummary_() });
    }
    return jsonResponse_({ ok: false, error: 'Unsupported action' }, 400);
  } catch (error) {
    return jsonResponse_({ ok: false, error: String(error.message || error) }, 500);
  }
}

function processAttendance() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rawSheet = getSheetByPossibleNames_(ss, [CONFIG.rawSheetName, 'Form Responses 1']);
  if (!rawSheet) {
    throw new Error('Raw form sheet tidak ketemu. Rename tab response menjadi Form_Responses atau Form Responses 1.');
  }

  const values = rawSheet.getDataRange().getValues();
  if (values.length < 2) {
    writeSheet_(ss, CONFIG.playersSheetName, getPlayersHeader_(), []);
    writeSheet_(ss, CONFIG.referralSheetName, getReferralHeader_(), []);
    writeSheet_(ss, CONFIG.rewardSheetName, getRewardHeader_(), []);
    return;
  }

  const headers = values[0].map(normalizeHeader_);
  const rows = values.slice(1).map((row) => rowToRecord_(headers, row)).filter((record) => record.name);
  const uniqueAttendance = dedupeAttendance_(rows);
  const players = buildPlayers_(uniqueAttendance);
  const referrals = buildReferralLog_(uniqueAttendance);
  const rewards = buildRewardStatus_(players);

  writeSheet_(ss, CONFIG.playersSheetName, getPlayersHeader_(), players);
  writeSheet_(ss, CONFIG.referralSheetName, getReferralHeader_(), referrals);
  writeSheet_(ss, CONFIG.rewardSheetName, getRewardHeader_(), rewards);
}

function appendSession_(record) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const header = getSessionsHeader_();
  let sheet = ss.getSheetByName(CONFIG.sessionsSheetName);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.sessionsSheetName);
    sheet.getRange(1, 1, 1, header.length).setValues([header]);
    sheet.setFrozenRows(1);
  }

  const existingValues = sheet.getDataRange().getValues();
  const existingSessionIds = existingValues.slice(1).map((row) => String(row[0] || '').trim());
  if (existingSessionIds.includes(String(record.session_id || '').trim())) {
    throw new Error(`Session ${record.session_id} sudah ada di tab sessions.`);
  }

  const row = header.map((key) => record[key] || '');
  sheet.appendRow(row);
  sheet.autoResizeColumns(1, header.length);
}

function appendPerformanceRecords_(records) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const header = getPerformanceHeader_();
  let sheet = ss.getSheetByName(CONFIG.performanceSheetName);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.performanceSheetName);
    sheet.getRange(1, 1, 1, header.length).setValues([header]);
    sheet.setFrozenRows(1);
  }

  const rows = records
    .filter((record) => String(record.player_name || '').trim())
    .map((record) => {
      const playerName = normalizeName_(record.player_name);
      const enriched = {
        created_at: record.created_at || new Date(),
        session_id: String(record.session_id || '').trim(),
        session_code: String(record.session_code || '').trim().toUpperCase(),
        session_date: record.session_date || '',
        venue: String(record.venue || '').trim(),
        player_name: playerName,
        player_key: makePlayerKey_(playerName),
        matches_played: Number(record.matches_played || 0),
        wins: Number(record.wins || 0),
        losses: Number(record.losses || 0),
        points: Number(record.points || 0),
        notes: String(record.notes || '').trim(),
      };
      return header.map((key) => enriched[key] || '');
    });

  if (!rows.length) {
    throw new Error('Tidak ada performance record valid untuk ditulis.');
  }

  sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, header.length).setValues(rows);
  sheet.autoResizeColumns(1, header.length);
}

function getPerformanceSummary_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.performanceSheetName);
  if (!sheet || sheet.getLastRow() < 2) {
    return { summary: [], records: [] };
  }

  const values = sheet.getDataRange().getValues();
  const headers = values[0].map((header) => String(header || '').trim());
  const records = values.slice(1).map((row) => {
    const record = {};
    headers.forEach((header, index) => {
      record[header] = row[index];
    });
    return record;
  });

  const byPlayer = {};
  records.forEach((record) => {
    const playerKey = String(record.player_key || makePlayerKey_(record.player_name)).trim();
    if (!playerKey) return;
    if (!byPlayer[playerKey]) {
      byPlayer[playerKey] = {
        player_name: record.player_name,
        total_points: 0,
        matches_played: 0,
        wins: 0,
        losses: 0,
        sessions_played: {},
        last_session_date: record.session_date || '',
      };
    }
    const player = byPlayer[playerKey];
    player.player_name = record.player_name || player.player_name;
    player.total_points += Number(record.points || 0);
    player.matches_played += Number(record.matches_played || 0);
    player.wins += Number(record.wins || 0);
    player.losses += Number(record.losses || 0);
    if (record.session_id) player.sessions_played[record.session_id] = true;
    if (record.session_date && String(record.session_date) > String(player.last_session_date || '')) {
      player.last_session_date = record.session_date;
    }
  });

  const summary = Object.values(byPlayer)
    .map((player) => {
      const totalMatches = Number(player.matches_played || 0);
      return {
        player_name: player.player_name,
        total_points: player.total_points,
        matches_played: totalMatches,
        wins: player.wins,
        losses: player.losses,
        win_rate: totalMatches ? player.wins / totalMatches : 0,
        sessions_played: Object.keys(player.sessions_played).length,
        last_session_date: player.last_session_date,
      };
    })
    .sort((a, b) => b.total_points - a.total_points || b.wins - a.wins || a.player_name.localeCompare(b.player_name));

  summary.forEach((player, index) => {
    player.rank = index + 1;
  });

  return { summary, records };
}

function rowToRecord_(headers, row) {
  const record = {};
  headers.forEach((header, index) => {
    record[header] = row[index];
  });

  const name = normalizeName_(record.name);
  const venue = String(record.venue || '').trim();
  const date = parseDate_(record.date);
  const timestamp = parseDate_(record.timestamp);
  const referralCode = normalizeReferralCode_(record.referral_code);
  const sessionId = makeSessionId_(date, venue);

  return {
    timestamp,
    name,
    player_key: makePlayerKey_(name),
    venue,
    date,
    referral_code: referralCode,
    session_id: sessionId,
  };
}

function dedupeAttendance_(rows) {
  const seen = {};
  return rows.filter((row) => {
    const key = `${row.player_key}::${row.session_id}`;
    if (seen[key]) return false;
    seen[key] = true;
    return true;
  });
}

function buildPlayers_(rows) {
  const byPlayer = {};

  rows.forEach((row) => {
    if (!byPlayer[row.player_key]) {
      byPlayer[row.player_key] = {
        player_key: row.player_key,
        name: row.name,
        total_attendance: 0,
        total_stamp: 0,
        last_played: row.date,
        venues: {},
        first_referral_code: '',
      };
    }

    const player = byPlayer[row.player_key];
    player.total_attendance += 1;
    player.total_stamp += 1;
    player.last_played = maxDate_(player.last_played, row.date);
    if (row.venue) player.venues[row.venue] = true;
    if (!player.first_referral_code && row.referral_code) {
      player.first_referral_code = row.referral_code;
    }
  });

  return Object.values(byPlayer)
    .sort((a, b) => b.total_stamp - a.total_stamp || String(a.name).localeCompare(String(b.name)))
    .map((player) => {
      const next = getNextReward_(player.total_stamp);
      return [
        player.player_key,
        player.name,
        player.total_attendance,
        player.total_stamp,
        player.last_played,
        Object.keys(player.venues).sort().join(', '),
        Object.keys(player.venues).length,
        getEligibleRewards_(player.total_stamp).join(', '),
        next.reward,
        next.stamps_remaining,
        player.first_referral_code,
        new Date(),
      ];
    });
}

function buildReferralLog_(rows) {
  const usedByPlayer = {};

  return rows
    .filter((row) => row.referral_code)
    .map((row) => {
      const alreadyUsed = Boolean(usedByPlayer[row.player_key]);
      const status = alreadyUsed ? 'invalid_duplicate_player_referral' : 'valid_first_referral';
      if (!alreadyUsed) usedByPlayer[row.player_key] = row.referral_code;

      return [
        row.timestamp,
        row.date,
        row.name,
        row.player_key,
        row.referral_code,
        status,
      ];
    });
}

function buildRewardStatus_(playerRows) {
  return playerRows.map((player) => {
    const name = player[1];
    const totalStamp = player[3];
    const next = getNextReward_(totalStamp);
    return [
      player[0],
      name,
      totalStamp,
      getEligibleRewards_(totalStamp).join(', '),
      next.reward,
      next.stamps_remaining,
      next.stamps_remaining === 0 ? 'eligible_all_main_rewards' : 'in_progress',
    ];
  });
}

function getPlayersHeader_() {
  return [
    'player_key',
    'name',
    'total_attendance',
    'total_stamp',
    'last_played',
    'venues',
    'venue_count',
    'eligible_rewards',
    'next_reward',
    'stamps_remaining',
    'first_referral_code',
    'updated_at',
  ];
}

function getReferralHeader_() {
  return ['timestamp', 'date', 'name', 'player_key', 'referral_code', 'status'];
}

function getRewardHeader_() {
  return ['player_key', 'name', 'total_stamp', 'eligible_rewards', 'next_reward', 'stamps_remaining', 'status'];
}

function getSessionsHeader_() {
  return ['session_id', 'session_code', 'venue', 'session_date', 'session_slot', 'status', 'created_at'];
}

function getPerformanceHeader_() {
  return [
    'created_at',
    'session_id',
    'session_code',
    'session_date',
    'venue',
    'player_name',
    'player_key',
    'matches_played',
    'wins',
    'losses',
    'points',
    'notes',
  ];
}

function writeSheet_(ss, sheetName, header, rows) {
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) sheet = ss.insertSheet(sheetName);
  sheet.clearContents();
  sheet.getRange(1, 1, 1, header.length).setValues([header]);
  if (rows.length) {
    sheet.getRange(2, 1, rows.length, header.length).setValues(rows);
  }
  sheet.setFrozenRows(1);
  sheet.autoResizeColumns(1, header.length);
}

function getSheetByPossibleNames_(ss, names) {
  for (const name of names) {
    const sheet = ss.getSheetByName(name);
    if (sheet) return sheet;
  }
  return null;
}

function jsonResponse_(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}

function normalizeHeader_(value) {
  const header = String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  const aliases = {
    referal_code: 'referral_code',
    kode_referal: 'referral_code',
    kode_referral: 'referral_code',
    nama: 'name',
    tanggal: 'date',
  };
  return aliases[header] || header;
}

function normalizeName_(name) {
  return String(name || '').trim().replace(/\s+/g, ' ').toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}

function normalizeReferralCode_(code) {
  const cleaned = String(code || '').trim().toUpperCase();
  if (!cleaned || ['-', 'NO', 'NONE', 'N/A', 'NA', 'TIDAK', 'GA', 'GAK'].includes(cleaned)) return '';
  return cleaned;
}

function makePlayerKey_(name) {
  return normalizeName_(name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function makeSessionId_(date, venue) {
  const formattedDate = Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyyMMdd');
  const venueKey = String(venue || 'unknown').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return `${formattedDate}-${venueKey}`;
}

function parseDate_(value) {
  if (value instanceof Date) return value;
  const parsed = new Date(value);
  if (!isNaN(parsed.getTime())) return parsed;
  return new Date();
}

function maxDate_(a, b) {
  return a.getTime() >= b.getTime() ? a : b;
}

function getEligibleRewards_(totalStamp) {
  return CONFIG.rewards.filter((item) => totalStamp >= item.stamps).map((item) => item.reward);
}

function getNextReward_(totalStamp) {
  for (const item of CONFIG.rewards) {
    if (totalStamp < item.stamps) {
      return {
        reward: item.reward,
        stamps_remaining: item.stamps - totalStamp,
      };
    }
  }
  return {
    reward: 'Semua reward utama sudah tercapai',
    stamps_remaining: 0,
  };
}
