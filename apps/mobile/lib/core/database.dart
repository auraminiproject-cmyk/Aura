import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

part 'database.g.dart';

/// Cached outfit designs for offline viewing
class CachedOutfits extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get brief => text()();
  TextColumn get imageBase64 => text().nullable()();
  TextColumn get prompt => text().nullable()();
  RealColumn get clipScore => real().withDefault(const Constant(0.0))();
  DateTimeColumn get cachedAt => dateTime().withDefault(currentDateAndTime)();
}

/// Cached product results for offline browsing
class CachedProducts extends Table {
  TextColumn get productId => text()();
  TextColumn get name => text()();
  RealColumn get priceInr => real().withDefault(const Constant(0))();
  TextColumn get platform => text().nullable()();
  TextColumn get category => text().nullable()();
  TextColumn get color => text().nullable()();
  TextColumn get affiliateUrl => text().nullable()();
  TextColumn get imageUrl => text().nullable()();
  DateTimeColumn get cachedAt => dateTime().withDefault(currentDateAndTime)();

  @override
  Set<Column> get primaryKey => {productId};
}

/// Offline sync queue — stores actions to replay when back online
class SyncQueue extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get action => text()(); // e.g. 'add_wardrobe', 'send_chat'
  TextColumn get payloadJson => text()();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
  BoolColumn get synced => boolean().withDefault(const Constant(false))();
}

/// User preferences cached locally
class UserPrefs extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}

@DriftDatabase(tables: [CachedOutfits, CachedProducts, SyncQueue, UserPrefs])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  // ── Outfit Cache ──────────────────────────────────────────────────────

  Future<void> cacheOutfit({
    required String brief,
    String? imageBase64,
    String? prompt,
    double clipScore = 0.0,
  }) async {
    await into(cachedOutfits).insert(CachedOutfitsCompanion.insert(
      brief: brief,
      imageBase64: Value(imageBase64),
      prompt: Value(prompt),
      clipScore: Value(clipScore),
    ));
  }

  Future<List<CachedOutfit>> getRecentOutfits({int limit = 20}) {
    return (select(cachedOutfits)
          ..orderBy([(t) => OrderingTerm.desc(t.cachedAt)])
          ..limit(limit))
        .get();
  }

  // ── Product Cache ─────────────────────────────────────────────────────

  Future<void> cacheProduct(Map<String, dynamic> product) async {
    await into(cachedProducts).insertOnConflictUpdate(
      CachedProductsCompanion.insert(
        productId: product['id']?.toString() ?? '',
        name: product['name']?.toString() ?? '',
        priceInr: Value((product['price_inr'] as num?)?.toDouble() ?? 0),
        platform: Value(product['platform']?.toString()),
        category: Value(product['category']?.toString()),
        color: Value(product['color']?.toString()),
        affiliateUrl: Value(product['affiliate_url']?.toString()),
        imageUrl: Value(product['image_url']?.toString()),
      ),
    );
  }

  Future<List<CachedProduct>> searchCachedProducts(String query) {
    final lower = query.toLowerCase();
    return (select(cachedProducts)
          ..where((t) =>
              t.name.lower().contains(lower) |
              t.category.lower().contains(lower)))
        .get();
  }

  // ── Sync Queue ────────────────────────────────────────────────────────

  Future<void> enqueueAction(String action, String payloadJson) async {
    await into(syncQueue).insert(SyncQueueCompanion.insert(
      action: action,
      payloadJson: payloadJson,
    ));
  }

  Future<List<SyncQueueData>> getPendingActions() {
    return (select(syncQueue)..where((t) => t.synced.equals(false))).get();
  }

  Future<void> markSynced(int id) async {
    await (update(syncQueue)..where((t) => t.id.equals(id)))
        .write(const SyncQueueCompanion(synced: Value(true)));
  }

  // ── User Prefs ────────────────────────────────────────────────────────

  Future<void> setPref(String key, String value) async {
    await into(userPrefs).insertOnConflictUpdate(
      UserPrefsCompanion.insert(key: key, value: value),
    );
  }

  Future<String?> getPref(String key) async {
    final row = await (select(userPrefs)..where((t) => t.key.equals(key)))
        .getSingleOrNull();
    return row?.value;
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'fashion_ai.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
