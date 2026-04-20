const CONFIG = {
  rawSheetName: 'Form_Responses',
  playersSheetName: 'players_db',
  referralSheetName: 'referral_log',
  rewardSheetName: 'reward_status',
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
