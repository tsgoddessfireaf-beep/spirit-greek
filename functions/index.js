// Firebase entry point: two web addresses, "reading" and "deleteReading".
// All logic lives in lib/service.js; this file only connects it to Google and Claude.
'use strict';

const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');
const logger = require('firebase-functions/logger');

const anthropicKey = defineSecret('ANTHROPIC_API_KEY');
const { loadLibrary, RequestError } = require('./lib/packet');
const { runReading, deleteReading } = require('./lib/service');

// Only these pages may call the server from a browser.
const ORIGINS = [
  'https://tsgoddessfireaf-beep.github.io',
  'https://aeonicarts.com',
  'https://www.aeonicarts.com',
  'http://localhost:8000',
];

const options = { region: 'us-central1', cors: ORIGINS, maxInstances: 5, memory: '256MiB' };

let library = null;
let firestore = null;
const getLibrary = () => library || (library = loadLibrary());
function db() {
  if (!firestore) {
    const admin = require('firebase-admin');
    if (!admin.apps.length) admin.initializeApp();
    firestore = admin.firestore();
  }
  return firestore;
}
const store = {
  save: (id, data) => db().collection('readings').doc(id).set(data),
  get: async (id) => {
    const snap = await db().collection('readings').doc(id).get();
    return snap.exists ? snap.data() : null;
  },
  remove: (id) => db().collection('readings').doc(id).delete(),
};

function fail(res, err) {
  if (err instanceof RequestError) return res.status(400).json({ error: err.message });
  logger.error('reading failed', { message: err.message }); // never the question
  return res.status(500).json({ error: 'The reading service had a problem. Please try again.' });
}

exports.reading = onRequest({ ...options, secrets: [anthropicKey], timeoutSeconds: 90 }, async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Use POST' });
  try {
    const Anthropic = require('@anthropic-ai/sdk');
    const client = new Anthropic({ apiKey: anthropicKey.value() });
    const result = await runReading({ body: req.body, lib: getLibrary(), client, store, log: (e) => logger.info('reading', e) });
    return res.json(result);
  } catch (err) {
    return fail(res, err);
  }
});

exports.deleteReading = onRequest({ ...options, timeoutSeconds: 30 }, async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Use POST' });
  try {
    return res.json(await deleteReading({ body: req.body, store }));
  } catch (err) {
    return fail(res, err);
  }
});
