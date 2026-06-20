import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:fashion_ai/core/database.dart';

/// Offline cache — Drift for structured data, SharedPreferences for auth tokens.
class LocalDb {
  static AppDatabase? _db;

  static AppDatabase get db {
    _db ??= AppDatabase();
    return _db!;
  }

  // ── SharedPreferences (auth tokens, simple flags) ──────────────────────

  static Future<void> cacheJson(String key, Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(key, jsonEncode(data));
  }

  static Future<Map<String, dynamic>?> readJson(String key) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(key);
    if (raw == null) return null;
    return jsonDecode(raw) as Map<String, dynamic>;
  }

  // ── Drift Sync Queue (offline-first actions) ──────────────────────────

  static Future<void> queueAction(Map<String, dynamic> action) async {
    final actionType = action['action'] as String? ?? 'unknown';
    final payload = jsonEncode(action);
    await db.enqueueAction(actionType, payload);
  }

  static Future<List<Map<String, dynamic>>> getPendingActions() async {
    final rows = await db.getPendingActions();
    return rows.map((r) {
      return jsonDecode(r.payloadJson) as Map<String, dynamic>;
    }).toList();
  }

  // ── Drift Outfit Cache ────────────────────────────────────────────────

  static Future<void> cacheOutfit({
    required String brief,
    String? imageBase64,
    String? prompt,
    double clipScore = 0.0,
  }) async {
    await db.cacheOutfit(
      brief: brief,
      imageBase64: imageBase64,
      prompt: prompt,
      clipScore: clipScore,
    );
  }

  // ── Drift Product Cache ───────────────────────────────────────────────

  static Future<void> cacheProduct(Map<String, dynamic> product) async {
    await db.cacheProduct(product);
  }

  static Future<List<CachedProduct>> searchOfflineProducts(String query) async {
    return db.searchCachedProducts(query);
  }
}
