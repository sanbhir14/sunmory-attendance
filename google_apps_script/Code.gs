const CONFIG = {
  rawSheetName: 'Form_Responses',
  attendanceSheetName: 'attendance_log',
  sessionsSheetName: 'sessions',
  performanceSheetName: 'performance_log',
  financeIncomeSheetName: 'finance_income',
  financeExpenseSheetName: 'finance_expenses',
  playersSheetName: 'players_db',
  referralSheetName: 'referral_log',
  rewardSheetName: 'reward_status',
  webhookToken: '',
  rewards: [
    { stamps: 3, reward: '10% diskon session' },
    { stamps: 5, reward: 'Free coffee' },
    { stamps: 8, reward: '20% diskon session' },
    { stamps: 10, reward: '50% diskon session' },
  ],
};

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Sunmory')
    .addItem('Process Attendance', 'processAttendance')
    .addItem('Rebuild Player DB', 'rebuildPlayerDbFromAttendance')
    .addToUi();
}

function rebuildPlayerDbFromAttendance() {
  rebuildPlayersDb_(SpreadsheetApp.getActiveSpreadsheet(), true);
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

    if (payload.action === 'append_attendance') {
      const record = payload.attendance || {};
      const result = appendAttendance_(record);
      return jsonResponse_(Object.assign({ ok: true }, result));
    }

    if (payload.action === 'update_session_status') {
      const sessionId = String(payload.session_id || '').trim();
      const status = String(payload.status || '').trim().toLowerCase();
      updateSessionStatus_(sessionId, status);
      return jsonResponse_({ ok: true, session_id: sessionId, status });
    }

    if (payload.action === 'rebuild_players_db') {
      rebuildPlayersDb_(SpreadsheetApp.getActiveSpreadsheet(), true);
      return jsonResponse_({ ok: true });
    }

    if (payload.action === 'rebuild_finance') {
      rebuildFinanceSheets_(SpreadsheetApp.getActiveSpreadsheet());
      return jsonResponse_({ ok: true });
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
    if (action === 'open_sessions') {
      return jsonResponse_({ ok: true, data: getOpenSessions_() });
    }
    if (action === 'all_sessions') {
      return jsonResponse_({ ok: true, data: getAllSessions_() });
    }
    if (action === 'attendance_records') {
      return jsonResponse_({ ok: true, data: getAttendanceRecords_() });
    }
    if (action === 'players_db') {
      return jsonResponse_({ ok: true, data: getPlayersDbRecords_() });
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
  const sheet = ensureSheet_(ss, CONFIG.sessionsSheetName, header);

  const existingValues = sheet.getDataRange().getValues();
  const existingSessionIds = existingValues.slice(1).map((row) => String(row[0] || '').trim());
  if (existingSessionIds.includes(String(record.session_id || '').trim())) {
    throw new Error(`Session ${record.session_id} sudah ada di tab sessions.`);
  }

  const sessionRecord = {
    session_id: String(record.session_id || '').trim(),
    session_code: String(record.session_code || '').trim().toUpperCase(),
    venue: String(record.venue || '').trim(),
    session_date: record.session_date || '',
    session_slot: String(record.session_slot || '').trim(),
    status: String(record.status || 'open').trim().toLowerCase(),
    expense_amount: Number(record.expense_amount || 0),
    player_price: Number(record.player_price || 0),
    paid_by: String(record.paid_by || '').trim(),
    created_at: record.created_at || new Date(),
  };

  appendRecordByHeader_(sheet, sessionRecord);
  appendExpenseRecord_(ss, sessionRecord);
}

function getOpenSessions_() {
  return getAllSessions_().filter((record) => String(record.status || '').toLowerCase() === 'open');
}

function getAllSessions_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ensureSheet_(ss, CONFIG.sessionsSheetName, getSessionsHeader_());
  if (!sheet || sheet.getLastRow() < 2) return [];

  const values = sheet.getDataRange().getValues();
  const headers = values[0].map((header) => String(header || '').trim());
  return values
    .slice(1)
    .map((row) => {
      const record = {};
      headers.forEach((header, index) => {
        record[header] = row[index];
      });
      return record;
    })
    .sort((a, b) => String(b.session_date || '').localeCompare(String(a.session_date || '')));
}

function updateSessionStatus_(sessionId, status) {
  if (!sessionId) throw new Error('session_id wajib diisi.');
  if (!['open', 'closed'].includes(status)) throw new Error('Status harus open atau closed.');

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sessionsSheetName);
  if (!sheet || sheet.getLastRow() < 2) throw new Error('Tab sessions belum ada atau masih kosong.');

  const values = sheet.getDataRange().getValues();
  const headers = values[0].map((header) => String(header || '').trim());
  const sessionIdIndex = headers.indexOf('session_id');
  const statusIndex = headers.indexOf('status');
  if (sessionIdIndex < 0 || statusIndex < 0) throw new Error('Kolom session_id/status tidak ditemukan.');

  for (let rowIndex = 1; rowIndex < values.length; rowIndex += 1) {
    if (String(values[rowIndex][sessionIdIndex] || '').trim() === sessionId) {
      sheet.getRange(rowIndex + 1, statusIndex + 1).setValue(status);
      return;
    }
  }
  throw new Error(`Session ${sessionId} tidak ditemukan.`);
}

function appendAttendance_(record) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sessionId = String(record.session_id || '').trim();
  const username = normalizeUsername_(record.username_reclub);
  if (!sessionId) throw new Error('Session wajib dipilih.');
  if (!username) throw new Error('Username Reclub wajib diisi.');

  const session = findSessionById_(ss, sessionId);
  if (!session) throw new Error(`Session ${sessionId} tidak ditemukan.`);
  if (String(session.status || '').toLowerCase() !== 'open') {
    throw new Error(`Session ${sessionId} sudah closed.`);
  }

  const header = getAttendanceHeader_();
  const sheet = ensureSheet_(ss, CONFIG.attendanceSheetName, header);
  const playerName = normalizeName_(record.player_name || username);
  const playerKey = makePlayerKeyFromUsername_(username);

  const existingAttendance = recordsFromSheet_(sheet);
  const duplicate = existingAttendance.some((row) => (
    String(row.attendance_type || 'regular').trim() !== 'referral_bonus'
    && String(row.session_id || '').trim() === sessionId
    && (
      String(row.player_key || '').trim() === playerKey
      || normalizeUsername_(row.username_reclub) === username
    )
  ));
  if (duplicate) {
    throw new Error(`${username} sudah check-in di session ini.`);
  }

  rebuildPlayersDb_(ss, false);
  const players = readPlayersByKey_(ss);
  const referralOwners = readPlayersByReferralCode_(ss);
  const player = players[playerKey] || {};
  const referralCodeUsed = normalizeReferralCode_(record.referral_code);
  let referralStatus = referralCodeUsed ? 'invalid_referral_code' : 'no_referral';

  if (referralCodeUsed) {
    if (String(player.referral_used_code || '').trim()) {
      referralStatus = 'invalid_already_used_referral';
    } else {
      const owner = referralOwners[referralCodeUsed];
      if (!owner) {
        referralStatus = 'invalid_referral_code';
      } else if (String(owner.player_key || '').trim() === playerKey) {
        referralStatus = 'invalid_self_referral';
      } else {
        referralStatus = 'valid_first_referral';
      }
    }
  }

  const attendanceRecord = {
    created_at: new Date(),
    attendance_id: makeAttendanceId_(playerKey, sessionId),
    session_id: sessionId,
    session_code: String(session.session_code || record.session_code || '').trim().toUpperCase(),
    session_date: session.session_date || record.session_date || '',
    session_slot: String(session.session_slot || record.session_slot || '').trim(),
    venue: String(session.venue || record.venue || '').trim(),
    player_name: playerName,
    username_reclub: username,
    player_key: playerKey,
    referral_code_used: referralCodeUsed,
    referral_status: referralStatus,
    attendance_type: 'regular',
    base_price: Number(session.player_price || record.base_price || 0),
    claimed_reward: normalizeClaimedReward_(record.claimed_reward),
    discount_percent: getRewardDiscountPercent_(normalizeClaimedReward_(record.claimed_reward)),
    income_amount: calculateIncomeAmount_(Number(session.player_price || record.base_price || 0), normalizeClaimedReward_(record.claimed_reward)),
    notes: String(record.notes || '').trim(),
  };

  appendRecordByHeader_(sheet, attendanceRecord);
  appendIncomeRecord_(ss, attendanceRecord);
  rebuildPlayersDb_(ss, true);
  return {
    attendance_id: attendanceRecord.attendance_id,
    player_name: playerName,
    username_reclub: username,
    referral_status: referralStatus,
  };
}

function getAttendanceRecords_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.attendanceSheetName);
  if (!sheet || sheet.getLastRow() < 2) return [];
  return recordsFromSheet_(sheet);
}

function getPlayersDbRecords_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.playersSheetName);
  if (!sheet || sheet.getLastRow() < 2) return [];
  return recordsFromSheet_(sheet);
}

function appendExpenseRecord_(ss, sessionRecord) {
  const header = getFinanceExpenseHeader_();
  const sheet = ensureSheet_(ss, CONFIG.financeExpenseSheetName, header);
  const existing = recordsFromSheet_(sheet).some((row) => String(row.session_id || '').trim() === sessionRecord.session_id);
  if (existing) return;

  appendRecordByHeader_(sheet, buildExpenseRecord_(sessionRecord));
}

function appendIncomeRecord_(ss, attendanceRecord) {
  const header = getFinanceIncomeHeader_();
  const sheet = ensureSheet_(ss, CONFIG.financeIncomeSheetName, header);
  const existing = recordsFromSheet_(sheet).some((row) => String(row.attendance_id || '').trim() === attendanceRecord.attendance_id);
  if (existing) return;

  appendRecordByHeader_(sheet, buildIncomeRecord_(attendanceRecord));
}

function rebuildFinanceSheets_(ss) {
  const expenseHeader = getFinanceExpenseHeader_();
  const incomeHeader = getFinanceIncomeHeader_();
  const sessionsSheet = ensureSheet_(ss, CONFIG.sessionsSheetName, getSessionsHeader_());
  const attendanceSheet = ensureSheet_(ss, CONFIG.attendanceSheetName, getAttendanceHeader_());
  const sessions = recordsFromSheet_(sessionsSheet);
  const attendance = recordsFromSheet_(attendanceSheet);

  const expenseRows = sessions
    .filter((session) => String(session.session_id || '').trim())
    .map((session) => {
      const record = buildExpenseRecord_(session);
      return expenseHeader.map((key) => record[key] || '');
    });

  const incomeRows = attendance
    .filter((row) => String(row.attendance_id || '').trim())
    .filter((row) => String(row.attendance_type || 'regular').trim() !== 'referral_bonus')
    .map((row) => {
      const record = buildIncomeRecord_(row);
      return incomeHeader.map((key) => record[key] || '');
    });

  writeSheet_(ss, CONFIG.financeExpenseSheetName, expenseHeader, expenseRows);
  writeSheet_(ss, CONFIG.financeIncomeSheetName, incomeHeader, incomeRows);
}

function buildExpenseRecord_(sessionRecord) {
  return {
    created_at: new Date(),
    session_id: String(sessionRecord.session_id || '').trim(),
    session_code: String(sessionRecord.session_code || '').trim().toUpperCase(),
    session_date: sessionRecord.session_date || '',
    venue: String(sessionRecord.venue || '').trim(),
    expense_type: 'venue',
    amount: Number(sessionRecord.expense_amount || 0),
    paid_by: String(sessionRecord.paid_by || '').trim(),
    notes: 'Auto expense dari Session Generator',
  };
}

function buildIncomeRecord_(attendanceRecord) {
  return {
    created_at: attendanceRecord.created_at || new Date(),
    attendance_id: String(attendanceRecord.attendance_id || '').trim(),
    session_id: String(attendanceRecord.session_id || '').trim(),
    session_code: String(attendanceRecord.session_code || '').trim().toUpperCase(),
    session_date: attendanceRecord.session_date || '',
    venue: String(attendanceRecord.venue || '').trim(),
    username_reclub: String(attendanceRecord.username_reclub || '').trim(),
    player_name: String(attendanceRecord.player_name || '').trim(),
    base_price: Number(attendanceRecord.base_price || 0),
    claimed_reward: String(attendanceRecord.claimed_reward || '').trim(),
    discount_percent: Number(attendanceRecord.discount_percent || 0),
    income_amount: Number(attendanceRecord.income_amount || 0),
    notes: String(attendanceRecord.notes || '').trim(),
  };
}

function rebuildPlayersDb_(ss, addMissingBonuses) {
  const attendanceSheet = ensureSheet_(ss, CONFIG.attendanceSheetName, getAttendanceHeader_());
  let attendance = recordsFromSheet_(attendanceSheet);
  const existingPlayers = readPlayersByKey_(ss);
  const existingCodes = {};
  Object.values(existingPlayers).forEach((player) => {
    const code = normalizeReferralCode_(player.referral_code);
    if (code) existingCodes[code] = true;
  });

  let build = buildPlayersDbFromAttendance_(attendance, existingPlayers, existingCodes);
  if (addMissingBonuses) {
    const added = appendMissingReferralBonuses_(attendanceSheet, build.players, attendance);
    if (added > 0) {
      attendance = recordsFromSheet_(attendanceSheet);
      const generatedPlayers = {};
      Object.values(build.players).forEach((player) => {
        generatedPlayers[player.player_key] = player;
      });
      build = buildPlayersDbFromAttendance_(attendance, Object.assign({}, existingPlayers, generatedPlayers), existingCodes);
    }
  }

  writeSheet_(ss, CONFIG.playersSheetName, getPlayerDbHeader_(), build.playerRows);
  writeSheet_(ss, CONFIG.referralSheetName, getReferralHeader_(), build.referralRows);
  writeSheet_(ss, CONFIG.rewardSheetName, getRewardHeader_(), build.rewardRows);
}

function buildPlayersDbFromAttendance_(attendance, existingPlayers, existingCodes) {
  const players = {};
  const referralRows = [];
  const rewardRows = [];

  attendance.forEach((row) => {
    const username = normalizeUsername_(row.username_reclub);
    const playerKey = String(row.player_key || makePlayerKeyFromUsername_(username)).trim();
    if (!playerKey) return;

    if (!players[playerKey]) {
      const existing = existingPlayers[playerKey] || {};
      const referralCode = normalizeReferralCode_(existing.referral_code) || generateReferralCode_(username || row.player_name, existingCodes);
      players[playerKey] = {
        player_key: playerKey,
        username_reclub: username,
        player_name: normalizeName_(row.player_name || username),
        referral_code: referralCode,
        total_attendance: 0,
        total_stamp: 0,
        last_played: '',
        venues: {},
        referral_used_code: String(existing.referral_used_code || '').trim(),
        referred_by_player_key: String(existing.referred_by_player_key || '').trim(),
        valid_referral_count: 0,
        referral_bonus_attendance: 0,
      };
    }

    const player = players[playerKey];
    if (username) player.username_reclub = username;
    if (row.player_name) player.player_name = normalizeName_(row.player_name);
    player.total_attendance += 1;
    player.total_stamp += 1;

    const attendanceType = String(row.attendance_type || 'regular').trim();
    if (attendanceType === 'referral_bonus') {
      player.referral_bonus_attendance += 1;
    } else {
      if (row.venue) player.venues[String(row.venue).trim()] = true;
      if (row.session_date && String(row.session_date) > String(player.last_played || '')) {
        player.last_played = row.session_date;
      }
    }

    if (String(row.referral_status || '').trim() === 'valid_first_referral' && !player.referral_used_code) {
      player.referral_used_code = normalizeReferralCode_(row.referral_code_used);
    }
  });

  const referralOwners = {};
  Object.values(players).forEach((player) => {
    referralOwners[player.referral_code] = player;
  });

  const countedReferralUsers = {};
  attendance.forEach((row) => {
    if (String(row.referral_status || '').trim() !== 'valid_first_referral') return;
    const referredKey = String(row.player_key || '').trim();
    if (!referredKey || countedReferralUsers[referredKey]) return;
    countedReferralUsers[referredKey] = true;

    const code = normalizeReferralCode_(row.referral_code_used);
    const owner = referralOwners[code];
    if (!owner || owner.player_key === referredKey) return;

    owner.valid_referral_count += 1;
    players[referredKey].referred_by_player_key = owner.player_key;
    referralRows.push([
      row.created_at || '',
      row.session_date || '',
      players[referredKey].player_name,
      referredKey,
      code,
      owner.player_key,
      'valid_first_referral',
    ]);
  });

  attendance.forEach((row) => {
    const status = String(row.referral_status || '').trim();
    if (!status || status === 'valid_first_referral' || status === 'no_referral') return;
    referralRows.push([
      row.created_at || '',
      row.session_date || '',
      row.player_name || '',
      row.player_key || '',
      row.referral_code_used || '',
      '',
      status,
    ]);
  });

  const playerRows = Object.values(players)
    .sort((a, b) => b.total_stamp - a.total_stamp || String(a.player_name).localeCompare(String(b.player_name)))
    .map((player) => {
      const totalStamp = Math.max(Number(player.total_stamp || 0), Number(player.total_attendance || 0));
      const totalAttendance = Math.max(Number(player.total_attendance || 0), totalStamp);
      const next = getNextReward_(totalStamp);
      const eligible = getEligibleRewards_(totalStamp).join(', ');
      const venues = Object.keys(player.venues).sort();
      rewardRows.push([
        player.player_key,
        player.player_name,
        totalStamp,
        eligible,
        next.reward,
        next.stamps_remaining,
        next.stamps_remaining === 0 ? 'eligible_all_main_rewards' : 'in_progress',
      ]);
      return [
        player.player_key,
        player.username_reclub,
        player.player_name,
        player.referral_code,
        totalAttendance,
        totalStamp,
        player.last_played,
        venues.join(', '),
        venues.length,
        eligible,
        next.reward,
        next.stamps_remaining,
        player.referral_used_code,
        player.referred_by_player_key,
        player.valid_referral_count,
        player.referral_bonus_attendance,
        new Date(),
      ];
    });

  return { players, playerRows, referralRows, rewardRows };
}

function appendMissingReferralBonuses_(attendanceSheet, players, attendance) {
  const header = getAttendanceHeader_();
  const existingBonus = {};
  attendance.forEach((row) => {
    if (String(row.attendance_type || '').trim() !== 'referral_bonus') return;
    const key = String(row.player_key || '').trim();
    existingBonus[key] = (existingBonus[key] || 0) + 1;
  });

  const rowsToAppend = [];
  Object.values(players).forEach((player) => {
    const bonusTarget = Math.floor(Number(player.valid_referral_count || 0) / 3);
    const already = existingBonus[player.player_key] || 0;
    for (let index = already + 1; index <= bonusTarget; index += 1) {
      const bonusSessionId = `REFERRAL-BONUS-${player.player_key}-${index}`;
      const record = {
        created_at: new Date(),
        attendance_id: makeAttendanceId_(player.player_key, bonusSessionId),
        session_id: bonusSessionId,
        session_code: `REF${index}`,
        session_date: Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd'),
        session_slot: 'Referral bonus',
        venue: 'Referral bonus',
        player_name: player.player_name,
        username_reclub: player.username_reclub,
        player_key: player.player_key,
        referral_code_used: '',
        referral_status: 'bonus_from_3_referrals',
        attendance_type: 'referral_bonus',
        base_price: 0,
        claimed_reward: '',
        discount_percent: 0,
        income_amount: 0,
        notes: `Bonus attendance dari ${index * 3} referral valid`,
      };
      rowsToAppend.push(header.map((key) => record[key] || ''));
    }
  });

  if (rowsToAppend.length) {
    attendanceSheet.getRange(attendanceSheet.getLastRow() + 1, 1, rowsToAppend.length, header.length).setValues(rowsToAppend);
  }
  return rowsToAppend.length;
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
        '',
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
  return ['timestamp', 'date', 'name', 'player_key', 'referral_code', 'referrer_player_key', 'status'];
}

function getRewardHeader_() {
  return ['player_key', 'name', 'total_stamp', 'eligible_rewards', 'next_reward', 'stamps_remaining', 'status'];
}

function getAttendanceHeader_() {
  return [
    'created_at',
    'attendance_id',
    'session_id',
    'session_code',
    'session_date',
    'session_slot',
    'venue',
    'player_name',
    'username_reclub',
    'player_key',
    'referral_code_used',
    'referral_status',
    'attendance_type',
    'base_price',
    'claimed_reward',
    'discount_percent',
    'income_amount',
    'notes',
  ];
}

function getPlayerDbHeader_() {
  return [
    'player_key',
    'username_reclub',
    'player_name',
    'referral_code',
    'total_attendance',
    'total_stamp',
    'last_played',
    'venues',
    'venue_count',
    'eligible_rewards',
    'next_reward',
    'stamps_remaining',
    'referral_used_code',
    'referred_by_player_key',
    'valid_referral_count',
    'referral_bonus_attendance',
    'updated_at',
  ];
}

function getSessionsHeader_() {
  return ['session_id', 'session_code', 'venue', 'session_date', 'session_slot', 'status', 'expense_amount', 'player_price', 'paid_by', 'created_at'];
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

function getFinanceExpenseHeader_() {
  return [
    'created_at',
    'session_id',
    'session_code',
    'session_date',
    'venue',
    'expense_type',
    'amount',
    'paid_by',
    'notes',
  ];
}

function getFinanceIncomeHeader_() {
  return [
    'created_at',
    'attendance_id',
    'session_id',
    'session_code',
    'session_date',
    'venue',
    'username_reclub',
    'player_name',
    'base_price',
    'claimed_reward',
    'discount_percent',
    'income_amount',
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

function ensureSheet_(ss, sheetName, header) {
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    sheet.getRange(1, 1, 1, header.length).setValues([header]);
    sheet.setFrozenRows(1);
    sheet.autoResizeColumns(1, header.length);
    return sheet;
  }

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, header.length).setValues([header]);
    sheet.setFrozenRows(1);
    return sheet;
  }

  const currentHeaders = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0].map((value) => String(value || '').trim());
  const missingHeaders = header.filter((value) => !currentHeaders.includes(value));
  if (missingHeaders.length) {
    sheet.getRange(1, currentHeaders.length + 1, 1, missingHeaders.length).setValues([missingHeaders]);
    sheet.autoResizeColumns(1, currentHeaders.length + missingHeaders.length);
  }
  return sheet;
}

function recordsFromSheet_(sheet) {
  const values = sheet.getDataRange().getValues();
  if (values.length < 2) return [];
  const headers = values[0].map((header) => String(header || '').trim());
  return values.slice(1).map((row) => {
    const record = {};
    headers.forEach((header, index) => {
      record[header] = row[index];
    });
    return record;
  });
}

function appendRecordByHeader_(sheet, record) {
  const headers = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0].map((header) => String(header || '').trim());
  const row = headers.map((header) => Object.prototype.hasOwnProperty.call(record, header) ? record[header] : '');
  sheet.appendRow(row);
  sheet.autoResizeColumns(1, headers.length);
}

function findSessionById_(ss, sessionId) {
  const sheet = ss.getSheetByName(CONFIG.sessionsSheetName);
  if (!sheet || sheet.getLastRow() < 2) return null;
  const records = recordsFromSheet_(sheet);
  return records.find((record) => String(record.session_id || '').trim() === sessionId) || null;
}

function readPlayersByKey_(ss) {
  const sheet = ss.getSheetByName(CONFIG.playersSheetName);
  if (!sheet || sheet.getLastRow() < 2) return {};
  const players = {};
  recordsFromSheet_(sheet).forEach((record) => {
    const key = String(record.player_key || '').trim();
    if (key) players[key] = record;
  });
  return players;
}

function readPlayersByReferralCode_(ss) {
  const players = readPlayersByKey_(ss);
  const byCode = {};
  Object.values(players).forEach((player) => {
    const code = normalizeReferralCode_(player.referral_code);
    if (code) byCode[code] = player;
  });
  return byCode;
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

function normalizeUsername_(username) {
  return String(username || '').trim().replace(/^@+/, '').toLowerCase();
}

function normalizeReferralCode_(code) {
  const cleaned = String(code || '').trim().toUpperCase();
  if (!cleaned || ['-', 'NO', 'NONE', 'N/A', 'NA', 'TIDAK', 'GA', 'GAK'].includes(cleaned)) return '';
  return cleaned;
}

function normalizeClaimedReward_(reward) {
  const cleaned = String(reward || '').trim();
  if (!cleaned || cleaned === 'Tidak claim reward') return '';
  return cleaned;
}

function getRewardDiscountPercent_(reward) {
  const cleaned = normalizeClaimedReward_(reward);
  if (cleaned === '10% diskon session') return 10;
  if (cleaned === '20% diskon session') return 20;
  if (cleaned === '50% diskon session') return 50;
  return 0;
}

function getRewardDiscountAmount_(reward) {
  const cleaned = normalizeClaimedReward_(reward);
  if (cleaned === 'Free coffee') return 20000;
  return 0;
}

function calculateIncomeAmount_(basePrice, reward) {
  const price = Number(basePrice || 0);
  const discount = getRewardDiscountPercent_(reward);
  const fixedDiscount = getRewardDiscountAmount_(reward);
  return Math.max(Math.round(price * (100 - discount) / 100) - fixedDiscount, 0);
}

function makePlayerKeyFromUsername_(username) {
  const normalized = normalizeUsername_(username);
  if (!normalized) return '';
  return `reclub-${normalized.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')}`;
}

function makePlayerKey_(name) {
  return normalizeName_(name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function generateReferralCode_(seed, existingCodes) {
  const cleaned = String(seed || 'SPC').toUpperCase().replace(/[^A-Z0-9]+/g, '');
  const prefix = (cleaned || 'SPC').slice(0, 5).padEnd(3, 'X');
  let counter = 1;
  let code = `${prefix}${counter}`;
  while (existingCodes[code]) {
    counter += 1;
    code = `${prefix}${counter}`;
  }
  existingCodes[code] = true;
  return code;
}

function makeAttendanceId_(playerKey, sessionId) {
  const raw = `${playerKey}::${sessionId}`;
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_1, raw)
    .map((byte) => (`0${(byte + 256).toString(16)}`).slice(-2))
    .join('')
    .slice(0, 12);
  return `ATT-${digest}`;
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
