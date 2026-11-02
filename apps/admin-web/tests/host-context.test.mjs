import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mergeHostContext, parseHostContext, safeReturnUrl } from '../app/lib/host-context.ts';

const ORIGINS = ['http://localhost:3003', 'http://localhost:5173'];
const IDPS = ['buildingflow', 'traceflow'];

test('accepts return urls only from allowed origins', () => {
  assert.equal(safeReturnUrl('http://localhost:3003/settings', ORIGINS), 'http://localhost:3003/settings');
  assert.equal(safeReturnUrl('https://evil.example/phish', ORIGINS), null);
  assert.equal(safeReturnUrl('javascript:alert(1)', ORIGINS), null);
  assert.equal(safeReturnUrl('//evil.example', ORIGINS), null);
});

test('parses host context and ignores unknown values', () => {
  const ctx = parseHostContext('?idp=buildingflow&return=http://localhost:3003/&locale=en&theme=dark&host=BuildingFlow', ORIGINS, IDPS);
  assert.deepEqual(ctx, { idp: 'buildingflow', returnUrl: 'http://localhost:3003/', hostName: 'BuildingFlow', locale: 'en', theme: 'dark' });
  const bad = parseHostContext('?idp=other&locale=de&theme=neon&host=<script>', ORIGINS, IDPS);
  assert.deepEqual(bad, { idp: null, returnUrl: null, hostName: null, locale: null, theme: null });
});

test('keeps earlier context when navigating inside the hub', () => {
  const first = parseHostContext('?idp=traceflow&return=http://localhost:5173/', ORIGINS, IDPS);
  const merged = mergeHostContext(first, parseHostContext('', ORIGINS, IDPS));
  assert.equal(merged.idp, 'traceflow');
  assert.equal(merged.returnUrl, 'http://localhost:5173/');
});
